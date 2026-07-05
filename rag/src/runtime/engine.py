"""RAG engine orchestration entry point."""

import logging

from contracts.rag.models import TutorResponse
from contracts.rag.interfaces import IRagEngine
from ..shared.interfaces.model_client import IModelClient
from ..shared.interfaces.vector_store import IVectorStore
from ..shared.chroma_vector_store import ChromaVectorStore
from ..shared.call_model import OpenRouterClient
from .generator import generate
from .guardrails import apply_input_guardrails, apply_output_guardrail
from .retrieval import retrieve

logger = logging.getLogger(__name__)


class RagEngine(IRagEngine):

    def __init__(
        self,
        store: IVectorStore | None = None,
        model_client: IModelClient | None = None,
    ) -> None:
        self._store = store or ChromaVectorStore()
        self._model_client = model_client or OpenRouterClient()

    def ask(
        self,
        course: str,
        query: str,
        summary: str = "",
        history: list[dict] | None = None,
        memory: str = "",
        course_scope: str = "",
    ) -> TutorResponse:
        """Run guardrails, retrieval, generation, and output guardrails."""
        query, blocked = apply_input_guardrails(query)
        if blocked is not None:
            return blocked

        results = retrieve(course, query, store=self._store)

        response = generate(
            query,
            results,
            summary,
            history,
            is_retrieval_fallback=results.is_empty(),
            memory=memory,
            course_scope=course_scope,
            model_client=self._model_client,
        )

        return apply_output_guardrail(response)

    def preload_models(self) -> None:
        from ..shared.config import RERANKER_MODEL
        from ..shared.embedding import get_embedder
        from .reranker import get_reranker
        get_embedder()
        if RERANKER_MODEL:
            get_reranker(RERANKER_MODEL)
        else:
            logger.info("Reranker disabled; skipping reranker preload.")

def get_engine() -> IRagEngine:
    return RagEngine()
