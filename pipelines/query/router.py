"""Adaptive RAG routing helper for Week08 classroom use."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from pipelines.query.rewriter import extract_lexical_terms


@dataclass
class QueryRoute:
    mode: str
    use_hybrid: bool
    use_rewrite: bool
    use_hyde: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def route_query(query: str) -> QueryRoute:
    lexical_terms = extract_lexical_terms(query)
    query_len = len(query.split())
    if lexical_terms:
        return QueryRoute(
            mode="hybrid_lexical_guard",
            use_hybrid=True,
            use_rewrite=True,
            use_hyde=False,
            reason="query_contains_error_code_or_identifier",
        )
    if query_len <= 3:
        return QueryRoute(
            mode="hybrid_short_query",
            use_hybrid=True,
            use_rewrite=True,
            use_hyde=True,
            reason="short_query_needs_expansion",
        )
    return QueryRoute(
        mode="hybrid_default",
        use_hybrid=True,
        use_rewrite=False,
        use_hyde=False,
        reason="standard_semantic_and_lexical_retrieval",
    )

