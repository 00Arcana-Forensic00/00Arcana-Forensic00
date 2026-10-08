/**
 * Arcana Forensics MCP Server — Cloudflare Worker
 *
 * Exposes three tool groups over the Model Context Protocol:
 *   1. Forensics API  — vault inspect, ledger verify, list vaults
 *   2. CI / Build     — trigger workflows, check run status, list releases
 *   3. Repo Mgmt      — list/create PRs, list/create issues, repo info
 *
 * Authentication: Bearer token (MCP_SHARED_SECRET) on every request.
 * GitHub access:  GITHUB_TOKEN secret with `repo` scope.
 */

// ─── GitHub helpers ─────────────────────────────────────────────────

async function gh(env, path, opts = {}) {
  const base = "https://api.github.com";
  const url = path.startsWith("http") ? path : `${base}${path}`;
  const res = await fetch(url, {
    ...opts,
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "arcana-forensics-mcp/1.0",
      ...(opts.headers || {}),
      ...(opts.body ? { "Content-Type": "application/json" } : {}),
    },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GitHub ${res.status}: ${text.slice(0, 300)}`);
  }
  return res.json();
}

const repo = (env) => `/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}`;

// ─── Tool definitions ───────────────────────────────────────────────

const TOOLS = [
  // ── Forensics API ──
  {
    name: "vault_inspect",
    description:
      "Inspect a vault file's header metadata (encryption params, KDF, version) without needing the passphrase. Provide the vault file path relative to the repo root.",
    inputSchema: {
      type: "object",
      properties: {
        vault_path: {
          type: "string",
          description: "Path to the .arcr vault file relative to repo root",
        },
        ref: {
          type: "string",
          description: "Git ref (branch/tag/sha) to read from. Default: main",
          default: "main",
        },
      },
      required: ["vault_path"],
    },
  },
  {
    name: "ledger_verify",
    description:
      "Verify the integrity of a vault directory's custody hash chain (ledger). Returns whether the chain is intact, the number of entries, and the current head hash.",
    inputSchema: {
      type: "object",
      properties: {
        vault_dir: {
          type: "string",
          description: "Path to the vault directory containing ledger.jsonl",
        },
        ref: { type: "string", default: "main" },
        expect_head: {
          type: "string",
          description:
            "Optional: expected head hash to verify against (detects removed entries)",
        },
      },
      required: ["vault_dir"],
    },
  },
  {
    name: "list_vaults",
    description:
      "List all .arcr vault files found in the repo (or a subdirectory). Returns file paths and sizes.",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description:
            "Directory to search in (default: repo root). Example: 'evidence/case-42'",
          default: "",
        },
        ref: { type: "string", default: "main" },
      },
    },
  },
  {
    name: "supported_formats",
    description:
      "List all file formats Arcana Restore supports for sealing (images and video).",
    inputSchema: { type: "object", properties: {} },
  },

  // ── CI / Build ──
  {
    name: "trigger_workflow",
    description:
      "Trigger a GitHub Actions workflow by filename. Use 'restore-release.yml' for the release build, 'ci.yml' for the main CI, etc.",
    inputSchema: {
      type: "object",
      properties: {
        workflow: {
          type: "string",
          description:
            "Workflow filename (e.g. 'ci.yml', 'restore-release.yml', 'field-test.yml')",
        },
        ref: {
          type: "string",
          description: "Branch or tag to run on. Default: main",
          default: "main",
        },
        inputs: {
          type: "object",
          description: "Optional workflow_dispatch inputs",
          additionalProperties: { type: "string" },
        },
      },
      required: ["workflow"],
    },
  },
  {
    name: "workflow_runs",
    description:
      "List recent workflow runs, optionally filtered by workflow file or branch. Shows status, conclusion, and timing.",
    inputSchema: {
      type: "object",
      properties: {
        workflow: {
          type: "string",
          description: "Filter by workflow filename (e.g. 'ci.yml')",
        },
        branch: { type: "string", description: "Filter by branch name" },
        status: {
          type: "string",
          enum: ["queued", "in_progress", "completed"],
          description: "Filter by run status",
        },
        limit: {
          type: "number",
          description: "Max runs to return (default 10)",
          default: 10,
        },
      },
    },
  },
  {
    name: "run_status",
    description:
      "Get detailed status of a specific workflow run including individual job statuses and step outcomes.",
    inputSchema: {
      type: "object",
      properties: {
        run_id: {
          type: "number",
          description: "The workflow run ID",
        },
      },
      required: ["run_id"],
    },
  },
  {
    name: "list_releases",
    description:
      "List published releases with tag, name, date, and asset download URLs.",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "number", default: 10 },
        include_drafts: { type: "boolean", default: false },
      },
    },
  },
  {
    name: "rerun_failed_jobs",
    description:
      "Re-run only the failed jobs in a workflow run (not the entire run).",
    inputSchema: {
      type: "object",
      properties: {
        run_id: { type: "number", description: "The workflow run ID" },
      },
      required: ["run_id"],
    },
  },

  // ── Repo Management ──
  {
    name: "list_pull_requests",
    description:
      "List open (or closed/all) pull requests with title, author, labels, CI status, and review state.",
    inputSchema: {
      type: "object",
      properties: {
        state: {
          type: "string",
          enum: ["open", "closed", "all"],
          default: "open",
        },
        limit: { type: "number", default: 10 },
      },
    },
  },
  {
    name: "get_pull_request",
    description:
      "Get full details of a pull request: diff stats, reviews, check status, merge state.",
    inputSchema: {
      type: "object",
      properties: {
        number: { type: "number", description: "PR number" },
      },
      required: ["number"],
    },
  },
  {
    name: "create_pull_request",
    description: "Create a new pull request.",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string" },
        body: { type: "string" },
        head: { type: "string", description: "Source branch" },
        base: { type: "string", default: "main" },
        draft: { type: "boolean", default: false },
      },
      required: ["title", "head"],
    },
  },
  {
    name: "merge_pull_request",
    description: "Merge a pull request (squash, merge, or rebase).",
    inputSchema: {
      type: "object",
      properties: {
        number: { type: "number" },
        method: {
          type: "string",
          enum: ["merge", "squash", "rebase"],
          default: "squash",
        },
        commit_title: { type: "string" },
      },
      required: ["number"],
    },
  },
  {
    name: "list_issues",
    description: "List open issues with labels, assignees, and milestone.",
    inputSchema: {
      type: "object",
      properties: {
        state: {
          type: "string",
          enum: ["open", "closed", "all"],
          default: "open",
        },
        labels: {
          type: "string",
          description: "Comma-separated label names to filter by",
        },
        limit: { type: "number", default: 10 },
      },
    },
  },
  {
    name: "create_issue",
    description: "Create a new issue in the repo.",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string" },
        body: { type: "string" },
        labels: {
          type: "array",
          items: { type: "string" },
          description: "Labels to apply",
        },
        assignees: {
          type: "array",
          items: { type: "string" },
          description: "GitHub usernames to assign",
        },
      },
      required: ["title"],
    },
  },
  {
    name: "repo_info",
    description:
      "Get repository metadata: description, stars, forks, default branch, language breakdown, and recent activity.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "list_branches",
    description: "List branches with their latest commit and protection status.",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "number", default: 30 },
      },
    },
  },
];

// ─── Tool handlers ──────────────────────────────────────────────────

async function handleTool(name, args, env) {
  const r = repo(env);

  switch (name) {
    // ── Forensics ──

    case "vault_inspect": {
      const ref = args.ref || "main";
      // Fetch raw file content from GitHub
      const data = await gh(env, `${r}/contents/${args.vault_path}?ref=${ref}`);
      if (data.encoding !== "base64") {
        return { error: "File too large for API content fetch; use git clone." };
      }
      // Parse the vault header from the first bytes
      const buf = Uint8Array.from(atob(data.content.replace(/\n/g, "")), (c) =>
        c.charCodeAt(0)
      );
      // The vault format: 8-byte magic + 4-byte header-len + JSON header
      const magic = new TextDecoder().decode(buf.slice(0, 8));
      if (magic !== "ARCANA\x00\x01") {
        return { error: "Not a valid Arcana vault file (bad magic bytes)" };
      }
      const hdrLen = new DataView(buf.buffer).getUint32(8, true);
      const header = JSON.parse(new TextDecoder().decode(buf.slice(12, 12 + hdrLen)));
      // Redact the salt for safety
      if (header.kdf?.salt) delete header.kdf.salt;
      return {
        file: args.vault_path,
        ref,
        header,
        size_bytes: data.size,
      };
    }

    case "ledger_verify": {
      const ref = args.ref || "main";
      const ledgerPath = `${args.vault_dir.replace(/\/$/, "")}/ledger.jsonl`;
      const data = await gh(env, `${r}/contents/${ledgerPath}?ref=${ref}`);
      const content = atob(data.content.replace(/\n/g, ""));
      const lines = content.trim().split("\n").filter(Boolean);
      const entries = lines.map((l) => JSON.parse(l));

      // Verify chain integrity
      let prevHash = null;
      let ok = true;
      let failMsg = "";
      for (let i = 0; i < entries.length; i++) {
        if (entries[i].prev !== prevHash) {
          ok = false;
          failMsg = `chain break at entry ${i}: expected prev=${prevHash}, got ${entries[i].prev}`;
          break;
        }
        // Recompute hash of this entry
        const payload = JSON.stringify({
          prev: entries[i].prev,
          sha256: entries[i].sha256,
          source: entries[i].source,
          ts: entries[i].ts,
        });
        const hashBuf = await crypto.subtle.digest(
          "SHA-256",
          new TextEncoder().encode(payload)
        );
        prevHash = [...new Uint8Array(hashBuf)]
          .map((b) => b.toString(16).padStart(2, "0"))
          .join("");
      }
      const head = prevHash;
      if (ok && args.expect_head && head !== args.expect_head) {
        ok = false;
        failMsg = `head mismatch: got ${head}, expected ${args.expect_head}`;
      }

      return {
        verified: ok,
        entries: entries.length,
        head,
        message: ok ? "chain intact" : failMsg,
      };
    }

    case "list_vaults": {
      const ref = args.ref || "main";
      const path = args.path || "";
      // Use the Git tree API to search recursively
      const tree = await gh(env, `${r}/git/trees/${ref}?recursive=1`);
      const vaults = tree.tree
        .filter(
          (f) =>
            f.type === "blob" &&
            f.path.endsWith(".arcr") &&
            (!path || f.path.startsWith(path))
        )
        .map((f) => ({ path: f.path, size_bytes: f.size }));
      return { count: vaults.length, vaults };
    }

    case "supported_formats":
      return {
        images: ["PNG", "JPEG", "TIFF", "BMP"],
        video: ["MP4", "MOV", "AVI", "WebM", "MKV"],
        note: "Video files are composited into a single restored image. Images can be repaired (glare removal, illumination flattening, shadow fill).",
      };

    // ── CI / Build ──

    case "trigger_workflow": {
      const ref = args.ref || "main";
      await gh(env, `${r}/actions/workflows/${args.workflow}/dispatches`, {
        method: "POST",
        body: { ref, inputs: args.inputs || {} },
      });
      return { triggered: true, workflow: args.workflow, ref };
    }

    case "workflow_runs": {
      let path = `${r}/actions/runs?per_page=${args.limit || 10}`;
      if (args.workflow)
        path = `${r}/actions/workflows/${args.workflow}/runs?per_page=${args.limit || 10}`;
      if (args.branch) path += `&branch=${encodeURIComponent(args.branch)}`;
      if (args.status) path += `&status=${args.status}`;
      const data = await gh(env, path);
      return {
        total: data.total_count,
        runs: data.workflow_runs.map((run) => ({
          id: run.id,
          name: run.name,
          status: run.status,
          conclusion: run.conclusion,
          branch: run.head_branch,
          sha: run.head_sha?.slice(0, 7),
          started: run.run_started_at,
          updated: run.updated_at,
          url: run.html_url,
        })),
      };
    }

    case "run_status": {
      const [run, jobs] = await Promise.all([
        gh(env, `${r}/actions/runs/${args.run_id}`),
        gh(env, `${r}/actions/runs/${args.run_id}/jobs`),
      ]);
      return {
        id: run.id,
        name: run.name,
        status: run.status,
        conclusion: run.conclusion,
        branch: run.head_branch,
        sha: run.head_sha?.slice(0, 7),
        started: run.run_started_at,
        updated: run.updated_at,
        url: run.html_url,
        jobs: jobs.jobs.map((j) => ({
          name: j.name,
          status: j.status,
          conclusion: j.conclusion,
          started: j.started_at,
          completed: j.completed_at,
          steps: j.steps?.map((s) => ({
            name: s.name,
            status: s.status,
            conclusion: s.conclusion,
          })),
        })),
      };
    }

    case "list_releases": {
      const data = await gh(
        env,
        `${r}/releases?per_page=${args.limit || 10}`
      );
      return data
        .filter((rel) => args.include_drafts || !rel.draft)
        .map((rel) => ({
          tag: rel.tag_name,
          name: rel.name,
          draft: rel.draft,
          prerelease: rel.prerelease,
          published: rel.published_at,
          assets: rel.assets.map((a) => ({
            name: a.name,
            size_mb: (a.size / 1048576).toFixed(1),
            downloads: a.download_count,
            url: a.browser_download_url,
          })),
          url: rel.html_url,
        }));
    }

    case "rerun_failed_jobs": {
      await gh(env, `${r}/actions/runs/${args.run_id}/rerun-failed-jobs`, {
        method: "POST",
      });
      return { rerun_triggered: true, run_id: args.run_id };
    }

    // ── Repo Management ──

    case "list_pull_requests": {
      const state = args.state || "open";
      const data = await gh(
        env,
        `${r}/pulls?state=${state}&per_page=${args.limit || 10}`
      );
      return data.map((pr) => ({
        number: pr.number,
        title: pr.title,
        state: pr.state,
        author: pr.user.login,
        branch: pr.head.ref,
        labels: pr.labels.map((l) => l.name),
        draft: pr.draft,
        created: pr.created_at,
        updated: pr.updated_at,
        url: pr.html_url,
      }));
    }

    case "get_pull_request": {
      const [pr, reviews, checks] = await Promise.all([
        gh(env, `${r}/pulls/${args.number}`),
        gh(env, `${r}/pulls/${args.number}/reviews`),
        gh(
          env,
          `${r}/commits/${(await gh(env, `${r}/pulls/${args.number}`)).head.sha}/check-runs`
        ),
      ]);
      return {
        number: pr.number,
        title: pr.title,
        state: pr.state,
        author: pr.user.login,
        branch: pr.head.ref,
        base: pr.base.ref,
        mergeable: pr.mergeable,
        merged: pr.merged,
        additions: pr.additions,
        deletions: pr.deletions,
        changed_files: pr.changed_files,
        labels: pr.labels.map((l) => l.name),
        reviews: reviews.map((rv) => ({
          user: rv.user.login,
          state: rv.state,
          submitted: rv.submitted_at,
        })),
        checks: checks.check_runs.map((c) => ({
          name: c.name,
          status: c.status,
          conclusion: c.conclusion,
        })),
        url: pr.html_url,
      };
    }

    case "create_pull_request": {
      const pr = await gh(env, `${r}/pulls`, {
        method: "POST",
        body: {
          title: args.title,
          body: args.body || "",
          head: args.head,
          base: args.base || "main",
          draft: args.draft || false,
        },
      });
      return {
        number: pr.number,
        url: pr.html_url,
        title: pr.title,
      };
    }

    case "merge_pull_request": {
      const res = await gh(env, `${r}/pulls/${args.number}/merge`, {
        method: "PUT",
        body: {
          merge_method: args.method || "squash",
          commit_title: args.commit_title,
        },
      });
      return { merged: true, sha: res.sha, message: res.message };
    }

    case "list_issues": {
      const state = args.state || "open";
      let path = `${r}/issues?state=${state}&per_page=${args.limit || 10}`;
      if (args.labels) path += `&labels=${encodeURIComponent(args.labels)}`;
      const data = await gh(env, path);
      // Filter out PRs (GitHub's issues API includes them)
      return data
        .filter((i) => !i.pull_request)
        .map((i) => ({
          number: i.number,
          title: i.title,
          state: i.state,
          author: i.user.login,
          labels: i.labels.map((l) => l.name),
          assignees: i.assignees.map((a) => a.login),
          milestone: i.milestone?.title,
          created: i.created_at,
          url: i.html_url,
        }));
    }

    case "create_issue": {
      const issue = await gh(env, `${r}/issues`, {
        method: "POST",
        body: {
          title: args.title,
          body: args.body || "",
          labels: args.labels || [],
          assignees: args.assignees || [],
        },
      });
      return {
        number: issue.number,
        url: issue.html_url,
        title: issue.title,
      };
    }

    case "repo_info": {
      const [info, langs] = await Promise.all([
        gh(env, r),
        gh(env, `${r}/languages`),
      ]);
      return {
        name: info.full_name,
        description: info.description,
        private: info.private,
        default_branch: info.default_branch,
        stars: info.stargazers_count,
        forks: info.forks_count,
        open_issues: info.open_issues_count,
        languages: langs,
        created: info.created_at,
        pushed: info.pushed_at,
        homepage: info.homepage,
        url: info.html_url,
      };
    }

    case "list_branches": {
      const data = await gh(
        env,
        `${r}/branches?per_page=${args.limit || 30}`
      );
      return data.map((b) => ({
        name: b.name,
        sha: b.commit.sha.slice(0, 7),
        protected: b.protected,
      }));
    }

    default:
      return { error: `Unknown tool: ${name}` };
  }
}

// ─── MCP Protocol handler ───────────────────────────────────────────

function jsonrpc(id, result) {
  return Response.json({ jsonrpc: "2.0", id, result });
}

function jsonrpcError(id, code, message) {
  return Response.json({ jsonrpc: "2.0", id, error: { code, message } });
}

async function handleMCP(request, env) {
  const body = await request.json();
  const { id, method, params } = body;

  switch (method) {
    case "initialize":
      return jsonrpc(id, {
        protocolVersion: "2024-11-05",
        serverInfo: {
          name: "arcana-forensics-mcp",
          version: "1.0.0",
        },
        capabilities: {
          tools: { listChanged: false },
        },
      });

    case "notifications/initialized":
      // Client acknowledged — no response needed for notifications
      return new Response(null, { status: 204 });

    case "tools/list":
      return jsonrpc(id, { tools: TOOLS });

    case "tools/call": {
      const { name, arguments: args } = params;
      try {
        const result = await handleTool(name, args || {}, env);
        return jsonrpc(id, {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        });
      } catch (err) {
        return jsonrpc(id, {
          content: [{ type: "text", text: `Error: ${err.message}` }],
          isError: true,
        });
      }
    }

    default:
      return jsonrpcError(id, -32601, `Method not found: ${method}`);
  }
}

// ─── Worker entry point ─────────────────────────────────────────────

export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
      });
    }

    // Health check
    if (request.method === "GET") {
      return Response.json({
        service: "arcana-forensics-mcp",
        version: "1.0.0",
        status: "ok",
        tools: TOOLS.length,
      });
    }

    // MCP requests must be POST
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    // Authenticate
    const auth = request.headers.get("Authorization");
    if (env.MCP_SHARED_SECRET) {
      if (!auth || auth !== `Bearer ${env.MCP_SHARED_SECRET}`) {
        return new Response("Unauthorized", { status: 401 });
      }
    }

    try {
      const response = await handleMCP(request, env);
      // Add CORS headers to the response
      const headers = new Headers(response.headers);
      headers.set("Access-Control-Allow-Origin", "*");
      return new Response(response.body, {
        status: response.status,
        headers,
      });
    } catch (err) {
      return Response.json(
        {
          jsonrpc: "2.0",
          id: null,
          error: { code: -32603, message: err.message },
        },
        { status: 500 }
      );
    }
  },
};
