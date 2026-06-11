"""PPT-compatible hybrid retrieval entrypoints for Week08.

Do not add retrieval logic here. The service runtime owns the implementation in
`services/rag_api/app/retrieval.py`; this module keeps the course deck path
stable without creating a second retrieval stack.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAG_API_PATH = PROJECT_ROOT / "services" / "rag_api"
if str(RAG_API_PATH) not in sys.path:
    sys.path.insert(0, str(RAG_API_PATH))

from app.retrieval import (  # noqa: E402
    RetrievalResult,
    fts_search,
    hybrid_retrieve,
    reciprocal_rank_fusion,
    vector_search,
)


hybrid_search = hybrid_retrieve

__all__ = [
    "RetrievalResult",
    "fts_search",
    "hybrid_retrieve",
    "hybrid_search",
    "reciprocal_rank_fusion",
    "vector_search",
]

