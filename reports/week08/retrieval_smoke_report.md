# Week8 Retrieval Smoke Report

## Scope

This sample report documents the intended Week8 smoke checks for hybrid retrieval.

## Cases

| Case | Expected behavior |
|---|---|
| vector-only | returns semantic candidates with `vector_score` |
| FTS-only | returns lexical candidates with `fts_score` |
| hybrid RRF | merges duplicate chunks and returns `rrf_score` |
| reranker unavailable | keeps RRF order and marks fallback |
| product_line filter | only returns matching product line |
| index_release_id filter | only returns chunks from the requested index release |

## Current status

- Contract and local RRF tests are implemented.
- Full DB-backed smoke requires Docker Compose and seeded Week7-ready chunks.
