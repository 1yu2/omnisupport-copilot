# Week8 RAG API Smoke Report

## Endpoint

- `POST /rag/answer`

## Contract fields

- `answer`
- `citations`
- `evidence_ids`
- `confidence`
- `abstain_reason`
- `release_id`
- `data_release_id`
- `index_release_id`
- `prompt_release_id`
- `trace_id`

## Current local smoke

- No DB / no evidence path returns structured no-answer.
- Citations are derived from retrieval metadata only.
- Prompt templates are file-backed under `services/rag_api/app/prompts/`.
