# Week8 Quarto Site Sync Checklist

Week 8：从“搜得到”到“答得稳”——检索 × 生成的一体化工程闭环

> 这份清单用于课程站点仓库同步。`omnisupport-copilot` 项目仓库不直接硬造 Quarto 页面。

## 需要新增的课程页

- `weeks/week08.qmd`
- `weeks/week08-lesson-1.qmd`
- `weeks/week08-lesson-2.qmd`
- `weeks/week08-lesson-3.qmd`
- `weeks/week08-lesson-4.qmd`
- `weeks/week08-lesson-5.qmd`
- `weeks/week08-lab.qmd`
- `weeks/week08-assignment.qmd`

## 五个课时标题

1. Lesson 01：为什么“搜得到”不等于“答得稳”：RAG 工程闭环的系统边界
2. Lesson 02：索引资产化：Embedding、Index Release、增量更新与回滚边界
3. Lesson 03：混合检索：pgvector + PostgreSQL FTS + RRF + Metadata Filter
4. Lesson 04：重排与生成门禁：Cross-Encoder rerank、证据筛选与 no-answer 策略
5. Lesson 05：RAG API 契约化：结构化输出、引用证据、Prompt as Code、审计日志

## 导航与站点数据

- `_quarto.yml` sidebar 加入 Week8。
- `data/current-learning.yml` 加入 Week8 学习卡。
- `scripts/build_handouts.py` 加入 5 个课时讲义。
- `appendix/glossary.qmd` 加入 pgvector、FTS、RRF、rerank、citation、prompt release、index release。
- `appendix/templates.qmd` 加入 Week8 模板下载。
- `appendix/reading-list.qmd` 加入 Week8 官方阅读材料。

## 建议模板

- `assets/templates/week08/index_manifest_template_v1.json`
- `assets/templates/week08/rag_request_template_v1.json`
- `assets/templates/week08/rag_response_template_v1.json`
- `assets/templates/week08/retrieval_smoke_report_v1.md`
- `assets/templates/week08/rag_api_smoke_report_v1.md`
- `assets/templates/week08/smoke_eval_report_v1.md`
- `assets/templates/week08/week08_delivery_summary_v1.md`

## 页面风格约束

- 复用 Week05 / Week06 / Week07 的 `hero-block`、`grid-two`、`info-card`、callout、Mermaid、标准 code block。
- 不新增外部 JS/CSS/CDN。
- 代码块使用站点统一复制按钮、语法高亮和横向滚动配置。
- 图示优先 Mermaid；如后续替换手绘图，放在 `assets/week08/`。
