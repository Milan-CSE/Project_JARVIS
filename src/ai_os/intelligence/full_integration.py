from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Protocol, runtime_checkable

from ai_os.intelligence.context import IntelligenceContext
from ai_os.intelligence.failure import (
    IntelligenceFailure,
    IntelligenceFailureBoundary,
    IntelligenceOperationStatus,
)
from ai_os.intelligence.memory_feedback import (
    MemoryFeedbackPipeline,
    MemoryFeedbackResult,
)
from ai_os.intelligence.orchestration import IntelligenceOrchestrator
from ai_os.intelligence.orchestration_models import (
    IntelligenceOrchestrationResult,
    IntelligenceOrchestrationStatus,
)
from ai_os.intelligence.response import (
    ResponseGenerationPipeline,
    ResponseGenerationResult,
)
from ai_os.intelligence.result_interpretation import (
    ResultInterpretationPipeline,
    ResultInterpretationResult,
)
from ai_os.intelligence.agent_intelligence import (
    AgentCommandReceipt,
    AgentFeedbackReceipt,
    AgentIntelligenceBridge,
)
from ai_os.runtime.cancellation import CancellationToken
from ai_os.runtime.contracts import (
    ExecutionPlan,
    ExecutionResult,
)


@dataclass(frozen=True, slots=True)
class ExecutionFeedback:
    """Immutable execution feedback supplied to 9.12."""

    plan: ExecutionPlan
    results: tuple[ExecutionResult, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "plan must be an ExecutionPlan"
            )

        if not isinstance(
            self.results,
            tuple,
        ):
            object.__setattr__(
                self,
                "results",
                tuple(self.results),
            )

        if not all(
            isinstance(
                result,
                ExecutionResult,
            )
            for result in self.results
        ):
            raise TypeError(
                "results must contain only ExecutionResult instances"
            )


