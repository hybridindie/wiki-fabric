# Fixture A — harness performance excerpt

The Godot editor is **single-threaded**: the addon drains queued command packets
once per `_process` frame and executes them serially on the main thread
(~50–100ms/command). The only levers are **fatter commands** and **fewer
commands**.

## 1. Batch arbitrary commands — `godot_composite_run_commands` (#167)

When you have N commands to run, send them as **one**
`godot_composite_run_commands` batch instead of N tool calls. The addon executes
the whole list in a single frame; N round-trips collapse to one.
`stop_on_error: true` halts at the first failure; false runs them all.
`godot_composite_run_commands` cannot be nested.

## 2. Pipeline independent reads — `gather_reads` (#169)

Awaiting each read in turn pays ~one frame of latency per read. The bridge
correlates responses by `id`, so many reads can be in flight at once: an
O(N)-frame discovery phase becomes ~O(1). Only read-only commands pipeline
safely — the editor is a single writer, so writes must stay ordered.
`gather_reads` rejects any non-read command with a `ValueError`.

## 3. Cache stable reads — `ReadCache` (#170)

Scene structure and node-property lists don't change *between* mutations, yet
harnesses often re-fetch them every step. `ReadCache` memoizes read-only
results per session and drops them on a write, so repeated identical reads cost
one round-trip instead of many. The cache is **per session** — unlike the old
server-side preflight cache, which was a process-global cleared on every
mutation and could bleed across sessions (removed in #166).
