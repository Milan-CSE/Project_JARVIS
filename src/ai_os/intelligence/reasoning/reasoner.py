from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ai_os.intelligence.context import IntelligenceContext
from ai_os.runtime.cancellation import CancellationToken


@runtime_checkable
class Reasoner(Protocol):
    """Contract for one logical reasoning operation."""

    def reason(
        self,
        context: IntelligenceContext,
        cancellation_token: CancellationToken | None = None,
    ) -> Any:
        ...