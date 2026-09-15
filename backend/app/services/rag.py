import logging

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm import LEGAL_DISCLAIMER, llm_client
from app.services.analysis import _clean_json_candidate, _first_json_object

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


class RAGService:
    async def chat(self, request: ChatRequest, resolve_text) -> ChatResponse:
        text = resolve_text(request.doc_id)
        if not text:
            raise ValueError("Document not found")

        context = self._retrieve_context(request.question, text)
        prompt = RAG_SYSTEM_PROMPT + "\n\n" + RAG_PROMPT_PARTIAL.format(
            question=request.question, context=context
        )
        raw = await llm_client.complete(prompt, system_prompt="")
        return self._parse(raw, context)

    def _retrieve_context(self, question: str, text: str) -> str:
        chunks = self._chunk_text(text)
        question_words = set(question.lower().split())
        scored_chunks = [
            (chunk, len(question_words & set(chunk.lower().split())))
            for chunk in chunks
        ]
        scored_chunks = [(c, s) for c, s in scored_chunks if s > 0]
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = [chunk for chunk, _ in scored_chunks[:3]]
        return "\n\n".join(top_chunks) if top_chunks else text[:2000]

    def _chunk_text(self, text: str, chunk_size: int = 500) -> list[str]:
        return [
            text[i: i + chunk_size]
            for i in range(0, len(text), chunk_size)
            if text[i: i + chunk_size].strip()
        ]

    def _parse(self, raw: str, context: str) -> ChatResponse:
        candidate = _first_json_object(_clean_json_candidate(raw))
        if candidate is None:
            raise MalformedRAGError("No JSON object found in the LLM response")
        try:
            parsed = ChatResponse.model_validate_json(candidate)
        except Exception as exc:
            raise MalformedRAGError("LLM response did not match the expected chat schema") from exc
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