import { describe, it, before, mock } from "node:test";
import assert from "node:assert/strict";

// ─── Import the worker module ──────────────────────────────────────

// We import the default export (the Cloudflare Worker fetch handler)
const mod = await import("../src/index.js");
const worker = mod.default;

// ─── Helpers ───────────────────────────────────────────────────────

const SECRET = "test-secret-42";

const env = {
  GITHUB_OWNER: "00Arcana-Forensic00",
  GITHUB_REPO: "00Arcana-Forensic00",
  GITHUB_TOKEN: "ghp_fake",
  MCP_SHARED_SECRET: SECRET,
  MCP_STATE: {},
};

function mcpRequest(method, params = {}, id = 1) {
  return new Request("https://mcp.test/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${SECRET}`,
    },
    body: JSON.stringify({ jsonrpc: "2.0", id, method, params }),
  });
}

function unauthRequest(method, params = {}) {
  return new Request("https://mcp.test/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
  });
}

// ─── Tests ─────────────────────────────────────────────────────────

describe("Worker entry point", () => {
  it("returns health check on GET", async () => {
    const req = new Request("https://mcp.test/", { method: "GET" });
    const res = await worker.fetch(req, env);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.equal(data.service, "arcana-forensics-mcp");
    assert.equal(data.status, "ok");
    assert.equal(typeof data.tools, "number");
    assert(data.tools >= 17);
  });

  it("returns CORS headers on OPTIONS", async () => {
    const req = new Request("https://mcp.test/", { method: "OPTIONS" });
    const res = await worker.fetch(req, env);
    assert.equal(res.headers.get("Access-Control-Allow-Origin"), "*");
    assert.equal(res.headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
  });

  it("rejects 405 on PUT", async () => {
    const req = new Request("https://mcp.test/", { method: "PUT" });
    const res = await worker.fetch(req, env);
    assert.equal(res.status, 405);
  });

  it("rejects 401 without auth header", async () => {
    const req = unauthRequest("initialize");
    const res = await worker.fetch(req, env);
    assert.equal(res.status, 401);
  });

  it("rejects 401 with wrong token", async () => {
    const req = new Request("https://mcp.test/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer wrong-token",
      },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "initialize" }),
    });
    const res = await worker.fetch(req, env);
    assert.equal(res.status, 401);
  });
});

describe("MCP protocol", () => {
  it("handles initialize", async () => {
    const res = await worker.fetch(mcpRequest("initialize"), env);
    const data = await res.json();
    assert.equal(data.jsonrpc, "2.0");
    assert.equal(data.id, 1);
    assert.equal(data.result.protocolVersion, "2024-11-05");
    assert.equal(data.result.serverInfo.name, "arcana-forensics-mcp");
    assert.deepEqual(data.result.capabilities.tools, { listChanged: false });
  });

  it("handles notifications/initialized with 204", async () => {
    const res = await worker.fetch(mcpRequest("notifications/initialized"), env);
    assert.equal(res.status, 204);
  });

  it("handles tools/list with all 17 tools", async () => {
    const res = await worker.fetch(mcpRequest("tools/list"), env);
    const data = await res.json();
    const tools = data.result.tools;
    assert(Array.isArray(tools));
    assert.equal(tools.length, 17);

    // Check all expected tools are present
    const names = tools.map((t) => t.name);
    const expected = [
      "vault_inspect", "ledger_verify", "list_vaults", "supported_formats",
      "trigger_workflow", "workflow_runs", "run_status", "list_releases", "rerun_failed_jobs",
      "list_pull_requests", "get_pull_request", "create_pull_request", "merge_pull_request",
      "list_issues", "create_issue", "repo_info", "list_branches",
    ];
    for (const name of expected) {
      assert(names.includes(name), `Missing tool: ${name}`);
    }

    // Each tool has required schema fields
    for (const tool of tools) {
      assert(typeof tool.name === "string");
      assert(typeof tool.description === "string");
      assert(typeof tool.inputSchema === "object");
      assert.equal(tool.inputSchema.type, "object");
    }
  });

  it("returns error for unknown method", async () => {
    const res = await worker.fetch(mcpRequest("unknown/method"), env);
    const data = await res.json();
    assert.equal(data.error.code, -32601);
    assert.match(data.error.message, /not found/i);
  });
});

describe("Tool: supported_formats", () => {
  it("returns image and video formats", async () => {
    const res = await worker.fetch(
      mcpRequest("tools/call", { name: "supported_formats", arguments: {} }),
      env
    );
    const data = await res.json();
    const content = JSON.parse(data.result.content[0].text);
    assert(Array.isArray(content.images));
    assert(Array.isArray(content.video));
    assert(content.images.includes("PNG"));
    assert(content.video.includes("MP4"));
  });
});

describe("Tool: unknown tool", () => {
  it("returns error for unknown tool name", async () => {
    const res = await worker.fetch(
      mcpRequest("tools/call", { name: "nonexistent", arguments: {} }),
      env
    );
    const data = await res.json();
    const content = JSON.parse(data.result.content[0].text);
    assert.match(content.error, /Unknown tool/);
  });
});

describe("CORS on MCP responses", () => {
  it("adds CORS header to MCP response", async () => {
    const res = await worker.fetch(mcpRequest("initialize"), env);
    assert.equal(res.headers.get("Access-Control-Allow-Origin"), "*");
  });
});

describe("Auth bypass when no secret configured", () => {
  it("allows requests when MCP_SHARED_SECRET is empty", async () => {
    const openEnv = { ...env, MCP_SHARED_SECRET: "" };
    const req = new Request("https://mcp.test/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "initialize" }),
    });
    const res = await worker.fetch(req, openEnv);
    assert.equal(res.status, 200);
    const data = await res.json();
    assert.equal(data.result.serverInfo.name, "arcana-forensics-mcp");
  });
});

describe("JSON-RPC envelope", () => {
  it("preserves the request id in responses", async () => {
    const res = await worker.fetch(mcpRequest("initialize", {}, 42), env);
    const data = await res.json();
    assert.equal(data.id, 42);
  });

  it("wraps tool errors in isError content", async () => {
    // Call a tool that will fail because fetch isn't mocked for GitHub API
    // supported_formats doesn't call GitHub, so use vault_inspect which will fail
    const res = await worker.fetch(
      mcpRequest("tools/call", {
        name: "vault_inspect",
        arguments: { vault_path: "test.arcr" },
      }),
      env
    );
    const data = await res.json();
    // Should get isError: true since GitHub fetch will fail
    assert.equal(data.result.isError, true);
    assert(data.result.content[0].text.startsWith("Error:"));
  });
});
