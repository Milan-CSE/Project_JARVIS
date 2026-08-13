from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from ai_os.cognition.context import InformationItem


@runtime_checkable
class MemoryStore(Protocol):
    """Contract for retained information storage."""

    def query(
        self,
        query: str,
        *,
        limit: int = 10,
        filters: Mapping[str, Any] | None = None,
    ) -> Sequence[InformationItem]:
        ...

    def retain(
        self,
        item: InformationItem,
    ) -> None:
        ...