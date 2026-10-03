// Arcalume license worker (Cloudflare Workers).
//
// POST /stripe/webhook   Stripe calls this after checkout. The signature is verified,
//                        then a license key is signed with Ed25519 and stored in KV.
// GET  /license?session_id=cs_...
//                        The checkout success page fetches the buyer's key with the
//                        Checkout Session id Stripe put in its URL.
//
// The app verifies keys offline with the public key; this worker never sees a customer
// document and the app never calls it.
//
// Bindings (wrangler.toml / secrets):
//   LICENSES               KV namespace
//   STRIPE_WEBHOOK_SECRET  secret, whsec_...
//   LICENSE_SIGNING_KEY    secret, base64 PKCS#8 Ed25519 key (packaging/license_tool.py keygen)
//   PAYMENT_LINK_PLANS     var, JSON: {"plink_...": {"plan": "pro", "seats": 1, "months": null}}
//   SITE_ORIGIN            var, e.g. https://arcana-forensics.com (CORS for the lookup)

export const PRODUCT = "arcalume";
const TOLERANCE_S = 300;
const SESSION_RE = /^cs_(test|live)_[A-Za-z0-9]{10,200}$/;
const enc = new TextEncoder();

const b64url = (bytes) => btoa(String.fromCharCode(...new Uint8Array(bytes))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const b64decode = (s) => Uint8Array.from(atob(s.trim()), (c) => c.charCodeAt(0));
const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");

// Same bytes Python's json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True) makes.
export function canonical(value) {
  const walk = (v) => {
    if (Array.isArray(v)) return "[" + v.map(walk).join(",") + "]";
    if (v && typeof v === "object") return "{" + Object.keys(v).sort().map((k) => JSON.stringify(k) + ":" + walk(v[k])).join(",") + "}";
    return JSON.stringify(v === undefined ? null : v);
  };
  return walk(value).replace(/[\u007f-￿]/g, (c) => (c === "\u007f" ? c : "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0")));
}

function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

export async function verifyStripeSignature(rawBody, header, secret, nowS = Math.floor(Date.now() / 1000)) {
  if (!header || !secret) return false;
  let t = null;
  const sigs = [];
  for (const item of header.split(",")) {
    const [k, v] = item.split("=", 2);
    if (k === "t") t = v;
    else if (k === "v1" && v) sigs.push(v);
  }
  if (!t || !/^\d+$/.test(t) || !sigs.length) return false;
  if (Math.abs(nowS - Number(t)) > TOLERANCE_S) return false;
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const expected = hex(await crypto.subtle.sign("HMAC", key, enc.encode(`${t}.${rawBody}`)));
  return sigs.some((s) => timingSafeEqual(s, expected));
}

export async function signLicense(payload, pkcs8b64) {
  const key = await crypto.subtle.importKey("pkcs8", b64decode(pkcs8b64), { name: "Ed25519" }, false, ["sign"]);
  const body = enc.encode(canonical(payload));
  const sig = await crypto.subtle.sign({ name: "Ed25519" }, key, body);
  return `ARC1.${b64url(body)}.${b64url(sig)}`;
}

function addMonths(date, months) {
  const d = new Date(date.getTime());
  d.setUTCMonth(d.getUTCMonth() + months);
  return d;
}

export function planFor(session, env) {
  let plans = {};
  try { plans = JSON.parse(env.PAYMENT_LINK_PLANS || "{}"); } catch (_) { plans = {}; }
  const fromLink = session.payment_link && plans[session.payment_link];
  if (fromLink) return fromLink;
  const md = session.metadata || {};
  if (md.arcalume_plan) return { plan: md.arcalume_plan, seats: Number(md.arcalume_seats || 1), months: md.arcalume_months ? Number(md.arcalume_months) : null };
  return null;
}

export function buildPayload(session, plan, now = new Date()) {
  const cd = session.customer_details || {};
  const months = plan.months || (session.mode === "subscription" ? 12 : null);
  // Subscriptions get the paid period plus 14 days of grace; one-time purchases never expire.
  const expires = months ? new Date(addMonths(now, months).getTime() + 14 * 864e5).toISOString().slice(0, 10) : null;
  return {
    v: 1,
    product: PRODUCT,
    id: "lic_" + hex(crypto.getRandomValues(new Uint8Array(8))),
    plan: plan.plan || "pro",
    email: cd.email || session.customer_email || "",
    name: cd.name || "",
    seats: Number(plan.seats || 1) * Number(session.quantity || 1),
    issued: now.toISOString().slice(0, 10),
    expires,
    order: session.id,
  };
}

function json(body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...extra } });
}

async function handleWebhook(request, env) {
  const raw = await request.text();
  if (raw.length > 1_000_000) return json({ error: "too large" }, 413);
  if (!(await verifyStripeSignature(raw, request.headers.get("Stripe-Signature"), env.STRIPE_WEBHOOK_SECRET))) {
    return json({ error: "bad signature" }, 400);
  }
  const event = JSON.parse(raw);
  if (event.type !== "checkout.session.completed" && event.type !== "checkout.session.async_payment_succeeded") {
    return json({ received: true, ignored: event.type });
  }
  const session = event.data && event.data.object;
  if (!session || !SESSION_RE.test(session.id || "")) return json({ error: "no session" }, 400);
  if (!["paid", "no_payment_required"].includes(session.payment_status)) return json({ received: true, pending: true });
  const plan = planFor(session, env);
  if (!plan) return json({ received: true, ignored: "not an Arcalume purchase" });
  const existing = await env.LICENSES.get("session:" + session.id);
  if (existing) return json({ received: true, duplicate: true });  // Stripe retries; issue once
  const payload = buildPayload(session, plan);
  const key = await signLicense(payload, env.LICENSE_SIGNING_KEY);
  await env.LICENSES.put("lic:" + payload.id, JSON.stringify({ ...payload, created: new Date().toISOString() }));
  await env.LICENSES.put("session:" + session.id, key, { expirationTtl: 60 * 60 * 24 * 90 });
  return json({ received: true, license: payload.id });
}

async function handleLookup(url, env) {
  const cors = { "Access-Control-Allow-Origin": env.SITE_ORIGIN || "https://arcana-forensics.com", Vary: "Origin" };
  const id = url.searchParams.get("session_id") || "";
  if (!SESSION_RE.test(id)) return json({ error: "bad session id" }, 400, cors);
  const key = await env.LICENSES.get("session:" + id);
  // 404 until the webhook lands; the success page retries for a short while.
  if (!key) return json({ error: "not ready" }, 404, cors);
  return json({ key }, 200, cors);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    try {
      if (request.method === "POST" && url.pathname === "/stripe/webhook") return await handleWebhook(request, env);
      if (request.method === "GET" && url.pathname === "/license") return await handleLookup(url, env);
    } catch (e) {
      return json({ error: "internal error" }, 500);
    }
    return json({ error: "not found" }, 404);
  },
};
