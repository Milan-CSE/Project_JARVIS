from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from ai_os.intelligence.decision import Decision
from ai_os.intelligence.intent import Intent
from ai_os.runtime.cancellation import CancellationToken


@runtime_checkable
class DecisionGeneratorContract(Protocol):
    """9.5.3 contract for Intent → Decision generation."""

    def generate(
        self,
        intent: Intent,
        decision_id: str,
        cancellation_token: CancellationToken | None = None,
    ) -> Decision:
        ...


class IntentDecisionStatus(str, Enum):
    RESOLVED = "resolved"


@dataclass(frozen=True, slots=True)
class IntentDecisionResult:
    """Immutable result of the 9.5.3 Intent → Decision pipeline."""

    status: IntentDecisionStatus
    intent: Intent
    decision: Decision
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            IntentDecisionStatus,
        ):
            object.__setattr__(
                self,
                "status",
                IntentDecisionStatus(self.status),
            )

        if not isinstance(
            self.intent,
            Intent,
        ):
            raise TypeError(
                "intent must be an Intent"
            )

        if not isinstance(
            self.decision,
            Decision,
        ):
            raise TypeError(
                "decision must be a Decision"
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


class IntentDecisionPipeline:
    """
    9.5.3 pipeline:

        Intent
          ↓
        DecisionGeneratorContract
          ↓
        Decision
          ↓
        IntentDecisionResult

    This stage intentionally stops at Decision.
    """

    def __init__(
        self,
        decision_generator: DecisionGeneratorContract,
    ) -> None:
        if not isinstance(
            decision_generator,
            DecisionGeneratorContract,
        ):
            raise TypeError(
                "decision_generator must implement "
                "DecisionGeneratorContract"
            )

        self._decision_generator = decision_generator

    def run(
        self,
        intent: Intent,
        decision_id: str,
        cancellation_token: CancellationToken | None = None,
    ) -> IntentDecisionResult:
        # ---------------------------------------------------------------
        # Input validation
        # ---------------------------------------------------------------

        if not isinstance(
            intent,
            Intent,
        ):
            raise TypeError(
                "intent must be an Intent"
            )

        if not isinstance(
            decision_id,
            str,
        ):
            raise TypeError(
                "decision_id must be a string"
            )

        if not decision_id.strip():
            raise ValueError(
                "decision_id must not be empty or whitespace"
            )

        # ---------------------------------------------------------------
        # Intent → Decision
        # ---------------------------------------------------------------

        decision = self._decision_generator.generate(
            intent,
            decision_id,
            cancellation_token,
        )

        # ---------------------------------------------------------------
        # Semantic boundary validation
        # ---------------------------------------------------------------

        if not isinstance(
            decision,
            Decision,
        ):
            raise TypeError(
                "decision_generator must return a Decision"
            )

        # ---------------------------------------------------------------
        # Completed 9.5.3
        # ---------------------------------------------------------------

        return IntentDecisionResult(
            status=IntentDecisionStatus.RESOLVED,
            intent=intent,
            decision=decision,
            metadata={
                "stage": "intent_to_decision",
            },
        )