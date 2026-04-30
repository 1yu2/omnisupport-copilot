"""Embedding + pgvector 索引构建

从 knowledge_section 读取待索引的 chunks，
调用 Embedding API 生成向量，写回 pgvector 列，
更新 index_release_id 与 knowledge_doc.chunk_count。

使用方式:
    python -m pipelines.indexing.embedder \
        --index-release-id index-v0.1.0 \
        --batch-size 64
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from pipelines.indexing.index_manifest import build_manifest
from pipelines.indexing.reporting import write_index_build_outputs

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1536   # text-embedding-3-small / voyage-2 default


# ── Embedding 提供者 ──────────────────────────────────────────────────────────

class EmbeddingProvider:
    """
    多后端嵌入提供者。按优先级尝试：
    1. Voyage AI (voyage-2, Anthropic 推荐)
    2. OpenAI text-embedding-3-small
    3. 本地 sentence-transformers (离线 fallback)
    """

    def __init__(self, model: str | None = None):
        self._model = model or os.environ.get("EMBEDDING_MODEL", "auto")
        self._backend = None

    def _init_backend(self):
        if self._backend:
            return

        model = self._model
        if model == "auto":
            # 按优先级探测可用后端
            for try_model in ["voyage-2", "text-embedding-3-small", "local"]:
                backend = self._try_init(try_model)
                if backend:
                    self._backend = backend
                    return
            raise RuntimeError("No embedding backend available")

        self._backend = self._try_init(model)
        if not self._backend:
            raise RuntimeError(f"Embedding backend '{model}' unavailable")

    def _try_init(self, model: str):
        if model == "voyage-2":
            return self._init_voyage()
        if model.startswith("text-embedding"):
            return self._init_openai(model)
        if model == "local":
            return self._init_local()
        return None

    def _init_voyage(self):
        try:
            if not os.environ.get("VOYAGE_API_KEY"):
                return None
            import voyageai
            client = voyageai.Client(api_key=os.environ.get("VOYAGE_API_KEY", ""))
            # 测试连通性
            logger.info("Using Voyage AI embeddings (voyage-2, dim=1024)")
            return ("voyage", client, "voyage-2", 1024)
        except Exception:
            return None

    def _init_openai(self, model: str):
        try:
            if not os.environ.get("OPENAI_API_KEY"):
                return None
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
            logger.info(f"Using OpenAI embeddings ({model}, dim=1536)")
            return ("openai", client, model, 1536)
        except Exception:
            return None

    def _init_local(self):
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Using local sentence-transformers (all-MiniLM-L6-v2, dim=384)")
            return ("local", model, "all-MiniLM-L6-v2", 384)
        except Exception:
            return None

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成嵌入向量，返回 list of float vectors"""
        self._init_backend()
        backend_type, client, model, dim = self._backend

        if backend_type == "voyage":
            result = client.embed(texts, model=model, input_type="document")
            return result.embeddings

        if backend_type == "openai":
            resp = client.embeddings.create(input=texts, model=model)
            return [item.embedding for item in resp.data]

        if backend_type == "local":
            embeddings = client.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()

        raise RuntimeError(f"Unknown backend: {backend_type}")

    @property
    def dim(self) -> int:
        self._init_backend()
        return self._backend[3]

    @property
    def provider(self) -> str:
        self._init_backend()
        return self._backend[0]

    @property
    def model(self) -> str:
        self._init_backend()
        return self._backend[2]


# ── 索引构建器 ────────────────────────────────────────────────────────────────

@dataclass
class IndexStats:
    index_release_id: str = ""
    data_release_id: str = ""
    chunk_strategy_version: str = ""
    provider: str = "unknown"
    embedding_model: str = "unknown"
    embedding_dim: int = 0
    total_chunks: int = 0
    embedded: int = 0
    skipped: int = 0
    errors: int = 0
    elapsed_sec: float = 0.0
    warnings: list[str] = field(default_factory=list)


