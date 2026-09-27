"""wiki_lib — export-wiki's internals, split by responsibility (#124.5).

modules:
  diagrams   — mermaid fence extraction/validate/repair
  edges      — wiki cross-page edges + the citation graph
  generators — article generators (topic/project/index/hubs) + LLM prompts
               + page enrichment + provenance/citation/staleness helpers

export-wiki.py remains the pipeline entry (main + corpus-side helpers);
the modules here are imported by it. Paths: keep everything relative to
fabric_config — no new global state.
"""
