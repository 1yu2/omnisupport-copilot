"""Week8 contract-first RAG endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request

from app.audit import Timer, write_rag_audit_log
from app.config import settings
from app.generator import generate_grounded_answer
from app.models.rag_models import (
    Citation,
    RagAnswerRequest,
    RagAnswerResponse,
    RetrievalContext,
    RetrievalDebugItem,
    RetrievalDebugPayload,
)
from app.routers.query import _get_pool

router = APIRouter(tags=["week08-rag"])


@router.post("/rag/answer", response_model=RagAnswerResponse, summary="Week8 RAG answer")
async def rag_answer(payload: RagAnswerRequest, http_request: Request) -> RagAnswerResponse:
    timer = Timer()
    trace_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    index_release_id = payload.index_release_id or settings.index_release_id
    data_release_id = payload.data_release_id or settings.data_release_id
    prompt_release_id = payload.prompt_release_id or settings.prompt_release_id
    filters = {
        "product_line": payload.product_line,
        "visibility_scope": payload.visibility_scope,
        "entitlement_tier": payload.entitlement_tier,
        "status": payload.status,
        "quality_status": payload.quality_status,
        "data_release_id": data_release_id,
        "index_release_id": index_release_id,
    }

    raw_chunks = []
    pool = None
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            from app.retrieval import hybrid_retrieve

            raw_chunks = await hybrid_retrieve(
                conn=conn,
                query=payload.question,
                top_k=payload.top_k,
                product_line=payload.product_line,
                index_release_id=index_release_id,
                data_release_id=data_release_id,
                visibility_scope=payload.visibility_scope,
                entitlement_tier=payload.entitlement_tier,
                status=payload.status,
                quality_status=payload.quality_status,
                rerank=settings.rerank_enabled,
            )
    except Exception:
        raw_chunks = []

    citations = [_citation_from_chunk(chunk) for chunk in raw_chunks]
    answer, confidence, abstain_reason = await generate_grounded_answer(
        question=payload.question,
        chunks=raw_chunks,
        prompt_release_id=prompt_release_id,
    )
    if not raw_chunks and abstain_reason is None:
        abstain_reason = "no_retrieval_results"

    retrieved_contexts = [
        RetrievalContext(
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            score=chunk.final_score,
            citation=citation,
        )
        for chunk, citation in zip(raw_chunks, citations)
    ]
    debug = _debug_payload(raw_chunks, filters) if payload.include_debug else None

    if pool is not None:
        try:
            async with pool.acquire() as conn:
                await write_rag_audit_log(
                    conn=conn,
                    request_id=trace_id,
                    trace_id=trace_id,
                    question=payload.question,
                    actor_role=payload.actor_role,
                    filters=filters,
                    retrieved_evidence_ids=[c.evidence_id for c in citations],
                    scores=[chunk.debug_scores() for chunk in raw_chunks],
                    answer=answer,
                    confidence=confidence,
                    abstain_reason=abstain_reason,
                    release_id=settings.release_id,
                    data_release_id=data_release_id,
                    index_release_id=index_release_id,
                    prompt_release_id=prompt_release_id,
                    latency_ms=timer.elapsed_ms,
                )
        except Exception:
            pass

    return RagAnswerResponse(
        answer=answer,
        citations=citations,
        evidence_ids=[c.evidence_id for c in citations],
        confidence=confidence,
        abstain_reason=abstain_reason,
        release_id=settings.release_id,
        data_release_id=data_release_id,
        index_release_id=index_release_id,
        prompt_release_id=prompt_release_id,
        trace_id=trace_id,
        retrieved_contexts=retrieved_contexts,
        retrieval_debug=debug,
    )


def _citation_from_chunk(chunk) -> Citation:
    return Citation(
        evidence_id=chunk.evidence_id,
        chunk_id=chunk.chunk_id,
        section_id=chunk.chunk_id,
        doc_id=chunk.doc_id,
        source_id=chunk.source_id,
        title=chunk.title,
        page_no=chunk.page_no,
        section_path=chunk.section_path,
        bbox=chunk.bbox,
        source_url=chunk.source_url,
        doc_version=chunk.doc_version,
        quote=chunk.content[:500],
        score=chunk.final_score,
    )


def _debug_payload(chunks, filters: dict) -> RetrievalDebugPayload:
    has_rerank = any(chunk.rerank_score is not None for chunk in chunks)
    return RetrievalDebugPayload(
        mode="hybrid_rrf_rerank" if has_rerank else "hybrid_rrf",
        rrf_k=60,
        rerank_enabled=settings.rerank_enabled,
        rerank_fallback=settings.rerank_enabled and not has_rerank,
        filters_applied={key: value for key, value in filters.items() if value is not None},
        results=[
            RetrievalDebugItem(
                chunk_id=chunk.chunk_id,
                vector_score=chunk.vector_score,
                fts_score=chunk.fts_score,
                rrf_score=chunk.rrf_score,
                rerank_score=chunk.rerank_score,
                final_score=chunk.final_score,
            )
            for chunk in chunks
        ],
    )
