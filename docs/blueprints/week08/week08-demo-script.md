# Week8 Demo Script

Week 8：从“搜得到”到“答得稳”——检索 × 生成的一体化工程闭环

## Demo spine

1. Show Week7 evidence assets as the upstream input.
2. Build a versioned index release.
3. Compare vector-only, FTS-only, and hybrid RRF behavior.
4. Show rerank fallback: when Cross-Encoder is unavailable, RRF still serves.
5. Call `/rag/answer` and inspect citations, evidence ids, release ids, prompt release id, and trace id.
6. Run smoke eval and inspect audit sample.
7. Point out PPT alignment paths: `pipelines/retrieve/*`, `pipelines/query/*`, and `services/rag_api/app/context_pruning.py`.

## Commands

```bash
docker compose --profile tools --env-file infra/env/.env.local -f infra/docker-compose.yml run --rm devbox \
  pytest tests/contract/ -v
```

```bash
docker compose --profile tools --env-file infra/env/.env.local -f infra/docker-compose.yml run --rm devbox \
  pytest tests/integration/test_week8_ppt_alignment.py -v
```

```bash
docker compose --profile tools --env-file infra/env/.env.local -f infra/docker-compose.yml run --rm devbox \
  python -m pipelines.indexing.embedder --index-release-id index-week08-dev --batch-size 32 --dry-run
```

```bash
curl -X POST http://localhost:8000/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"question":"How do I recover an Edge Gateway after firmware upgrade failure?","product_line":"edge-gateway","top_k":5,"index_release_id":"index-week08-dev","prompt_release_id":"prompt-week08-v1","include_debug":true}'
```

```bash
docker compose --profile tools --env-file infra/env/.env.local -f infra/docker-compose.yml run --rm devbox \
  python evals/week08/run_smoke_eval.py
```

## What to point out

- Retrieval filters run before generation. Permission filtering after generation is too late.
- `citation` objects come from retrieval metadata, not from the LLM.
- `index_release_id` and `prompt_release_id` make the answer reproducible.
- No-answer is a valid product behavior when evidence is absent or unsafe.
- Query Rewrite / HyDE / Adaptive RAG are deterministic classroom scaffolds in Week08, not full LLM agent loops.
