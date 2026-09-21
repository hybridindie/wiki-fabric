---
type: index
title: "godot-agents: What We Learned"
review_after: 2027-03-20
---

# godot-agents: What We Learned

## Current state

96 verified claim(s) from 96 analyzed sources.

## Key findings

- The `godot-agents` repository functions as the orchestrator/client, depending on the `godot-mcp` repository for the actual Godot editor brid [1]
- The `godot-agents` system is tightly coupled to the specific `godot-mcp` server implementation, requiring its exact surface structure." [2]
- The client implementation mirrors the server's tool names and parameter keys exactly, serving as a contract between the two repositories." [3]
- For `godot-mcp` versions 2026.08.31b4 and later, toolset enablement is server-global and persists across client connections." [4]
- The default transport mechanism is stdio, requiring the `godot-mcp` CLI to be resolvable via environment variables or installation path." [5]
- Since version 2026.08.31b4, `godot-mcp` emits a structured payload, which the client prefers for normalization over text parsing." [6]
- The build/verify/fix loop is capped by a default of 3 retries and a recursion limit of 50." [7]
- Run durability can be configured using `sqlite` or `postgres` backends to survive restarts, though the default is a non-persistent in-proces [8]
- The client implements retry logic for transport failures using exponential backoff and a circuit breaker, but tool-level errors are determin [9]
- Upon first contact, the system performs a deterministic structural scan to populate the `project_map`, and subsequent runs skip this scan." [10]
- All configuration must be done via environment variables, as there is no configuration file." [11]
- The default transport mechanism for MCP is `stdio`." [12]
- The default port for HTTP transport is 9090." [13]
- Web search is disabled by default, requiring explicit opt-in to enable the retrieval band." [14]
- The experimental fluid executor is disabled by default, requiring explicit opt-in to activate the fluid loop." [15]

