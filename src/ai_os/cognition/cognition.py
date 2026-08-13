from __future__ import annotations

from ai_os.cognition.context import Context, ContextRequest
from ai_os.cognition.retrieval import Retriever


class Cognition:
    """
    Coordinates information retrieval and assembles Context.

    Cognition supplies information to Intelligence.
    It does not perform reasoning or execute actions.
    """

    def __init__(self, retriever: Retriever) -> None:
        if not isinstance(retriever, Retriever):
            raise TypeError("retriever must implement Retriever")

        self._retriever = retriever

    def get_context(self, request: ContextRequest) -> Context:
        if not isinstance(request, ContextRequest):
            raise TypeError("request must be a ContextRequest")

        items = self._retriever.query(
            request.query,
            limit=request.max_items,
            filters=request.filters,
        )

        return Context(
            query=request.query,
            items=tuple(items),
            metadata=request.metadata,
        )