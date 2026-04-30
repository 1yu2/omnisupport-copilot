# Week8 Assignment Spec

Week 8：从“搜得到”到“答得稳”——检索 × 生成的一体化工程闭环

## Required artifacts

1. `reports/week08/index_build_report_<index_release_id>.md`
2. `reports/week08/retrieval_smoke_report.md`
3. `reports/week08/rag_api_smoke_report.md`
4. `reports/week08/smoke_eval_report.md`
5. `reports/week08/rag_audit_log.sample.jsonl` or a real exported audit sample.

## Architecture questions

Answer these in the delivery summary:

1. Why is vector-only retrieval insufficient for support knowledge?
2. Why must citations come from retrieval evidence instead of the LLM?
3. Why must `index_release_id` and `prompt_release_id` appear in the API response?

## Minimum acceptance

- Contract tests pass.
- Index dry-run produces a report.
- `/rag/answer` returns a structured response.
- Answer cases include citations/evidence ids or return a clear `abstain_reason`.
- Smoke eval report explains pass/fail/placeholder status.

## Not accepted

- Free-form answer without citations.
- Hard-coded fake citations.
- RAG API response missing release ids or trace id.
- A demo that only works with a private local venv and not Docker Compose/devbox.
