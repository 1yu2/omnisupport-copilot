"""Retrieval models used by Week8 debug responses."""

from __future__ import annotations

from pydantic import BaseModel


class RetrievalDebugItem(BaseModel):
    chunk_id: str
    vector_score: float | None = None
    fts_score: float | None = None
    rrf_score: float | None = None
    rerank_score: float | None = None
    final_score: float


class RetrievalDebug(BaseModel):
    mode: str
    rrf_k: int = 60
    rerank_enabled: bool
    rerank_fallback: bool
    filters_applied: dict[str, str | int | float | bool | None]
    results: list[RetrievalDebugItem]
