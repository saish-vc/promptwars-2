"""RAG (Retrieval-Augmented Generation) service for contract Q&A.

Context retrieval strategy (in priority order):
1. **Vector search** (when ``EMBEDDING_ENABLED=true`` and pgvector is available):
   Embed the question → cosine similarity search over ``document_chunks`` table →
   hybrid re-rank with BM25 keyword score → top 3 chunks returned.
2. **Keyword fallback** (when embeddings are disabled or unavailable):
   Exact token intersection scoring over in-memory text chunks (original behavior).
"""

from __future__ import annotations

import logging
import math
from collections import Counter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm import LEGAL_DISCLAIMER, llm_client
from app.services.json_utils import clean_llm_json
from app.core.config import settings

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = (
    LEGAL_DISCLAIMER
    + "\n\n"
    + "You are answering questions about a contract based on the provided context. "
    + "Return ONLY a single JSON object with these exact keys: "
    + "`answer`, `confidence`, and `sources`.\n\n"
    + "`answer`: your answer to the question based on the context.\n"
    + "`confidence`: a number between 0.0 and 1.0 indicating how confident you are "
    + "that the answer is based on the provided context. Use 0.0 if the context doesn't "
    + "contain the answer, 1.0 if it clearly does, and values in between for partial matches.\n"
    + "`sources`: a list of objects, each with `text` (the relevant snippet from the context) "
    + "and optionally `page` (page number if applicable).\n\n"
    + "If the context doesn't contain information to answer the question, state that clearly "
    + "and set confidence to 0.0 or near 0.0. Do not hallucinate or use outside knowledge."
)

RAG_PROMPT_PARTIAL = (
    "Question: {question}\n\n"
    "Contract context:\n\n{context}\n"
)


class MalformedRAGError(RuntimeError):
    pass


# ── Vector retrieval ──────────────────────────────────────────────────────────


async def _vector_retrieve_context(doc_id: str, question: str, top_k: int = 5) -> str | None:
    """Retrieve context via pgvector cosine similarity + BM25 hybrid re-ranking.

    Returns:
        Concatenated top-chunk text, or ``None`` if vector search is unavailable.
    """
    from app.services.embeddings import embedding_service

    question_vec = await embedding_service.embed(question)
    if question_vec is None:
        return None

    try:
        from sqlalchemy import select, text as sa_text
        from app.db.base import get_session
        from app.db.models import DocumentChunk

        async with get_session() as session:
            # pgvector cosine distance (<=> operator)
            result = await session.execute(
                sa_text(
                    "SELECT text, embedding <=> :vec AS distance "
                    "FROM document_chunks "
                    "WHERE doc_id = :doc_id AND embedding IS NOT NULL "
                    "ORDER BY distance ASC "
                    "LIMIT :k"
                ),
                {"vec": str(question_vec), "doc_id": doc_id, "k": top_k},
            )
            rows = result.fetchall()

        if not rows:
            logger.debug("pgvector: no embedded chunks found for doc_id=%s", doc_id)
            return None

        chunks = [row[0] for row in rows]
        distances = [row[1] for row in rows]

        # ── Hybrid re-rank: combine cosine score with BM25 keyword score ─────
        reranked = _hybrid_rerank(question, chunks, distances, top_n=3)
        context = "\n\n".join(reranked)
        logger.debug(
            "pgvector: retrieved %d chunks for doc_id=%s (hybrid reranked → %d)",
            len(chunks), doc_id, len(reranked),
        )
        return context

    except Exception as exc:
        logger.warning("Vector retrieval failed, falling back to keyword search: %s", exc)
        return None


def _hybrid_rerank(
    question: str,
    chunks: list[str],
    cosine_distances: list[float],
    top_n: int = 3,
    alpha: float = 0.6,
) -> list[str]:
    """Re-rank chunks by combining cosine similarity and BM25 keyword scores.

    Args:
        question:          The user question.
        chunks:            Text chunks (ordered by cosine distance ascending).
        cosine_distances:  Corresponding cosine distances (lower = more similar).
        top_n:             Number of top chunks to return.
        alpha:             Weight for cosine score (1-alpha for BM25).

    Returns:
        Top-N re-ranked chunk texts.
    """
    question_terms = question.lower().split()
    bm25_scores = [_bm25_score(question_terms, chunk, chunks) for chunk in chunks]

    # Normalise cosine similarity (invert distance so higher = better)
    cos_scores = [1.0 - d for d in cosine_distances]
    max_cos = max(cos_scores) or 1.0
    norm_cos = [s / max_cos for s in cos_scores]

    max_bm25 = max(bm25_scores) or 1.0
    norm_bm25 = [s / max_bm25 for s in bm25_scores]

    combined = [
        (alpha * nc + (1 - alpha) * nb, chunk)
        for nc, nb, chunk in zip(norm_cos, norm_bm25, chunks)
    ]
    combined.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in combined[:top_n]]


