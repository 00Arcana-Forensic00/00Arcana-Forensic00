// Prints {public_key, key}: a key signed by the worker code, for the Python interop test.
import { generateKeyPairSync } from "node:crypto";
import { signLicense, buildPayload } from "../src/index.js";

const { privateKey, publicKey } = generateKeyPairSync("ed25519");
const pkcs8 = privateKey.export({ type: "pkcs8", format: "der" }).toString("base64");
const raw = publicKey.export({ type: "spki", format: "der" }).subarray(-32).toString("base64");
const payload = buildPayload({ id: "cs_test_interop000001", mode: "payment",
  customer_details: { email: "ann@example.com", name: "Ann Exäminer" } }, { plan: "pro", seats: 1 });
console.log(JSON.stringify({ public_key: raw, key: await signLicense(payload, pkcs8) }));
