from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.intelligence.context import IntelligenceContext
from ai_os.intelligence.decision import Proposal
from ai_os.intelligence.failure import (
    IntelligenceFailureBoundary,
    IntelligenceOperationStatus,
)
from ai_os.intelligence.intent import Intent
from ai_os.intelligence.intent_decision import (
    IntentDecisionPipeline,
    IntentDecisionResult,
)
from ai_os.intelligence.decision_proposal import (
    DecisionProposalPipeline,
    DecisionProposalResult,
    DecisionProposalStatus,
)
from ai_os.intelligence.reasoning_intent import (
    ReasoningIntentPipeline,
    ReasoningIntentResult,
    ReasoningIntentStatus,
)
from ai_os.intelligence.semantic_validation import (
    SemanticValidationPipeline,
    SemanticValidationResult,
    SemanticValidationStatus,
)
from ai_os.intelligence.agent_handoff import (
    AgentDecisionHandoffPipeline,
    AgentDecisionHandoffResult,
)
from ai_os.intelligence.orchestration import (
    IntelligenceOrchestrator,
)
from ai_os.intelligence.orchestration_models import (
    IntelligenceOrchestrationResult,
    IntelligenceOrchestrationStatus,
)
from ai_os.runtime.cancellation import CancellationToken


@runtime_checkable
class ReasoningIntentStageContract(Protocol):
    def run(
        self,
        context: IntelligenceContext,
        intent_id: str,
        candidate_index: int | None = None,
        cancellation_token: CancellationToken | None = None,
    ) -> ReasoningIntentResult:
        ...


@runtime_checkable
class IntentDecisionStageContract(Protocol):
    def run(
        self,
        intent: Intent,
        decision_id: str,
        cancellation_token: CancellationToken | None = None,
    ) -> IntentDecisionResult:
        ...


@runtime_checkable
class DecisionProposalStageContract(Protocol):
    def run(
        self,
        decision,
        proposal_id: str,
    ) -> DecisionProposalResult:
        ...


@runtime_checkable
class SemanticValidationStageContract(Protocol):
    def run(
        self,
        intent,
        decision,
        proposal: Proposal | None,
    ) -> SemanticValidationResult:
        ...


@runtime_checkable
class AgentDecisionHandoffStageContract(Protocol):
    def run(
        self,
        validated: SemanticValidationResult,
    ) -> AgentDecisionHandoffResult:
        ...


