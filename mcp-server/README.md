# Arcana Forensics MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io/) server deployed on **Cloudflare Workers** that exposes 17 tools for forensics, CI/build, and repo management.

## Tools

### Forensics API (4)
| Tool | Description |
|------|-------------|
| `vault_inspect` | Inspect vault header metadata (encryption, KDF, version) |
| `ledger_verify` | Verify custody hash-chain integrity |
| `list_vaults` | List `.arcr` vault files in the repo |
| `supported_formats` | List supported image/video formats |

### CI / Build (5)
| Tool | Description |
|------|-------------|
| `trigger_workflow` | Trigger a GitHub Actions workflow |
| `workflow_runs` | List recent workflow runs |
| `run_status` | Get detailed run + job + step status |
| `list_releases` | List published releases |
| `rerun_failed_jobs` | Re-run only failed jobs in a run |

### Repo Management (8)
| Tool | Description |
|------|-------------|
| `list_pull_requests` | List PRs with status and labels |
| `get_pull_request` | Full PR details (diff, reviews, checks) |
| `create_pull_request` | Create a new PR |
| `merge_pull_request` | Merge a PR (squash/merge/rebase) |
| `list_issues` | List issues with filters |
| `create_issue` | Create a new issue |
| `repo_info` | Repo metadata and language breakdown |
| `list_branches` | List branches with protection status |

## Setup

### 1. Deploy to Cloudflare Workers

```bash
cd mcp-server
npm install

# Create the KV namespace
npx wrangler kv namespace create MCP_STATE
# Copy the printed id into wrangler.toml

# Set secrets
npx wrangler secret put GITHUB_TOKEN        # GitHub PAT with repo scope
npx wrangler secret put MCP_SHARED_SECRET    # shared secret for MCP clients

# Deploy
npx wrangler deploy
```

### 2. Connect to Claude Desktop

Add this to your Claude Desktop config (`~/.claude/claude_desktop_config.json` on macOS/Linux, or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "arcana-forensics": {
      "transport": "http",
      "url": "https://arcana-forensics-mcp.<your-subdomain>.workers.dev",
      "headers": {
        "Authorization": "Bearer <your-MCP_SHARED_SECRET>"
      }
    }
  }
}
```

### 3. Connect to GitHub (optional webhook)

To receive push/PR/release events, add a GitHub webhook:

1. Go to **Settings → Webhooks** in the repo
2. Payload URL: `https://arcana-forensics-mcp.<subdomain>.workers.dev/webhook`
3. Content type: `application/json`
4. Select events: Pushes, Pull requests, Workflow runs

## Development

```bash
npm run dev    # Start local dev server (wrangler dev)
npm test       # Run tests
npm run deploy # Deploy to Cloudflare
```

## Authentication

All MCP requests require a `Bearer` token matching the `MCP_SHARED_SECRET` secret.
When `MCP_SHARED_SECRET` is not set, authentication is disabled (dev mode only).

## Architecture

- **Runtime:** Cloudflare Workers (V8 isolate, `nodejs_compat`)
- **Protocol:** JSON-RPC 2.0 over HTTP (MCP spec `2024-11-05`)
- **GitHub API:** REST v3 with PAT authentication
- **Forensics:** Vault headers parsed directly from GitHub file contents API
- **Ledger verification:** SHA-256 hash chain verified using Web Crypto API
