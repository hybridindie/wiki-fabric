# Fixture C — two sources that contradict (test contradiction detection)

Two hypothetical claims about KV-cache memory, stated by two different sources,
one a measurement and one a paper. They conflict, and the ingest must represent
that as a `contradicts` relation plus a `status: contested` claim, not silently
merge.

## Source C1: an engineering blog (secondary)

> "Paged attention roughly halves KV-cache memory fragmentation under heavy
>  continuous batching on H100, at a constant 1.5x throughput."
> (single anecdotal benchmark, no config disclosed)

## Source C2: a primary paper abstract (primary)

> "Paged attention reduces fragmentation, but on A100 80GB the throughput gain
>  is 12±3%; the headline figure requires specific batch sizes and a
>  context length < 4096."

## Expected behavior

- One `claim` with `status: contested`.
- `source_refs` to both C1 and C2, with locators.
- A `relations` entry: one `contradicts` the other.
- `applies_when` must differ between the two refs (config-dependent).
- A `synthesis` answer must surface the conflict, not collapse it.
