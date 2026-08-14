from __future__ import annotations

from typing import Any

from ai_os.intelligence.context import IntelligenceContext
from ai_os.intelligence.intelligence import Intelligence
from ai_os.intelligence.integration import IntelligenceOrchestrator
from ai_os.runtime.cancellation import CancellationToken


class IntegratedIntelligence:
    """9.1 Intelligence implementation backed by the 9.4 pipeline."""

    def __init__(
        self,
        orchestrator: IntelligenceOrchestrator,
    ) -> None:
        if not isinstance(
            orchestrator,
            IntelligenceOrchestrator,
        ):
            raise TypeError(
                "orchestrator must be an IntelligenceOrchestrator"
            )

        self._orchestrator = orchestrator

    def decide(
        self,
        input: Any,
        cancellation_token: CancellationToken | None = None,
    ) -> Any:
        if isinstance(
            input,
            IntelligenceContext,
        ):
            context = input
        else:
            context = IntelligenceContext(
                input=input,
            )

        return self._orchestrator.run(
            context=context,
            intent_id="intent:integration",
            decision_id="decision:integration",
            cancellation_token=cancellation_token,
        )