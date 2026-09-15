import logging
from typing import List, Tuple

from app.schemas.chat import ChatRequest, ChatResponse, SourceSnippet
from app.services.llm import LEGAL_DISCLAIMER, llm_client

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


class RAGService:
    def __init__(self):
        # For a minimal implementation, we'll use a simple text-based approach
        # In production, this would use embeddings and a vector DB
        pass

    async def chat(self, request: ChatRequest, resolve_text) -> ChatResponse:
        # Get the document text
        text = resolve_text(request.doc_id)
        if not text:
            raise ValueError("Document not found")

        # Simple keyword-based context retrieval (replace with vector search in production)
        context = self._retrieve_context(request.question, text)

        # Generate answer using LLM
        prompt = RAG_SYSTEM_PROMPT + "\n\n" + RAG_PROMPT_PARTIAL.format(
            question=request.question, context=context
        )
        raw = await llm_client.complete(prompt, system_prompt="")
        return self._parse(raw, context)

    def _retrieve_context(self, question: str, text: str) -> str:
        """Simple keyword-based context retrieval (placeholder for vector search)"""
        # Split text into chunks
        chunks = self._chunk_text(text)
        
        # Score chunks based on keyword overlap with question
        question_words = set(question.lower().split())
        scored_chunks = []
        
        for chunk in chunks:
            chunk_words = set(chunk.lower().split())
            overlap = len(question_words & chunk_words)
            if overlap > 0:
                scored_chunks.append((chunk, overlap))
        
        # Sort by overlap score and take top chunks
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = [chunk for chunk, score in scored_chunks[:3]]
        
        return "\n\n".join(top_chunks) if top_chunks else text[:2000]

    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks for processing"""
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    def _parse(self, raw: str, context: str) -> ChatResponse:
        from app.services.analysis import _first_json_object, _clean_json_candidate

        candidate = _first_json_object(_clean_json_candidate(raw))
        if candidate is None:
            raise MalformedRAGError("No JSON object found in the LLM response")
        try:
            parsed = ChatResponse.model_validate_json(candidate)
        except Exception as exc:
            raise MalformedRAGError("LLM response did not match the expected chat schema") from exc
        
        # Ensure sources are actually from the context
        if parsed.sources:
            valid_sources = []
            for source in parsed.sources:
                if source.text in context or len(source.text) < 200:  # Allow short matches
                    valid_sources.append(source)
            parsed.sources = valid_sources
        
        return parsed


class MalformedRAGError(RuntimeError):
    pass


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