# Arcana Forensics — Base44 Dev Environment

## What this is
A static marketing website for "Arcana Forensics" — an air-gapped digital forensics tool.
The repo root contains `index.html` (the landing page) and a `site/` directory with
sub-pages (pricing, try/field-test, checkout success/cancel). The repo also contains
Rust crates, Python tools, and other non-web components, but the web entry point is
purely static HTML/CSS/JS — no build step, no backend.

## How it runs
- `docker-compose.base44.yml` serves the static files via `nginx:alpine` on port 3000.
- The repo root is bind-mounted read-only at `/usr/share/nginx/html`.
- nginx runs as `user root` (via `nginx.base44.conf`) because the sandbox repo directory
  has restrictive (0700) permissions that the default nginx worker user cannot traverse.
- No external credentials or secrets are needed. Stripe integration uses external
  Payment Link URLs (buy.stripe.com), not server-side API calls.

## Verification
- `curl http://localhost:3000/` → 200 (landing page)
- `curl http://localhost:3000/site/pricing.html` → 200
- `curl http://localhost:3000/site/try.html` → 200
- Healthcheck: `wget --spider http://localhost:80/index.html`
