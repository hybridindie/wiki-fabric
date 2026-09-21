---
type: index
title: "godot-agents: What We Learned"
review_after: 2027-03-20
---

# godot-agents: What We Learned

## Current state

109 verified claim(s) from 109 analyzed sources.

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
- The knowledge fabric is accessible by default at a specific local path, but this location can be overridden." [11]
- Running `wf context --task` compiles a scoped manifest of relevant information and decisions before a task begins, and this operation incurs [12]
- For codebase or architecture questions, `wf query` provides evidence-backed answers with locators and also operates with zero token cost." [13]
- The CLI prevents the re-ingestion of a source if its SHA256 hash has already been recorded, and it notifies the user of this action." [14]
- Promotion of work is a human-gated process where the `wf` system proposes dossiers, but the final promotion decision rests with the user." [15]

