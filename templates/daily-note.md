---
type: daily-note
description: "<One-line summary for index and search>"
project: "<your-project-slug>"
date: "{{date:YYYY-MM-DD}}"
tags: [daily-note]
---

# Daily Note: {{date:YYYY-MM-DD}}

## 🎯 Today's Focus

- [ ] <primary goal>
- [ ] <secondary goal>

## 📝 Fabric Queries

```dataview
TABLE project, observed_problem, intervention, outcomes
FROM "02-Human/Projects"
WHERE type = "experience-event" AND created = date(today)
SORT created DESC
```

## 📥 Inbox

- [ ] <item to process>

## 🔍 Fabric Queries Run

| Query | Result | Action |
|-------|--------|--------|
| <query> | <result> | <action> |

## 💡 Insights / Observations

- <insight 1>
- <insight 2>

## 📝 Decisions Made

- [ ] [[decision-<slug>]] — <brief description>

## 📤 Experience Events to Capture

- [ ] <problem observed> → intervention: <what you did>

## 📚 Sources to Ingest

- [ ] <source path> → reason: <why>

## 📊 Metrics

| Metric | Value |
|--------|-------|
| Sources ingested | 0 |
| Claims extracted | 0 |
| Experience events logged | 0 |