def _bm25_score(
    query_terms: list[str],
    chunk: str,
    corpus: list[str],
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Compute a single BM25 score for ``chunk`` against ``query_terms``.

    Uses corpus average length for IDF normalisation.
    """
    avg_len = sum(len(c.split()) for c in corpus) / max(len(corpus), 1)
    chunk_terms = chunk.lower().split()
    chunk_len = len(chunk_terms)
    tf_map = Counter(chunk_terms)

    total_docs = len(corpus)
    score = 0.0
    for term in query_terms:
        df = sum(1 for c in corpus if term in c.lower())
        if df == 0:
            continue
        idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1)
        tf = tf_map.get(term, 0)
        norm_tf = tf * (k1 + 1) / (tf + k1 * (1 - b + b * chunk_len / avg_len))
        score += idf * norm_tf
    return score


# ── Keyword retrieval (fallback) ──────────────────────────────────────────────


def _keyword_retrieve_context(question: str, text: str) -> str:
    """Original keyword-intersection-based context retrieval (fallback).

    Preserved exactly from the original implementation for backward compatibility.
    """
    chunks = _chunk_text_simple(text)
    question_words = set(question.lower().split())
    scored_chunks = [
        (chunk, len(question_words & set(chunk.lower().split())))
        for chunk in chunks
    ]
    scored_chunks = [(c, s) for c, s in scored_chunks if s > 0]
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    top_chunks = [chunk for chunk, _ in scored_chunks[:3]]
    return "\n\n".join(top_chunks) if top_chunks else text[:2000]


def _chunk_text_simple(text: str, chunk_size: int = 500) -> list[str]:
    return [
        text[i : i + chunk_size]
        for i in range(0, len(text), chunk_size)
        if text[i : i + chunk_size].strip()
    ]


# ── RAG service ───────────────────────────────────────────────────────────────


class RAGService:
    async def chat(self, request: ChatRequest, resolve_text) -> ChatResponse:
        """Run the full RAG pipeline: retrieve context → call LLM → parse response."""
        text = resolve_text(request.doc_id) if callable(resolve_text) else None

        # Try async resolve first (production store)
        if text is None:
            try:
                from app.services.documents import get_async_store
                text = await get_async_store().get_text(request.doc_id)
            except Exception:
                pass

        # Sync resolve (fallback store)
        if text is None and callable(resolve_text):
            text = resolve_text(request.doc_id)

        if not text:
            raise ValueError("Document not found")

        # ── Context retrieval ─────────────────────────────────
        context: str | None = None

        if settings.embedding_active:
            context = await _vector_retrieve_context(
                doc_id=request.doc_id, question=request.question
            )

        if context is None:
            # Fallback: keyword matching
            context = _keyword_retrieve_context(request.question, text)
            logger.debug("Using keyword context retrieval for doc_id=%s", request.doc_id)
        else:
            logger.debug("Using vector context retrieval for doc_id=%s", request.doc_id)

        prompt = RAG_SYSTEM_PROMPT + "\n\n" + RAG_PROMPT_PARTIAL.format(
            question=request.question, context=context
        )
        raw = await llm_client.complete(prompt, system_prompt="")
        return self._parse(raw, context)

    def _parse(self, raw: str, context: str) -> ChatResponse:
        candidate = clean_llm_json(raw)
        if candidate is None:
            raise MalformedRAGError("No JSON object found in the LLM response")
        try:
            parsed = ChatResponse.model_validate_json(candidate)
        except Exception as exc:
            raise MalformedRAGError(
                f"LLM response did not match the expected chat schema: {exc}"
            ) from exc
        if parsed.sources:
            parsed.sources = [s for s in parsed.sources if s.text in context or len(s.text) < 200]
        return parsed


async def chat_about_contract(
    request: ChatRequest,
    resolve_text,
    service: RAGService | None = None,
) -> ChatResponse:
    service = service or RAGService()
    try:
        return await service.chat(request, resolve_text)
    except MalformedRAGError:
        logger.warning("First chat generation failed, retrying once")
        try:
            return await service.chat(request, resolve_text)
        except MalformedRAGError as exc:
            logger.error("Chat generation retry failed: %s", exc)
            raise RuntimeError("Chat generation failed after retry") from exc