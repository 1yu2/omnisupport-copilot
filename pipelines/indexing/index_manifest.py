"""Week8 index manifest helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass
class IndexManifest:
    index_release_id: str
    data_release_id: str
    chunk_strategy_version: str
    embedding_model: str
    embedding_dim: int
    provider: str
    built_at: str
    source_table: str
    total_chunks: int
    embedded_chunks: int
    skipped_chunks: int
    error_count: int
    quality_gate: str
    notes: str
    warnings: list[str] = field(default_factory=list)
    elapsed_sec: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def quality_gate_for(total_chunks: int, embedded_chunks: int, error_count: int) -> str:
    if error_count > 0:
        return "fail"
    if total_chunks == 0 or embedded_chunks < total_chunks:
        return "warn"
    return "pass"


def build_manifest(
    *,
    index_release_id: str,
    data_release_id: str,
    chunk_strategy_version: str,
    embedding_model: str,
    embedding_dim: int,
    provider: str,
    source_table: str,
    total_chunks: int,
    embedded_chunks: int,
    skipped_chunks: int,
    error_count: int,
    warnings: list[str],
    elapsed_sec: float | None,
) -> IndexManifest:
    gate = quality_gate_for(total_chunks, embedded_chunks, error_count)
    notes = "Week8 index build completed."
    if skipped_chunks:
        notes = f"Week8 index build completed with {skipped_chunks} skipped chunks."
    if error_count:
        notes = f"Week8 index build failed with {error_count} errors."

    return IndexManifest(
        index_release_id=index_release_id,
        data_release_id=data_release_id,
        chunk_strategy_version=chunk_strategy_version,
        embedding_model=embedding_model,
        embedding_dim=embedding_dim,
        provider=provider,
        built_at=datetime.now(timezone.utc).isoformat(),
        source_table=source_table,
        total_chunks=total_chunks,
        embedded_chunks=embedded_chunks,
        skipped_chunks=skipped_chunks,
        error_count=error_count,
        quality_gate=gate,
        notes=notes,
        warnings=warnings,
        elapsed_sec=elapsed_sec,
    )
