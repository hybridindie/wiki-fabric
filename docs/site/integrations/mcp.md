---
title: "MCP server — the fabric as native tools"
description: "wf-mcp: query/context/gate/thread as MCP tools for any MCP client"
type: index
---

# MCP (wf-mcp)

The fabric's core surface as native [MCP](https://modelcontextprotocol.io)
tools — any MCP client (Claude Desktop, opencode, Codex, custom agents)
gets the same 0-token surface the CLI offers, wrapped as a stdio server.

## Setup

```bash
uv tool install wiki-fabric --with mcp
wf-mcp          # stdio MCP server
```

Point your client at the binary (stdio transport):

```json
// opencode.json (or any MCP client config)
{ "mcp": { "wiki-fabric": { "type": "local",
    "command": ["wf-mcp"], "enabled": true } } }
```

## Tool surface

| Tool | Wraps | Cost |
|---|---|---|
| `fabric_query` | `wf query` | 0 tokens |
| `fabric_context` | `wf context` | 0 tokens |
| `fabric_gate` | `wf gate` | 0 tokens |
| `fabric_thread` | `wf thread` | 0 tokens |
| `fabric_log` | `wf log` | file write (the one mutation, schema-gated) |

**No reimplementation risk**: each tool is subprocess-wrapped — the real CLI
runs, the server translates inputs/outputs. Mutations beyond `log` stay
CLI-gated (a client gets the 0-token read surface plus the audit write;
promotions, merges, and config changes require the human at a terminal).

## When it earns its keep

- Your harness speaks MCP and you want the fabric as native tools rather
  than shelling out.
- Multi-client setups (desktop app + CLI agent reading the same fabric).

**Skip it when** your agent harness already wraps `wf` verbs directly (the
harness-support matrix) — the MCP layer would be an extra hop with no added
capability.