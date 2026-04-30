# Week8 Current State Diagnosis

Week 8：从“搜得到”到“答得稳”——检索 × 生成的一体化工程闭环

## 已有可复用能力

| 区域 | 当前状态 | Week8 复用方式 |
|---|---|---|
| PostgreSQL / pgvector | `infra/migrations/001_init.sql` 已创建 `knowledge_doc`、`knowledge_section.embedding vector(1536)`、FTS GIN 索引和 `evidence_anchor` | 继续使用 PostgreSQL + pgvector + PostgreSQL FTS 作为 Student Core，不引入外部向量库 |
| Indexing | `pipelines/indexing/embedder.py` 已能读取 `knowledge_section`、写入 embedding 与 `index_release_id` | 增强为可 dry-run、可报告、可生成 index manifest 的 index build，不重写 embedding 系统 |
| Retrieval | `services/rag_api/app/retrieval.py` 已有 vector search、FTS、RRF、CrossEncoder fallback 雏形 | 增强 metadata filter、debug scores、evidence metadata 和 rerank fallback，不新建平行 retrieval 模块 |
| RAG API | `services/rag_api/app/routers/query.py` 已有 `/api/v1/query` 与健康检查 | 保留兼容端点，新增 Week8 契约化 `/rag/answer` |
| Release IDs | `settings` 已有 `release_id`、`data_release_id`、`index_release_id`、`prompt_release_id` | 将 release ids 进入 response、audit、reports |
| Week6/7 链路 | 已有 Week06 run evidence 和 Week07 课程设计 | Week8 只消费已通过 gate 的 chunks；不足时使用明确 placeholder，不伪造成熟状态 |

## 必须补齐的 gap

### Blocker

- `contracts/service/` 缺 RAG request / response / citation / retrieval debug schema。
- `contracts/release/index_manifest.schema.json` 缺 index release contract。
- `pipeline/indexing` 缺 index manifest/reporting 模块，当前 build 没有稳定报告产物。
- `pipelines/definitions.py` 未注册 indexing assets。
- RAG response 缺 `data_release_id`、`index_release_id`、`prompt_release_id`、`abstain_reason`、`retrieval_debug`。

### Yellow flag

- `knowledge_section.embedding` 固定为 `vector(1536)`，但 Voyage/local sentence-transformers 可能输出 1024/384 维。必须显式拒绝维度不匹配，不能默默写入。
- 当前 audit 写到通用 `audit_log`，不足以表达 retrieval scores、citations、release ids。
- 当前 generator 内置 prompt 字符串，不利于 prompt release / rollback / smoke 对比。

### Safe-to-implement

- 新增 Week8 contracts、fixtures、contract tests。
- 新增 `index_manifest`、`index_build_log`、`rag_audit_log` migration。
- 增强现有 indexing / retrieval / generator / routers，不破坏 Week01-Week07 主线。
- 新增 smoke eval 脚本和样例报告。

### Should-defer

- Week10 tool action / HITL。
- Week11 full RAGAS 或 LLM-as-judge 评测系统。
- Week12 Phoenix bad-case 深度 tracing。
- Week13 GraphRAG。
- Week14 lakeFS / OpenLineage release governance 全量工作流。
- Pinecone / Weaviate / Qdrant / OpenSearch / Azure AI Search 等外部向量库生产化。

## 兼容策略

- Runtime 以当前已落地的 `knowledge_doc` / `knowledge_section` / `evidence_anchor` 为准。
- 如果后续 Week7 引入 `document_chunk`，Week8 将 `document_chunk.chunk_id` 映射到当前 `knowledge_section.section_id`，课程文档中说明此兼容层。
- 如果 Week7 evidence 尚不足，使用 synthetic fixture 或 no-answer fallback，并在 reports 中标注 placeholder。
- 如果 LLM key 不存在，RAG API 返回结构化 fallback / abstain response，不让链路直接失败。
