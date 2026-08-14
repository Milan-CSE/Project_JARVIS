from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.intelligence.context import IntelligenceContext
from ai_os.intelligence.orchestration_models import (
    IntelligenceOrchestrationResult,
)
from ai_os.runtime.cancellation import CancellationToken


@runtime_checkable
class IntelligenceOrchestrator(Protocol):
    """Contract for the complete Intelligence orchestration lifecycle."""

    def orchestrate(
        self,
        context: IntelligenceContext,
        cancellation_token: CancellationToken | None = None,
    ) -> IntelligenceOrchestrationResult:
        ...