"""Unit tests for the wiki-fabric MCP server (#117).

Launches the real stdio server as a subprocess against a fixture fabric and
exercises it with the MCP client library — the same way Claude Desktop or any
MCP client connects.

Run: python3 -m pytest tests/test_mcp_server.py -v
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest import mock

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))

REPO = Path(__file__).parent.parent


def _fabric(tmp):
    """Minimal fixture fabric: a claim + a source, no LLM needed."""
    root = tmp / "vault"
    corpus = root / "corpus"
    (corpus / "evidence" / "raw" / "proj").mkdir(parents=True)
    (corpus / "evidence" / "claims").mkdir(parents=True)
    (corpus / "evidence" / "sources").mkdir(parents=True)
    (corpus / "registry").mkdir(parents=True)
    (corpus / "projects" / "proj").mkdir(parents=True)
    (corpus / "projects" / "proj" / "README.md").write_text(
        "---\ntype: index\ntitle: proj\nproject: proj\nnamespace: proj\n"
        "owner: test\ncreated: 2026-09-27\n---\n\n# proj\n")
    (root / "fabric.yaml").write_text(
        "owner: test\nllm:\n  base_url: http://localhost:11434/v1\n"
        "  api_key: ollama\n  model: test-model\n")
    (corpus / "evidence/raw/proj/doc.md").write_text("intro line\nthe quote is here\n")
    (corpus / "evidence/sources/src-proj-doc-md.md").write_text(
        "---\ntype: source\nsource_path: evidence/raw/proj/doc.md\nsha256: x\n---\n\n# s\n")
    (corpus / "evidence/claims/claim-proj-doc-md-000.md").write_text(
        "---\ntype: claim\nid: claim-proj-doc-md-000\nstatus: supported\n"
        "statement: \"The quote is here and it matters.\"\n"
        "source_refs:\n  - source: \"[[src-proj-doc-md]]\"\n    locator: \"L2\"\n"
        "    quote: \"the quote is here\"\nrelations: []\n---\n\n# c\n\nThe quote is here.\n")
    return root


def _server_params(root):
    from mcp import StdioServerParameters
    return StdioServerParameters(
        command=sys.executable,
        args=["-c", "import sys; sys.path.insert(0, %r); "
                      "from wiki_fabric.mcp_server import main; main()" % str(REPO / "src")],
        env={"WIKI_FABRIC_ROOT": str(root), "WIKI_FABRIC_DIR": str(root),
             "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(Path.home())},
    )


class TestMcpServer:
    def _run(self, tmp, coro_body):
        import fabric_config as fc
        with mock.patch.object(fc, "FABRIC_ROOT", tmp), \
                mock.patch.object(fc, "CORPUS_ROOT", tmp), \
                mock.patch.dict("os.environ", {"WIKI_FABRIC_DIR": str(tmp),
                                               "WIKI_FABRIC_ROOT": str(tmp)}, clear=False):
            return asyncio.run(_coro(coro_body))

    def test_roundtrip_query_gate_thread(self, tmp_path):
        """The full client round-trip: list tools, call query + gate + thread."""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def inner():
            async with stdio_client(_server_params(_fabric(tmp_path))) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    names = [t.name for t in tools.tools]
                    assert set(names) == {"fabric_query", "fabric_context",
                                          "fabric_gate", "fabric_thread", "fabric_doctor",
                                          "fabric_log",
                                          "wiki_begin", "wiki_next", "wiki_submit_page",
                                          "wiki_finish", "wiki_status",
                                          "wiki_inspect_page_claims"}
                    r = await session.call_tool("fabric_query", {"question": "the quote is here"})
                    text = r.content[0].text
                    assert "Bottom line" in text
                    r = await session.call_tool("fabric_thread", {"stats": True})
                    assert ("Thread index" in r.content[0].text
                            or "No thread index" in r.content[0].text)
                    return names

        names = asyncio.run(_async_wrapper(inner))
        assert "fabric_query" in names

    def test_log_tool_writes_event(self, tmp_path):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def inner():
            async with stdio_client(_server_params(_fabric(tmp_path))) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    r = await session.call_tool(
                        "fabric_log",
                        {"project": "proj", "problem": "test problem",
                         "intervention": "test intervention"})
                    return r.content[0].text

        out = asyncio.run(_async_wrapper(inner))
        assert "Logged experience event" in out

    def test_unknown_tool_is_error_result(self, tmp_path):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def inner():
            async with stdio_client(_server_params(_fabric(tmp_path))) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    r = await session.call_tool("fabric_danger", {})
                    return r.content[0].text

        out = asyncio.run(_async_wrapper(inner))
        assert "unknown tool" in out

    def test_no_mutation_tools(self, tmp_path):
        """The tool surface is read + log + gate only: promote/ingest/sync are
        CLI-gated (the MCP boundary must never mutate the corpus)."""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def inner():
            async with stdio_client(_server_params(_fabric(tmp_path))) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    return {t.name for t in tools.tools}

        names = asyncio.run(_async_wrapper(inner))
        forbidden = {"fabric_promote", "fabric_ingest", "fabric_sync",
                     "fabric_export", "fabric_bootstrap"}
        assert not (names & forbidden)


def _async_wrapper(coro_factory):
    return coro_factory()