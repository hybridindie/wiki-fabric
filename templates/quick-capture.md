---
type: quick-capture
title: "{{date:YYYY-MM-DD HH:mm}} - {{value:title}}"
project: <your-project-slug>
tags: [quick-capture]
created: {{date:YYYY-MM-DD}}
---

# Quick Capture: {{value:title}}

## Raw Input

{{value:content}}

## To Process

- [ ] Create source record in `evidence/sources/`
- [ ] Write source summary in `evidence/source-summaries/`
- [ ] Extract claims to `evidence/claims/`
- [ ] Link to project: `projects/<namespace>/`

## Quick Links

- [Ingest skill](command:obsidian://open?path=~/wiki-fabric/.opencode/skills/ingest/SKILL.md)
- [Lint](command:obsidian://open?path=~/wiki-fabric/scripts/lint.py)
- [Registry Index](obsidian://open?path={{vault}}/01-Raw/registry/index.md)