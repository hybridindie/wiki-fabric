#!/usr/bin/env python3
"""wiki-fabric MCP server (#117) — the core surface as native tools.

Stdio MCP server (graphify's serve.py shape, mcp 1.x/2.x dual-compat).
Tools wrap the REAL scripts via subprocess — never a reimplementation
(anti-loop rule 7): the 0-token core stays import-isolated and every
tool call runs exactly what `wf` runs.

Tool classes:
  read/query tools  — query, context, thread, doctor (0 tokens)
  status tools      — gate (pending HITL), integrations (0 tokens)
  log tool          — log-experience (the mining intake; same validation
                      as wf log — the one mutation, gated by schema)
Mutations beyond `log` stay CLI-gated: no promote/ingest/sync tools.

Launch: wf-mcp (console script, [project.scripts], the `mcp` extra).
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# script resolution: dev tree (repo root) or packaged _harness/
_PACKAGED = Path(__file__).resolve().parent / "_harness"
_HERE = _PACKAGED if (_PACKAGED / "scripts").exists() else Path(__file__).resolve().parent.parent.parent


def _script(rel: str) -> Path:
    """Path to a shipped script (dev tree or packaged _harness)."""
    for base in (_HERE, _PACKAGED):
        cand = base / rel
        if cand.exists():
            return cand
    raise FileNotFoundError(rel)


def _run_script(rel: str, *args: str, timeout: int = 120) -> str:
    """Run a shipped script with the current interpreter — what `wf` does."""
    script = _script(rel)
    out = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, timeout=timeout,
    )
    text = (out.stdout or "").strip()
    if out.returncode != 0 and not text:
        text = (out.stderr or "").strip()[:2000]
    return text


TOOLS = [
    types.Tool(
        name="fabric_query",
        description="Ask the wiki-fabric an evidence-backed question (0 tokens). Returns a structured answer: bottom line, cited claims with source locators, related pages, confidence.",
        inputSchema={
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question to ask the knowledge fabric"},
                "type": {"type": "string", "enum": ["auto", "decision", "verify", "compare", "gap", "concept"]},
            },
            "required": ["question"],
        },
    ),
    types.Tool(
        name="fabric_context",
        description="Compile a task-scoped context manifest (0 tokens): relevant claims, patterns, decisions (project > domain > global precedence), every item with a reason. Run before starting a task.",
        inputSchema={
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "project": {"type": "string", "description": "Pin a project namespace"},
                "paths": {"type": "array", "items": {"type": "string"}},
                "format": {"type": "string", "enum": ["markdown", "json"]},
            },
            "required": ["task"],
        },
    ),
    types.Tool(
        name="fabric_gate",
        description="Aggregate pending human-in-the-loop decisions (0 tokens): stale claims, promotion dossiers, domain proposals, open questions. Exit semantics: report content returned regardless; empty means nothing pending.",
        inputSchema={
            "type": "object",
            "properties": {"json": {"type": "boolean", "description": "Machine-readable output"}},
        },
    ),
    types.Tool(
        name="fabric_thread",
        description="Look up the evidence-graph neighborhood of a session/PR/claim (0 tokens): claims citing the node, files touched, continuation edges.",
        inputSchema={
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Session id, PR number, or capture file stem"},
                "stats": {"type": "boolean", "description": "Index inventory instead of a lookup"},
            },
        },
    ),
    types.Tool(
        name="fabric_log",
        description="Log an experience event (the mining intake). Records what went wrong, what was done, outcomes. The one mutating tool — same schema validation as `wf log`.",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "problem": {"type": "string"},
                "intervention": {"type": "string"},
                "conditions": {"type": "string", "description": "key=value pairs, comma-separated"},
                "outcomes": {"type": "string", "description": "key=value pairs, comma-separated"},
                "tags": {"type": "string", "description": "Comma-separated"},
                "session": {"type": "string", "description": "Source session id (thread-index join key)"},
                "receipt": {"type": "string", "description": "Context delivery receipt id (#87 linkage)"},
            },
            "required": ["project", "problem"],
        },
    ),
]


def _call_tool(name: str, arguments: dict) -> str:
    args = {k: v for k, v in (arguments or {}).items() if v is not None}
    if name == "fabric_query":
        argv = ["scripts/cmd/query.py", args["question"]]
        if args.get("type"):
            argv += ["--type", args["type"]]
        return _run_script(*argv)
    if name == "fabric_context":
        argv = ["scripts/cmd/context.py", "--task", args["task"]]
        if args.get("project"):
            argv += ["--project", args["project"]]
        for p in args.get("paths") or []:
            argv += ["--paths", str(p)]
        if args.get("format") == "json":
            argv += ["--format", "json"]
        return _run_script(*argv)
    if name == "fabric_gate":
        argv = ["scripts/cmd/gate.py"]
        if args.get("json"):
            argv += ["--json"]
        return _run_script(*argv)
    if name == "fabric_thread":
        argv = ["scripts/cmd/thread.py"]
        if args.get("stats"):
            argv += ["--stats"]
        elif args.get("id"):
            argv += [args["id"]]
        return _run_script(*argv)
    if name == "fabric_log":
        argv = ["scripts/cmd/log-experience.py"]
        for k in ("project", "problem", "intervention", "conditions",
                  "outcomes", "tags", "session", "receipt"):
            if args.get(k):
                argv += [f"--{k}", str(args[k])]
        if len(argv) % 2 == 0:  # no --project/--problem pair
            return "error: project and problem are required"
        return _run_script(*argv)
    raise ValueError(f"unknown tool: {name}")


def _build_server() -> Server:
    server = Server("wiki-fabric")

    # mcp 1.x exposes decorators; 2.x uses constructor callbacks (same
    # pattern as graphify serve.py — clients on either share the toolset)
    async def list_tools() -> list[types.Tool]:
        return TOOLS

    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        try:
            text = _call_tool(name, arguments)
        except Exception as e:  # tool failures surface as isError results
            return [types.TextContent(type="text", text=f"error: {e}")]
        return [types.TextContent(type="text", text=text)]

    if hasattr(Server, "list_tools"):
        server = Server("wiki-fabric")
        server.list_tools()(list_tools)
        server.call_tool()(call_tool)
        return server

    async def _on_list_tools(ctx, params) -> types.ListToolsResult:
        return types.ListToolsResult(tools=await list_tools())

    async def _on_call_tool(ctx, params) -> types.CallToolResult:
        try:
            content = await call_tool(params.name, dict(params.arguments or {}))
            return types.CallToolResult(content=content)
        except Exception as e:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=f"error: {e}")],
                isError=True)

    server = Server(
        "wiki-fabric",
        on_list_tools=_on_list_tools,
        on_call_tool=_on_call_tool,
    )
    return server


def main() -> None:
    import asyncio

    async def _serve():
        server = _build_server()
        options = server.create_initialization_options()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, options,
                             raise_exceptions=False)

    asyncio.run(_serve())


if __name__ == "__main__":
    main()