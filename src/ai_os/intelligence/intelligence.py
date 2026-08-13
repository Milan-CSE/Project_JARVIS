from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ai_os.runtime.cancellation import CancellationToken


@runtime_checkable
class Intelligence(Protocol):
    """Contract for one logical Intelligence decision."""

    def decide(
        self,
        input: Any,
        cancellation_token: CancellationToken | None = None,
    ) -> Any:
        ...