class FullIntelligenceStatus(str, Enum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_FOR_EXECUTION = "waiting_for_execution"
    AGENT_REJECTED = "agent_rejected"
    EXECUTION_INCOMPLETE = "execution_incomplete"


@dataclass(frozen=True, slots=True)
class FullIntelligenceResult:
    """Immutable result of the complete 9.12 Intelligence integration."""

    status: FullIntelligenceStatus
    context: IntelligenceContext
    orchestration: IntelligenceOrchestrationResult
    response: ResponseGenerationResult | None = None
    command: AgentCommandReceipt | None = None
    feedback: AgentFeedbackReceipt | None = None
    interpretation: ResultInterpretationResult | None = None
    memory_feedback: MemoryFeedbackResult | None = None
    failure: IntelligenceFailure | None = None
    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            FullIntelligenceStatus,
        ):
            object.__setattr__(
                self,
                "status",
                FullIntelligenceStatus(self.status),
            )

        if not isinstance(
            self.context,
            IntelligenceContext,
        ):
            raise TypeError(
                "context must be an IntelligenceContext"
            )

        if not isinstance(
            self.orchestration,
            IntelligenceOrchestrationResult,
        ):
            raise TypeError(
                "orchestration must be an "
                "IntelligenceOrchestrationResult"
            )

        if self.response is not None and not isinstance(
            self.response,
            ResponseGenerationResult,
        ):
            raise TypeError(
                "response must be a ResponseGenerationResult "
                "or None"
            )

        if self.command is not None and not isinstance(
            self.command,
            AgentCommandReceipt,
        ):
            raise TypeError(
                "command must be an AgentCommandReceipt or None"
            )

        if self.feedback is not None and not isinstance(
            self.feedback,
            AgentFeedbackReceipt,
        ):
            raise TypeError(
                "feedback must be an AgentFeedbackReceipt or None"
            )

        if self.interpretation is not None and not isinstance(
            self.interpretation,
            ResultInterpretationResult,
        ):
            raise TypeError(
                "interpretation must be a "
                "ResultInterpretationResult or None"
            )

        if self.memory_feedback is not None and not isinstance(
            self.memory_feedback,
            MemoryFeedbackResult,
        ):
            raise TypeError(
                "memory_feedback must be a "
                "MemoryFeedbackResult or None"
            )

        if self.failure is not None and not isinstance(
            self.failure,
            IntelligenceFailure,
        ):
            raise TypeError(
                "failure must be an IntelligenceFailure or None"
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


@runtime_checkable
class ResponseStageContract(Protocol):
    def run(
        self,
        result: IntelligenceOrchestrationResult,
    ) -> ResponseGenerationResult:
        ...


class FullIntelligenceIntegration:
    """
    9.12 complete Intelligence composition.

    This class composes already-locked boundaries.
    It does not own their semantics.
    """

    def __init__(
        self,
        orchestrator: IntelligenceOrchestrator,
        agent_bridge: AgentIntelligenceBridge,
        *,
        result_interpretation: ResultInterpretationPipeline | None = None,
        memory_feedback: MemoryFeedbackPipeline | None = None,
        response_generation: ResponseStageContract | None = None,
        failure_boundary: IntelligenceFailureBoundary | None = None,
    ) -> None:
        if not isinstance(
            orchestrator,
            IntelligenceOrchestrator,
        ):
            raise TypeError(
                "orchestrator must implement "
                "IntelligenceOrchestrator"
            )

        if not isinstance(
            agent_bridge,
            AgentIntelligenceBridge,
        ):
            raise TypeError(
                "agent_bridge must be an AgentIntelligenceBridge"
            )

        if result_interpretation is None:
            result_interpretation = ResultInterpretationPipeline()

        if memory_feedback is None:
            memory_feedback = MemoryFeedbackPipeline()

        if response_generation is None:
            response_generation = ResponseGenerationPipeline()

        if failure_boundary is None:
            failure_boundary = IntelligenceFailureBoundary()

        if not isinstance(
            result_interpretation,
            ResultInterpretationPipeline,
        ):
            raise TypeError(
                "result_interpretation must be a "
                "ResultInterpretationPipeline"
            )

        if not isinstance(
            memory_feedback,
            MemoryFeedbackPipeline,
        ):
            raise TypeError(
                "memory_feedback must be a "
                "MemoryFeedbackPipeline"
            )

        if not isinstance(
            response_generation,
            ResponseStageContract,
        ):
            raise TypeError(
                "response_generation must implement "
                "ResponseStageContract"
            )

        if not isinstance(
            failure_boundary,
            IntelligenceFailureBoundary,
        ):
            raise TypeError(
                "failure_boundary must be an "
                "IntelligenceFailureBoundary"
            )

        self._orchestrator = orchestrator
        self._agent_bridge = agent_bridge
        self._result_interpretation = result_interpretation
        self._memory_feedback = memory_feedback
        self._response_generation = response_generation
        self._failure_boundary = failure_boundary

    def run(
        self,
        context: IntelligenceContext,
        execution_feedback: ExecutionFeedback | None = None,
        cancellation_token: CancellationToken | None = None,
    ) -> FullIntelligenceResult:
        if not isinstance(
            context,
            IntelligenceContext,
        ):
            raise TypeError(
                "context must be an IntelligenceContext"
            )

        if execution_feedback is not None and not isinstance(
            execution_feedback,
            ExecutionFeedback,
        ):
            raise TypeError(
                "execution_feedback must be an "
                "ExecutionFeedback or None"
            )

        orchestration_operation = self._failure_boundary.run(
            lambda: self._orchestrator.orchestrate(
                context,
                cancellation_token,
            ),
            cancellation_token,
        )

        if orchestration_operation.status is IntelligenceOperationStatus.CANCELLED:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.CANCELLED,
                context=context,
                orchestration=IntelligenceOrchestrationResult(
                    status=IntelligenceOrchestrationStatus.CANCELLED,
                    context=context,
                ),
                metadata={
                    "stage": "orchestration",
                },
            )

        if orchestration_operation.status is IntelligenceOperationStatus.FAILED:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=IntelligenceOrchestrationResult(
                    status=IntelligenceOrchestrationStatus.FAILED,
                    context=context,
                ),
                failure=orchestration_operation.failure,
                metadata={
                    "stage": "orchestration",
                },
            )

        orchestration = orchestration_operation.value

        if not isinstance(
            orchestration,
            IntelligenceOrchestrationResult,
        ):
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=IntelligenceOrchestrationResult(
                    status=IntelligenceOrchestrationStatus.FAILED,
                    context=context,
                ),
                metadata={
                    "stage": "orchestration",
                    "error": "invalid orchestration result",
                },
            )

        response_operation = self._failure_boundary.run(
            lambda: self._response_generation.run(
                orchestration,
            ),
            cancellation_token,
        )

        if response_operation.status is IntelligenceOperationStatus.CANCELLED:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.CANCELLED,
                context=context,
                orchestration=orchestration,
                metadata={
                    "stage": "response_generation",
                },
            )

        if response_operation.status is IntelligenceOperationStatus.FAILED:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=orchestration,
                failure=response_operation.failure,
                metadata={
                    "stage": "response_generation",
                },
            )

        response = response_operation.value

        if not isinstance(
            response,
            ResponseGenerationResult,
        ):
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=orchestration,
                metadata={
                    "stage": "response_generation",
                    "error": "invalid response result",
                },
            )

        if orchestration.status is not IntelligenceOrchestrationStatus.COMPLETED:
            status_map = {
                IntelligenceOrchestrationStatus.BLOCKED:
                    FullIntelligenceStatus.BLOCKED,
                IntelligenceOrchestrationStatus.FAILED:
                    FullIntelligenceStatus.FAILED,
                IntelligenceOrchestrationStatus.CANCELLED:
                    FullIntelligenceStatus.CANCELLED,
            }

            return FullIntelligenceResult(
                status=status_map[orchestration.status],
                context=context,
                orchestration=orchestration,
                response=response,
                metadata={
                    "stage": "orchestration_terminal",
                },
            )

        if orchestration.agent_decision is None:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=orchestration,
                response=response,
                metadata={
                    "stage": "agent_handoff",
                    "error": "completed orchestration "
                             "has no AgentDecision",
                },
            )

        command_operation = self._failure_boundary.run(
            lambda: self._agent_bridge.send(
                orchestration.agent_decision,
            ),
            cancellation_token,
        )

        if command_operation.status is IntelligenceOperationStatus.CANCELLED:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.CANCELLED,
                context=context,
                orchestration=orchestration,
                response=response,
                metadata={
                    "stage": "agent_handoff",
                },
            )

        if command_operation.status is IntelligenceOperationStatus.FAILED:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=orchestration,
                response=response,
                failure=command_operation.failure,
                metadata={
                    "stage": "agent_handoff",
                },
            )

        command = command_operation.value

        if not isinstance(
            command,
            AgentCommandReceipt,
        ):
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=orchestration,
                response=response,
                metadata={
                    "stage": "agent_handoff",
                    "error": "invalid command receipt",
                },
            )

        if not command.accepted:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.AGENT_REJECTED,
                context=context,
                orchestration=orchestration,
                response=response,
                command=command,
                metadata={
                    "stage": "agent_handoff",
                    "reason": "agent_rejected_command",
                },
            )

        if execution_feedback is None:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.WAITING_FOR_EXECUTION,
                context=context,
                orchestration=orchestration,
                response=response,
                command=command,
                metadata={
                    "stage": "waiting_for_execution",
                },
            )

        feedback_operation = self._failure_boundary.run(
            lambda: self._agent_bridge.receive(
                execution_feedback.results,
            ),
            cancellation_token,
        )

        if feedback_operation.status is IntelligenceOperationStatus.CANCELLED:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.CANCELLED,
                context=context,
                orchestration=orchestration,
                response=response,
                command=command,
                metadata={
                    "stage": "agent_feedback",
                },
            )

        if feedback_operation.status is IntelligenceOperationStatus.FAILED:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=orchestration,
                response=response,
                command=command,
                failure=feedback_operation.failure,
                metadata={
                    "stage": "agent_feedback",
                },
            )

        feedback = feedback_operation.value

        if not isinstance(
            feedback,
            AgentFeedbackReceipt,
        ):
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=orchestration,
                response=response,
                command=command,
                metadata={
                    "stage": "agent_feedback",
                    "error": "invalid feedback receipt",
                },
            )

        interpretation_operation = self._failure_boundary.run(
            lambda: self._result_interpretation.run(
                execution_feedback.plan,
                feedback.results,
            ),
            cancellation_token,
        )

        if interpretation_operation.status is IntelligenceOperationStatus.CANCELLED:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.CANCELLED,
                context=context,
                orchestration=orchestration,
                response=response,
                command=command,
                feedback=feedback,
                metadata={
                    "stage": "result_interpretation",
                },
            )

        if interpretation_operation.status is IntelligenceOperationStatus.FAILED:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=orchestration,
                response=response,
                command=command,
                feedback=feedback,
                failure=interpretation_operation.failure,
                metadata={
                    "stage": "result_interpretation",
                },
            )

        interpretation = interpretation_operation.value

        if not isinstance(
            interpretation,
            ResultInterpretationResult,
        ):
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=orchestration,
                response=response,
                command=command,
                feedback=feedback,
                metadata={
                    "stage": "result_interpretation",
                    "error": "invalid interpretation result",
                },
            )

        memory_operation = self._failure_boundary.run(
            lambda: self._memory_feedback.run(
                interpretation,
            ),
            cancellation_token,
        )

        if memory_operation.status is IntelligenceOperationStatus.CANCELLED:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.CANCELLED,
                context=context,
                orchestration=orchestration,
                response=response,
                command=command,
                feedback=feedback,
                interpretation=interpretation,
                metadata={
                    "stage": "memory_feedback",
                },
            )

        if memory_operation.status is IntelligenceOperationStatus.FAILED:
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=orchestration,
                response=response,
                command=command,
                feedback=feedback,
                interpretation=interpretation,
                failure=memory_operation.failure,
                metadata={
                    "stage": "memory_feedback",
                },
            )

        memory_feedback = memory_operation.value

        if not isinstance(
            memory_feedback,
            MemoryFeedbackResult,
        ):
            return FullIntelligenceResult(
                status=FullIntelligenceStatus.FAILED,
                context=context,
                orchestration=orchestration,
                response=response,
                command=command,
                feedback=feedback,
                interpretation=interpretation,
                metadata={
                    "stage": "memory_feedback",
                    "error": "invalid memory feedback result",
                },
            )

        interpretation_status = (
            interpretation.interpretation.status
        )

        if interpretation_status.value == "completed":
            final_status = FullIntelligenceStatus.COMPLETED
        elif interpretation_status.value == "failed":
            final_status = FullIntelligenceStatus.FAILED
        elif interpretation_status.value == "cancelled":
            final_status = FullIntelligenceStatus.CANCELLED
        else:
            final_status = FullIntelligenceStatus.EXECUTION_INCOMPLETE

        return FullIntelligenceResult(
            status=final_status,
            context=context,
            orchestration=orchestration,
            response=response,
            command=command,
            feedback=feedback,
            interpretation=interpretation,
            memory_feedback=memory_feedback,
            metadata={
                "stage": "complete",
            },
        )

    def decide(
        self,
        input: Any,
        cancellation_token: CancellationToken | None = None,
    ) -> FullIntelligenceResult:
        if isinstance(
            input,
            IntelligenceContext,
        ):
            context = input
        else:
            context = IntelligenceContext(
                input=input,
            )

        return self.run(
            context,
            cancellation_token=cancellation_token,
        )