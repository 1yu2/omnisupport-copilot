"""Context pruning for Week08 RAG generation.

The Week08 student core uses a deterministic top-k + token-budget strategy.
LongLLMLingua or model-based compression can be added later without changing
the RAG response contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass
class PrunedContext:
    chunks: list
    estimated_tokens: int
    dropped_chunk_ids: list[str]
    strategy: str = "top_k_token_budget"

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["chunks"] = [getattr(chunk, "chunk_id", None) for chunk in self.chunks]
        return payload


def estimate_tokens(text: str) -> int:
    # Conservative enough for classroom cost discussions; production should use
    # provider-specific tokenizers.
    return max(1, len(text) // 4)


def prune_contexts(
    chunks: Iterable,
    *,
    max_chunks: int = 5,
    token_budget: int = 2500,
) -> PrunedContext:
    selected = []
    dropped = []
    used_tokens = 0

    for chunk in list(chunks)[:max_chunks]:
        chunk_tokens = estimate_tokens(getattr(chunk, "content", ""))
        if selected and used_tokens + chunk_tokens > token_budget:
            dropped.append(getattr(chunk, "chunk_id", "unknown"))
            continue
        selected.append(chunk)
        used_tokens += chunk_tokens

    for chunk in list(chunks)[max_chunks:]:
        dropped.append(getattr(chunk, "chunk_id", "unknown"))

    return PrunedContext(
        chunks=selected,
        estimated_tokens=used_tokens,
        dropped_chunk_ids=dropped,
    )