class DefaultIntelligenceOrchestrator:
    """
    9.5.8 complete Intelligence orchestration.

    This class composes the already-locked 9.5 stages.
    It owns sequencing and operational outcome normalization,
    but not the semantics of individual stages.
    """

    def __init__(
        self,
        reasoning_intent: ReasoningIntentStageContract,
        intent_decision: IntentDecisionStageContract,
        decision_proposal: DecisionProposalStageContract,
        semantic_validation: SemanticValidationStageContract,
        agent_handoff: AgentDecisionHandoffStageContract,
        *,
        intent_id: str,
        decision_id: str,
        proposal_id: str,
        candidate_index: int | None = None,
        failure_boundary: IntelligenceFailureBoundary | None = None,
    ) -> None:
        if not isinstance(
            reasoning_intent,
            ReasoningIntentStageContract,
        ):
            raise TypeError(
                "reasoning_intent must implement "
                "ReasoningIntentStageContract"
            )

        if not isinstance(
            intent_decision,
            IntentDecisionStageContract,
        ):
            raise TypeError(
                "intent_decision must implement "
                "IntentDecisionStageContract"
            )

        if not isinstance(
            decision_proposal,
            DecisionProposalStageContract,
        ):
            raise TypeError(
                "decision_proposal must implement "
                "DecisionProposalStageContract"
            )

        if not isinstance(
            semantic_validation,
            SemanticValidationStageContract,
        ):
            raise TypeError(
                "semantic_validation must implement "
                "SemanticValidationStageContract"
            )

        if not isinstance(
            agent_handoff,
            AgentDecisionHandoffStageContract,
        ):
            raise TypeError(
                "agent_handoff must implement "
                "AgentDecisionHandoffStageContract"
            )

        for name, value in (
            ("intent_id", intent_id),
            ("decision_id", decision_id),
            ("proposal_id", proposal_id),
        ):
            if not isinstance(value, str):
                raise TypeError(
                    f"{name} must be a string"
                )

            if not value.strip():
                raise ValueError(
                    f"{name} must not be empty or whitespace"
                )

        if candidate_index is not None:
            if (
                isinstance(candidate_index, bool)
                or not isinstance(candidate_index, int)
            ):
                raise TypeError(
                    "candidate_index must be an int or None"
                )

        if failure_boundary is not None and not isinstance(
            failure_boundary,
            IntelligenceFailureBoundary,
        ):
            raise TypeError(
                "failure_boundary must be an "
                "IntelligenceFailureBoundary or None"
            )

        self._reasoning_intent = reasoning_intent
        self._intent_decision = intent_decision
        self._decision_proposal = decision_proposal
        self._semantic_validation = semantic_validation
        self._agent_handoff = agent_handoff

        self._intent_id = intent_id
        self._decision_id = decision_id
        self._proposal_id = proposal_id
        self._candidate_index = candidate_index

        self._failure_boundary = (
            failure_boundary
            if failure_boundary is not None
            else IntelligenceFailureBoundary()
        )

    def orchestrate(
        self,
        context: IntelligenceContext,
        cancellation_token: CancellationToken | None = None,
    ) -> IntelligenceOrchestrationResult:
        if not isinstance(
            context,
            IntelligenceContext,
        ):
            raise TypeError(
                "context must be an IntelligenceContext"
            )

        intent = None
        decision = None
        proposal = None
        agent_decision = None
        metadata = {}

        # ---------------------------------------------------------------
        # 9.5.2 Reasoning → Intent
        # ---------------------------------------------------------------

        reasoning_operation = self._failure_boundary.run(
            lambda: self._reasoning_intent.run(
                context,
                self._intent_id,
                candidate_index=self._candidate_index,
                cancellation_token=cancellation_token,
            ),
            cancellation_token,
        )

        if reasoning_operation.status is IntelligenceOperationStatus.CANCELLED:
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.CANCELLED,
                context=context,
                metadata={
                    "stage": "reasoning_to_intent",
                },
            )

        if reasoning_operation.status is IntelligenceOperationStatus.FAILED:
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.FAILED,
                context=context,
                metadata={
                    "stage": "reasoning_to_intent",
                    "failure": reasoning_operation.failure,
                },
            )

        reasoning_result = reasoning_operation.value

        if not isinstance(
            reasoning_result,
            ReasoningIntentResult,
        ):
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.FAILED,
                context=context,
                metadata={
                    "stage": "reasoning_to_intent",
                    "error": "invalid stage result",
                },
            )

        if (
            reasoning_result.status
            is not ReasoningIntentStatus.RESOLVED
        ):
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.BLOCKED,
                context=context,
                metadata={
                    "stage": "reasoning_to_intent",
                    "reason": reasoning_result.status.value,
                },
            )

        intent = reasoning_result.intent

        # ---------------------------------------------------------------
        # 9.5.3 Intent → Decision
        # ---------------------------------------------------------------

        decision_operation = self._failure_boundary.run(
            lambda: self._intent_decision.run(
                intent,
                self._decision_id,
                cancellation_token,
            ),
            cancellation_token,
        )

        if decision_operation.status is IntelligenceOperationStatus.CANCELLED:
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.CANCELLED,
                context=context,
                intent=intent,
                metadata={
                    "stage": "intent_to_decision",
                },
            )

        if decision_operation.status is IntelligenceOperationStatus.FAILED:
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.FAILED,
                context=context,
                intent=intent,
                metadata={
                    "stage": "intent_to_decision",
                    "failure": decision_operation.failure,
                },
            )

        decision_result = decision_operation.value

        if not isinstance(
            decision_result,
            IntentDecisionResult,
        ):
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.FAILED,
                context=context,
                intent=intent,
                metadata={
                    "stage": "intent_to_decision",
                    "error": "invalid stage result",
                },
            )

        decision = decision_result.decision

        # ---------------------------------------------------------------
        # 9.5.4 Decision → Proposal
        # ---------------------------------------------------------------

        proposal_operation = self._failure_boundary.run(
            lambda: self._decision_proposal.run(
                decision,
                self._proposal_id,
            ),
            cancellation_token,
        )

        if proposal_operation.status is IntelligenceOperationStatus.CANCELLED:
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.CANCELLED,
                context=context,
                intent=intent,
                decision=decision,
                metadata={
                    "stage": "decision_to_proposal",
                },
            )

        if proposal_operation.status is IntelligenceOperationStatus.FAILED:
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.FAILED,
                context=context,
                intent=intent,
                decision=decision,
                metadata={
                    "stage": "decision_to_proposal",
                    "failure": proposal_operation.failure,
                },
            )

        proposal_result = proposal_operation.value

        if not isinstance(
            proposal_result,
            DecisionProposalResult,
        ):
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.FAILED,
                context=context,
                intent=intent,
                decision=decision,
                metadata={
                    "stage": "decision_to_proposal",
                    "error": "invalid stage result",
                },
            )

        proposal = proposal_result.proposal

        # ---------------------------------------------------------------
        # 9.5.5 Semantic validation
        # ---------------------------------------------------------------

        validation_operation = self._failure_boundary.run(
            lambda: self._semantic_validation.run(
                intent,
                decision,
                proposal,
            ),
            cancellation_token,
        )

        if validation_operation.status is IntelligenceOperationStatus.CANCELLED:
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.CANCELLED,
                context=context,
                intent=intent,
                decision=decision,
                proposal=proposal,
                metadata={
                    "stage": "semantic_validation",
                },
            )

        if validation_operation.status is IntelligenceOperationStatus.FAILED:
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.FAILED,
                context=context,
                intent=intent,
                decision=decision,
                proposal=proposal,
                metadata={
                    "stage": "semantic_validation",
                    "failure": validation_operation.failure,
                },
            )

        validation_result = validation_operation.value

        if not isinstance(
            validation_result,
            SemanticValidationResult,
        ):
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.FAILED,
                context=context,
                intent=intent,
                decision=decision,
                proposal=proposal,
                metadata={
                    "stage": "semantic_validation",
                    "error": "invalid stage result",
                },
            )

        if (
            validation_result.status
            is not SemanticValidationStatus.VALID
        ):
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.BLOCKED,
                context=context,
                intent=intent,
                decision=decision,
                proposal=proposal,
                metadata={
                    "stage": "semantic_validation",
                    "reason": "semantic_validation_rejected",
                    "validation": validation_result.validation,
                },
            )

        # ---------------------------------------------------------------
        # 9.5.6 AgentDecision handoff
        # ---------------------------------------------------------------

        handoff_operation = self._failure_boundary.run(
            lambda: self._agent_handoff.run(
                validation_result,
            ),
            cancellation_token,
        )

        if handoff_operation.status is IntelligenceOperationStatus.CANCELLED:
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.CANCELLED,
                context=context,
                intent=intent,
                decision=decision,
                proposal=proposal,
                metadata={
                    "stage": "agent_decision_handoff",
                },
            )

        if handoff_operation.status is IntelligenceOperationStatus.FAILED:
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.FAILED,
                context=context,
                intent=intent,
                decision=decision,
                proposal=proposal,
                metadata={
                    "stage": "agent_decision_handoff",
                    "failure": handoff_operation.failure,
                },
            )

        handoff_result = handoff_operation.value

        if not isinstance(
            handoff_result,
            AgentDecisionHandoffResult,
        ):
            return IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.FAILED,
                context=context,
                intent=intent,
                decision=decision,
                proposal=proposal,
                metadata={
                    "stage": "agent_decision_handoff",
                    "error": "invalid stage result",
                },
            )

        agent_decision = handoff_result.agent_decision

        # ---------------------------------------------------------------
        # Complete
        # ---------------------------------------------------------------

        metadata["stage"] = "complete"

        return IntelligenceOrchestrationResult(
            status=IntelligenceOrchestrationStatus.COMPLETED,
            context=context,
            intent=intent,
            decision=decision,
            proposal=proposal,
            agent_decision=agent_decision,
            metadata=metadata,
        )