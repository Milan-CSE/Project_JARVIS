from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from ai_os.intelligence.decision import (
    Decision,
    DecisionAdapter,
    Proposal,
)
from ai_os.intelligence.intent import Intent
from ai_os.intelligence.semantic_validation import (
    SemanticValidationResult,
    SemanticValidationStatus,
)
from ai_os.runtime.agents import AgentDecision


@runtime_checkable
class DecisionAdapterContract(Protocol):
    """9.5.6 contract for semantic → AgentDecision translation."""

    def to_agent_decision(
        self,
        intent: Intent,
        decision: Decision,
        proposal: Proposal | None,
    ) -> AgentDecision:
        ...


class AgentDecisionHandoffStatus(str, Enum):
    HANDED_OFF = "handed_off"


@dataclass(frozen=True, slots=True)
class AgentDecisionHandoffResult:
    """Immutable result of the 9.5.6 AgentDecision handoff."""

    status: AgentDecisionHandoffStatus
    intent: Intent
    decision: Decision
    proposal: Proposal | None
    validation: SemanticValidationResult
    agent_decision: AgentDecision
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            AgentDecisionHandoffStatus,
        ):
            object.__setattr__(
                self,
                "status",
                AgentDecisionHandoffStatus(self.status),
            )

        if not isinstance(self.intent, Intent):
            raise TypeError(
                "intent must be an Intent"
            )

        if not isinstance(self.decision, Decision):
            raise TypeError(
                "decision must be a Decision"
            )

        if self.proposal is not None and not isinstance(
            self.proposal,
            Proposal,
        ):
            raise TypeError(
                "proposal must be a Proposal or None"
            )

        if not isinstance(
            self.validation,
            SemanticValidationResult,
        ):
            raise TypeError(
                "validation must be a SemanticValidationResult"
            )

        if not isinstance(
            self.agent_decision,
            AgentDecision,
        ):
            raise TypeError(
                "agent_decision must be an AgentDecision"
            )

        if self.validation.status is not SemanticValidationStatus.VALID:
            raise ValueError(
                "AgentDecisionHandoffResult requires "
                "a VALID semantic validation result"
            )

        if self.validation.intent is not self.intent:
            raise ValueError(
                "validation intent does not match result intent"
            )

        if self.validation.decision is not self.decision:
            raise ValueError(
                "validation decision does not match result decision"
            )

        if self.validation.proposal is not self.proposal:
            raise ValueError(
                "validation proposal does not match result proposal"
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
            MappingProxyType(dict(self.metadata)),
        )


class AgentDecisionHandoffPipeline:
    """
    9.5.6 pipeline:

        SemanticValidationResult
                 ↓
        DecisionAdapterContract
                 ↓
            AgentDecision
    """

    def __init__(
        self,
        adapter: DecisionAdapterContract,
    ) -> None:
        if not isinstance(
            adapter,
            DecisionAdapterContract,
        ):
            raise TypeError(
                "adapter must implement "
                "DecisionAdapterContract"
            )

        self._adapter = adapter

    def run(
        self,
        validated: SemanticValidationResult,
    ) -> AgentDecisionHandoffResult:
        if not isinstance(
            validated,
            SemanticValidationResult,
        ):
            raise TypeError(
                "validated must be a SemanticValidationResult"
            )

        if (
            validated.status
            is not SemanticValidationStatus.VALID
        ):
            raise ValueError(
                "cannot hand off rejected semantic validation"
            )

        agent_decision = self._adapter.to_agent_decision(
            validated.intent,
            validated.decision,
            validated.proposal,
        )

        if not isinstance(
            agent_decision,
            AgentDecision,
        ):
            raise TypeError(
                "adapter must return an AgentDecision"
            )

        return AgentDecisionHandoffResult(
            status=AgentDecisionHandoffStatus.HANDED_OFF,
            intent=validated.intent,
            decision=validated.decision,
            proposal=validated.proposal,
            validation=validated,
            agent_decision=agent_decision,
            metadata={
                "stage": "agent_decision_handoff",
            },
        )