async def build_index(
    index_release_id: str,
    batch_size: int = 64,
    doc_id: str | None = None,         # None = 全量
    dry_run: bool = False,
    data_release_id: str = "data-week08-dev",
    chunk_strategy_version: str = "section_aware_v1",
    report_dir: str | Path = "reports/week08",
) -> IndexStats:
    """
    从 knowledge_section 读取未索引的 chunks，
    批量嵌入，写回 embedding 列，更新 index_release_id。
    """
    from pipelines.ingestion.db import acquire

    stats = IndexStats(
        index_release_id=index_release_id,
        data_release_id=data_release_id,
        chunk_strategy_version=chunk_strategy_version,
    )
    provider = EmbeddingProvider()
    t0 = time.time()

    async with acquire() as conn:
        # 查询待索引 chunks（embedding IS NULL 或 index_release_id 不匹配）
        where_clauses = ["(embedding IS NULL OR index_release_id != $1)"]
        params: list = [index_release_id]

        if doc_id:
            where_clauses.append(f"doc_id = ${len(params)+1}")
            params.append(doc_id)

        rows = await conn.fetch(
            f"""
            SELECT section_id, doc_id, content
            FROM knowledge_section
            WHERE {" AND ".join(where_clauses)}
            ORDER BY doc_id, chunk_index
            """,
            *params,
        )

        stats.total_chunks = len(rows)
        logger.info(f"Found {stats.total_chunks} chunks to index (release: {index_release_id})")

        if dry_run:
            logger.info("[dry-run] Skipping actual embedding generation")
            stats.skipped = stats.total_chunks
            stats.elapsed_sec = time.time() - t0
            stats.provider = "dry_run"
            stats.embedding_model = "dry_run"
            stats.embedding_dim = EMBEDDING_DIM
            stats.warnings.append("dry_run=true; embeddings were not generated")
            _write_report(stats, report_dir)
            return stats

        try:
            stats.provider = provider.provider
            stats.embedding_model = provider.model
            stats.embedding_dim = provider.dim
        except Exception as e:
            stats.errors = stats.total_chunks
            stats.elapsed_sec = time.time() - t0
            stats.warnings.append(f"embedding provider unavailable: {e}")
            _write_report(stats, report_dir)
            return stats

        if stats.embedding_dim != EMBEDDING_DIM:
            stats.errors = stats.total_chunks
            stats.skipped = stats.total_chunks
            stats.elapsed_sec = time.time() - t0
            stats.warnings.append(
                f"dimension mismatch: provider returned {stats.embedding_dim}, "
                f"but knowledge_section.embedding is vector({EMBEDDING_DIM})"
            )
            _write_report(stats, report_dir)
            return stats

        # 批量处理
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            texts = [r["content"] for r in batch]
            ids = [r["section_id"] for r in batch]

            try:
                vectors = provider.embed_batch(texts)
            except Exception as e:
                logger.error(f"Embedding batch {i//batch_size} failed: {e}")
                stats.errors += len(batch)
                continue

            # 批量写回向量
            for row_id, vector in zip(ids, vectors):
                try:
                    await conn.execute(
                        """
                        UPDATE knowledge_section
                        SET embedding = $1::vector,
                            embedding_model = $2,
                            embedding_dim = $3,
                            index_release_id = $4,
                            data_release_id = $5,
                            chunk_strategy_version = $6,
                            indexed_at = NOW()
                        WHERE section_id = $7
                        """,
                        vector,
                        stats.embedding_model,
                        stats.embedding_dim,
                        index_release_id,
                        data_release_id,
                        chunk_strategy_version,
                        row_id,
                    )
                    stats.embedded += 1
                except Exception as e:
                    logger.error(f"Failed to update embedding for {row_id}: {e}")
                    stats.errors += 1

            if (i // batch_size) % 10 == 0:
                logger.info(f"Progress: {stats.embedded}/{stats.total_chunks} embedded")

        # 更新 knowledge_doc.chunk_count
        await conn.execute(
            """
            UPDATE knowledge_doc kd
            SET chunk_count = sub.cnt,
                index_release_id = $1,
                data_release_id = $2,
                indexed_at = NOW()
            FROM (
                SELECT doc_id, COUNT(*) AS cnt
                FROM knowledge_section
                WHERE index_release_id = $1
                GROUP BY doc_id
            ) sub
            WHERE kd.doc_id = sub.doc_id
            """,
            index_release_id,
            data_release_id,
        )

        await conn.execute(
            """
            INSERT INTO index_manifest (
                index_release_id, data_release_id, chunk_strategy_version,
                embedding_model, embedding_dim, provider, source_table,
                total_chunks, embedded_chunks, skipped_chunks, error_count,
                quality_gate, notes, warnings
            )
            VALUES ($1, $2, $3, $4, $5, $6, 'knowledge_section',
                    $7, $8, $9, $10, $11, $12, $13::jsonb)
            ON CONFLICT (index_release_id) DO UPDATE
            SET data_release_id = EXCLUDED.data_release_id,
                chunk_strategy_version = EXCLUDED.chunk_strategy_version,
                embedding_model = EXCLUDED.embedding_model,
                embedding_dim = EXCLUDED.embedding_dim,
                provider = EXCLUDED.provider,
                built_at = NOW(),
                total_chunks = EXCLUDED.total_chunks,
                embedded_chunks = EXCLUDED.embedded_chunks,
                skipped_chunks = EXCLUDED.skipped_chunks,
                error_count = EXCLUDED.error_count,
                quality_gate = EXCLUDED.quality_gate,
                notes = EXCLUDED.notes,
                warnings = EXCLUDED.warnings
            """,
            index_release_id,
            data_release_id,
            chunk_strategy_version,
            stats.embedding_model,
            stats.embedding_dim,
            stats.provider,
            stats.total_chunks,
            stats.embedded,
            stats.skipped,
            stats.errors,
            "fail" if stats.errors else ("warn" if stats.skipped else "pass"),
            "Week8 index build completed",
            json.dumps(stats.warnings, ensure_ascii=False),
        )

        # 启用向量索引（首次构建后）
        await _ensure_vector_index(conn)

    stats.elapsed_sec = time.time() - t0
    logger.info(
        f"Index build complete: {stats.embedded} embedded, "
        f"{stats.errors} errors, {stats.elapsed_sec:.1f}s elapsed"
    )
    _write_report(stats, report_dir)
    return stats


def _write_report(stats: IndexStats, report_dir: str | Path) -> None:
    manifest = build_manifest(
        index_release_id=stats.index_release_id,
        data_release_id=stats.data_release_id,
        chunk_strategy_version=stats.chunk_strategy_version,
        embedding_model=stats.embedding_model,
        embedding_dim=stats.embedding_dim or EMBEDDING_DIM,
        provider=stats.provider,
        source_table="knowledge_section",
        total_chunks=stats.total_chunks,
        embedded_chunks=stats.embedded,
        skipped_chunks=stats.skipped,
        error_count=stats.errors,
        warnings=stats.warnings,
        elapsed_sec=stats.elapsed_sec,
    )
    md_path, json_path = write_index_build_outputs(manifest, report_dir)
    logger.info("Index reports written: %s %s", md_path, json_path)


async def _ensure_vector_index(conn):
    """确保 IVFFlat 向量索引存在（首次索引构建后创建）"""
    try:
        idx_exists = await conn.fetchval(
            "SELECT 1 FROM pg_indexes WHERE indexname = 'idx_ksection_embedding'"
        )
        if not idx_exists:
            logger.info("Creating IVFFlat vector index...")
            # lists 参数约为 chunk 总数的平方根（至少 1）
            count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_section WHERE embedding IS NOT NULL")
            lists = max(1, int(count ** 0.5))
            await conn.execute(
                f"""
                CREATE INDEX idx_ksection_embedding
                ON knowledge_section
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = {lists})
                """
            )
            logger.info(f"Vector index created (lists={lists})")
    except Exception as e:
        logger.warning(f"Could not create vector index: {e}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="pgvector Index Builder")
    parser.add_argument("--index-release-id", default="index-v0.1.0")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--doc-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--data-release-id", default=os.environ.get("WEEK08_DATA_RELEASE_ID", "data-week08-dev"))
    parser.add_argument("--chunk-strategy-version", default=os.environ.get("WEEK08_CHUNK_STRATEGY_VERSION", "section_aware_v1"))
    parser.add_argument("--report-dir", default=os.environ.get("WEEK08_REPORT_DIR", "reports/week08"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    stats = asyncio.run(
        build_index(
            args.index_release_id,
            args.batch_size,
            args.doc_id,
            args.dry_run,
            args.data_release_id,
            args.chunk_strategy_version,
            args.report_dir,
        )
    )
    sys.exit(1 if stats.errors > 0 else 0)


if __name__ == "__main__":
    main()
