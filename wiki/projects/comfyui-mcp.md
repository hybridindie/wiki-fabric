---
type: index
title: "comfyui-mcp: What We Learned"
review_after: 2027-03-20
---

# comfyui-mcp: What We Learned

## Current state

46 verified claim(s) from 46 analyzed sources.

## Key findings

- comfyui_mcp is a standalone MCP server for ComfyUI that is usable by any AI agent harness over stdio or Streamable HTTP." [1]
- The comfyui_mcp server is built on FastMCP 4 and enables AI assistants to generate images, run workflows, and manage jobs through ComfyUI wi [2]
- The MCP framework used is fastmcp[tasks] 4.0.0b1, a standalone FastMCP 4 beta built on MCP SDK v2." [3]
- SecurityMiddleware provides centralized rate limiting and entry audit logging via the FastMCP 4 on_call_tool hook across every tool call." [4]
- The Workflow Inspector detects dangerous nodes such as eval and exec, and in enforce mode asks the user to confirm before submitting a flagg [5]
- The configuration file for comfyui_mcp is located at ~/.comfyui-mcp/config.yaml." [6]
- The security.mode setting accepts two values: \"audit\" (log only) or \"enforce\" (block unapproved nodes, elicit user on warnings)." [7]
- The ComfyUI-Model-Manager plugin wraps all its responses in a {\"success\": bool, \"data\": <payload>} envelope, which the MCP client normal [8]
- The previewFile field is always required for POST /model-manager/model calls because save_model_preview() is invoked server-side regardless, [9]
- After a download finishes, the task remains in the list with status \"pause\" and progress 100, which is upstream behavior, and cancel_downl [10]
- Tests use pytest-asyncio with asyncio_mode = auto and mock ComfyUI API responses with respx." [11]
- The _DEFAULT_DANGEROUS_NODES list in config.py contains real ComfyUI custom node class_type values grouped by threat category (code executio [12]
- comfyui-mcp-secure version 2.2.0 was released on 2026-08-29." [13]
- The workflow inspector in v2.2.0 fetches ComfyUI's /node_replacements map and warns when a submitted class_type will be silently rewritten s [14]
- _DEFAULT_DANGEROUS_NODES in v2.2.0 includes all 135 first-party ComfyUI cloud API node class_types across 16 vendors, which send user prompt [15]

