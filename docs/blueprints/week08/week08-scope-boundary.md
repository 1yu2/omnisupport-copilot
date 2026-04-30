# Week8 Scope Boundary

Week 8：从“搜得到”到“答得稳”——检索 × 生成的一体化工程闭环

## 本周主叙事

Week7 证据资产 → Week8 索引资产 → 混合检索 → 重排 → 结构化 RAG API → 审计与回归。

Week8 的核心不是“接一个聊天机器人”，而是把可引用文档资产升级成可版本化、可过滤、可解释、可审计、可回归的检索与生成接口。

## Student Core

| 能力 | 本周默认路径 |
|---|---|
| 存储 | PostgreSQL |
| 向量 | pgvector |
| 关键词 | PostgreSQL FTS |
| 融合 | RRF |
| 重排 | optional CrossEncoder，失败时回退 RRF |
| 生成 | RAG API contract + Prompt as Code |
| 引用 | evidence metadata only，不允许 LLM 编造 |
| 审计 | request / retrieved evidence / scores / response / release ids |

## 降级路线

| 故障 | 降级方式 |
|---|---|
| Week7 chunks 不足 | 使用 synthetic ready chunks fixture，明确标记 placeholder |
| Embedding provider 不可用 | dry-run 仍可完成；real build 报告 provider unavailable |
| Embedding 维度不匹配 | 拒绝写入 `vector(1536)`，在 index report 写 dimension mismatch |
| CrossEncoder 不可用 | 跳过 rerank，继续返回 RRF 结果 |
| LLM key 不可用 | 返回 citation-carrying fallback 或 structured no-answer |
| 权限 / filter 后无结果 | 返回 `abstain_reason`，不生成假答案 |

## 不做边界

- 不实现 Week10 ticket action / HITL 主流程。
- 不做 Week11 full eval harness。
- 不做 Week12 full tracing / Phoenix bad-case 系统。
- 不做 GraphRAG。
- 不引入外部向量数据库作为 Student Core。
- 不重写 Week7 parse/chunk/evidence 主逻辑。
- 不允许 generator 临时发明 citation。

## 本周完成后的判断标准

1. 每次 RAG response 都带 `index_release_id`、`prompt_release_id`、`trace_id`。
2. 每条 citation 都来自 retrieval result 的 evidence metadata。
3. vector-only、FTS-only、hybrid RRF、rerank fallback 都能被 smoke 验证。
4. no-answer 是一等路径，而不是异常。
5. 报告和 runbook 能让学员解释：为什么只向量检索不够，为什么 citation 不能编造，为什么 release id 必须进入 response。
