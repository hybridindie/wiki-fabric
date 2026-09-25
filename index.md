---
okf_version: "0.2"
---

# Wiki Fabric — Knowledge Bundle

This repository is a conformant [OKF v0.2](https://okf.md/spec/) knowledge bundle:
a directory of markdown files with YAML frontmatter, readable by humans and agents
without special tooling.

## Bundle Map

* [AGENTS.md](AGENTS.md) - Master contract: note types, provenance rules, workflows
* [README.md](README.md) - Project overview and quick start
* [schemas/frontmatter.md](schemas/frontmatter.md) - Per-type frontmatter contracts
* [schemas/ontology.md](schemas/ontology.md) - Live domain taxonomy
* [registry/epics/okf-alignment.md](registry/epics/okf-alignment.md) - OKF v0.2 alignment epic & status
* [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution workflow and gates

## Fabric content layout

The fabric holds **knowledge atoms** (evidence/, patterns/, concepts/, domains/,
projects/, ...). These live in the content root — the sibling `vault/corpus/` by
default — not in the harness repo (they are gitignored here). `wf status` and
`wf query` operate on that content root; see AGENTS.md "Where Things Live".

## Registry

* [registry/catalog.json](registry/catalog.json) - Auto-generated catalog (machine-readable)
* [registry/log.md](registry/log.md) - Append-only operation timeline (OKF §9 shape)
