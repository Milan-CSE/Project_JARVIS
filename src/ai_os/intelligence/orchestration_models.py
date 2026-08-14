from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from ai_os.intelligence.context import IntelligenceContext
from ai_os.intelligence.decision import (
    Decision,
    Proposal,
)
from ai_os.intelligence.intent import Intent
from ai_os.runtime.agents import AgentDecision


class IntelligenceOrchestrationStatus(str, Enum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class IntelligenceOrchestrationResult:
    """Immutable result of the complete Intelligence lifecycle."""

    status: IntelligenceOrchestrationStatus
    context: IntelligenceContext
    intent: Intent | None = None
    decision: Decision | None = None
    proposal: Proposal | None = None
    agent_decision: AgentDecision | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            IntelligenceOrchestrationStatus,
        ):
            object.__setattr__(
                self,
                "status",
                IntelligenceOrchestrationStatus(self.status),
            )

        if not isinstance(
            self.context,
            IntelligenceContext,
        ):
            raise TypeError(
                "context must be an IntelligenceContext"
            )

        if self.intent is not None and not isinstance(
            self.intent,
            Intent,
        ):
            raise TypeError(
                "intent must be an Intent or None"
            )

        if self.decision is not None and not isinstance(
            self.decision,
            Decision,
        ):
            raise TypeError(
                "decision must be a Decision or None"
            )

        if self.proposal is not None and not isinstance(
            self.proposal,
            Proposal,
        ):
            raise TypeError(
                "proposal must be a Proposal or None"
            )

        if self.agent_decision is not None and not isinstance(
            self.agent_decision,
            AgentDecision,
        ):
            raise TypeError(
                "agent_decision must be an "
                "AgentDecision or None"
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