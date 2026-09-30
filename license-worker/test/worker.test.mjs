import { test } from "node:test";
import assert from "node:assert/strict";
import { createHmac, generateKeyPairSync, verify as edVerify, createPublicKey } from "node:crypto";
import worker, { canonical, verifyStripeSignature } from "../src/index.js";

function keys() {
  const { privateKey, publicKey } = generateKeyPairSync("ed25519");
  const pkcs8 = privateKey.export({ type: "pkcs8", format: "der" }).toString("base64");
  const raw = publicKey.export({ type: "spki", format: "der" }).subarray(-32).toString("base64");
  return { pkcs8, raw, publicKey };
}

function kv() {
  const m = new Map();
  return { m, get: async (k) => m.get(k) ?? null, put: async (k, v) => { m.set(k, v); } };
}

const SECRET = "whsec_test_secret";
const sign = (body, t = Math.floor(Date.now() / 1000), secret = SECRET) =>
  `t=${t},v1=${createHmac("sha256", secret).update(`${t}.${body}`).digest("hex")}`;

function session(over = {}) {
  return { id: "cs_test_a1B2c3D4e5F6g7H8", mode: "payment", payment_status: "paid", payment_link: "plink_pro",
           customer_details: { email: "ann@example.com", name: "Ann Exäminer" }, ...over };
}

function env(k) {
  return { LICENSES: kv(), STRIPE_WEBHOOK_SECRET: SECRET, LICENSE_SIGNING_KEY: k.pkcs8,
           PAYMENT_LINK_PLANS: JSON.stringify({ plink_pro: { plan: "pro", seats: 1, months: null } }) };
}

const post = (body, sig) => new Request("https://w/stripe/webhook", { method: "POST", body, headers: { "Stripe-Signature": sig } });
const event = (obj, type = "checkout.session.completed") => JSON.stringify({ type, data: { object: obj } });

test("canonical JSON matches Python's sorted, ASCII-only form", () => {
  assert.equal(canonical({ b: 1, a: [true, null, "é"], c: { z: "x", y: 2 } }), '{"a":[true,null,"\\u00e9"],"b":1,"c":{"y":2,"z":"x"}}');
});

test("stripe signature: valid, wrong secret, stale, malformed", async () => {
  const body = "{}";
  assert.equal(await verifyStripeSignature(body, sign(body), SECRET), true);
  assert.equal(await verifyStripeSignature(body, sign(body, undefined, "whsec_other"), SECRET), false);
  assert.equal(await verifyStripeSignature(body, sign(body, 1000), SECRET), false);
  assert.equal(await verifyStripeSignature(body, "garbage", SECRET), false);
  assert.equal(await verifyStripeSignature(body + " ", sign(body), SECRET), false);
});

test("paid checkout issues one verifiable key, retrievable by session id", async () => {
  const k = keys();
  const e = env(k);
  const body = event(session());
  let r = await worker.fetch(post(body, sign(body)), e);
  assert.equal(r.status, 200);
  const first = await r.json();
  assert.ok(first.license.startsWith("lic_"));
  r = await worker.fetch(post(body, sign(body)), e);          // Stripe retry
  assert.equal((await r.json()).duplicate, true);
  r = await worker.fetch(new Request("https://w/license?session_id=cs_test_a1B2c3D4e5F6g7H8"), e);
  assert.equal(r.status, 200);
  const { key } = await r.json();
  const [prefix, p, s] = key.split(".");
  assert.equal(prefix, "ARC1");
  const payloadBytes = Buffer.from(p, "base64url");
  const payload = JSON.parse(payloadBytes);
  assert.equal(payload.product, "arcalume");
  assert.equal(payload.email, "ann@example.com");
  assert.equal(payload.expires, null);
  assert.ok(edVerify(null, payloadBytes, k.publicKey, Buffer.from(s, "base64url")));
});

test("bad signature, unpaid, unknown product and junk lookups are refused", async () => {
  const k = keys();
  const e = env(k);
  const body = event(session());
  assert.equal((await worker.fetch(post(body, sign(body, undefined, "whsec_x")), e)).status, 400);
  const unpaid = event(session({ payment_status: "unpaid" }));
  assert.equal((await (await worker.fetch(post(unpaid, sign(unpaid)), e)).json()).pending, true);
  const other = event(session({ payment_link: "plink_other" }));
  assert.match((await (await worker.fetch(post(other, sign(other)), e)).json()).ignored, /not an Arcalume/);
  assert.equal(e.LICENSES.m.size, 0);
  assert.equal((await worker.fetch(new Request("https://w/license?session_id=../../x"), e)).status, 400);
  assert.equal((await worker.fetch(new Request("https://w/license?session_id=cs_test_nothinghere1"), e)).status, 404);
  assert.equal((await worker.fetch(new Request("https://w/other"), e)).status, 404);
});

test("subscriptions expire after the period plus grace", async () => {
  const k = keys();
  const e = env(k);
  const body = event(session({ mode: "subscription", payment_link: "plink_pro" }));
  await worker.fetch(post(body, sign(body)), e);
  const key = [...e.LICENSES.m.entries()].find(([n]) => n.startsWith("session:"))[1];
  const payload = JSON.parse(Buffer.from(key.split(".")[1], "base64url"));
  const days = (new Date(payload.expires) - new Date(payload.issued)) / 864e5;
  assert.ok(days >= 365 + 13 && days <= 366 + 15, `days=${days}`);
});
