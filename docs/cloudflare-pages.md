# Cloudflare Pages deployment

This repository now includes a static Cloudflare Pages site in `site/`.

## One-time Cloudflare setup

1. Create a Pages project named `arcana-forensics` and connect this repository, or deploy with Wrangler.
2. Use `site` as the output directory. No build command is required.
3. Add `www.arcana-forensics.com` under **Workers & Pages → Custom domains**. Cloudflare will provide the DNS record and certificate.
4. Add a Cloudflare Redirect Rule from `arcana-forensics.com/*` to `https://www.arcana-forensics.com/$1` with status 301 if the apex domain should also resolve.
5. Keep SSL/TLS mode **Full (strict)** and enable **Always Use HTTPS**. Do not proxy forensic data or expose the local Rust CLI through a public endpoint.

## Local preview

```bash
npx wrangler pages dev site
# or serve the static directory with any local HTTP server
```

The `_headers` file applies browser security headers on Cloudflare Pages. `wrangler.toml` intentionally contains no account ID or credentials; authenticate Wrangler through `wrangler login` or a secret-managed `CLOUDFLARE_API_TOKEN`.
