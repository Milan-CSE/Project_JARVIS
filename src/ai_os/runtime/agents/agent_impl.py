from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.runtime.agents.agent import Agent
from ai_os.runtime.agents.decision import (
    AgentDecision,
    AgentDecisionKind,
)
from ai_os.runtime.agents.request import AgentRequest
from ai_os.runtime.agents.resolver import WorkflowResolver
from ai_os.runtime.agents.response import AgentResponse
from ai_os.runtime.cancellation import CancellationToken
from ai_os.runtime.workflows import WorkflowRunner


class AgentResolutionError(RuntimeError):
    """Raised when a requested workflow cannot be resolved."""


@runtime_checkable
class Intelligence(Protocol):
    """Minimal decision boundary used by Agent.

    This is only a structural dependency for 8.10.
    Actual Intelligence implementation belongs to Step 9.
    """

    def decide(
        self,
        request: AgentRequest,
        cancellation_token: CancellationToken | None = None,
    ) -> AgentDecision:
        ...


class DefaultAgent:
    """Coordinates Intelligence, Workflow, and Runtime boundaries."""

    def __init__(
        self,
        intelligence: Intelligence,
        workflow_resolver: WorkflowResolver,
        workflow_runner: WorkflowRunner,
    ) -> None:
        if not isinstance(
            intelligence,
            Intelligence,
        ):
            raise TypeError(
                "intelligence must implement "
                "Intelligence protocol"
            )

        if not isinstance(
            workflow_resolver,
            WorkflowResolver,
        ):
            raise TypeError(
                "workflow_resolver must implement "
                "WorkflowResolver protocol"
            )

        if not isinstance(
            workflow_runner,
            WorkflowRunner,
        ):
            raise TypeError(
                "workflow_runner must implement "
                "WorkflowRunner protocol"
            )

        self._intelligence = intelligence
        self._workflow_resolver = workflow_resolver
        self._workflow_runner = workflow_runner

    def handle(
        self,
        request: AgentRequest,
        cancellation_token: CancellationToken | None = None,
    ) -> AgentResponse:
        if not isinstance(request, AgentRequest):
            raise TypeError(
                "request must be an AgentRequest"
            )

        decision = self._intelligence.decide(
            request,
            cancellation_token,
        )

        if not isinstance(
            decision,
            AgentDecision,
        ):
            raise TypeError(
                "Intelligence returned an invalid "
                "AgentDecision"
            )

        if (
            cancellation_token is not None
            and cancellation_token.is_cancelled
        ):
            return AgentResponse(
                request_id=request.request_id,
                message="request cancelled",
                metadata={
                    "termination_reason":
                        "explicit_cancellation",
                },
            )

        if decision.kind in (
            AgentDecisionKind.RESPOND,
            AgentDecisionKind.ASK_CLARIFICATION,
            AgentDecisionKind.DECLINE,
        ):
            return AgentResponse(
                request_id=request.request_id,
                message=decision.message,
                metadata=decision.metadata,
            )

        if decision.kind is AgentDecisionKind.RUN_WORKFLOW:
            workflow = self._workflow_resolver.resolve(
                decision.workflow_id,
            )

            if workflow is None:
                raise AgentResolutionError(
                    f"workflow not found: "
                    f"{decision.workflow_id}"
                )

            results = self._workflow_runner.execute(
                workflow,
                decision.parameters,
                cancellation_token,
            )

            return AgentResponse(
                request_id=request.request_id,
                execution_results=results,
                metadata=decision.metadata,
            )

        raise ValueError(
            f"unsupported AgentDecision kind: "
            f"{decision.kind}"
        )