from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from ai_os.cognition.context import InformationItem


@runtime_checkable
class Retriever(Protocol):
    """Contract for finding relevant information."""

    def query(
        self,
        query: str,
        *,
        limit: int = 10,
        filters: Mapping[str, Any] | None = None,
    ) -> Sequence[InformationItem]:
        ...