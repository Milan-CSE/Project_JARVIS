from __future__ import annotations

from ai_os.intelligence.decision.decision import (
    Decision,
    DecisionKind,
)
from ai_os.intelligence.decision.proposal import (
    Proposal,
    WorkflowProposal,
)
from ai_os.intelligence.decision.validation import (
    SemanticValidator,
)
from ai_os.intelligence.intent import Intent
from ai_os.runtime.agents import (
    AgentDecision,
    AgentDecisionKind,
)


class UnsupportedDecisionKindError(ValueError):
    """Raised when a Step 9 decision cannot map to AgentDecision."""


class DecisionAdapter:
    """Translates validated Step 9 decisions into the 8.10 Agent contract."""

    def __init__(
        self,
        validator: SemanticValidator | None = None,
    ) -> None:
        self._validator = (
            validator
            if validator is not None
            else SemanticValidator()
        )

        if not isinstance(
            self._validator,
            SemanticValidator,
        ):
            raise TypeError(
                "validator must be a SemanticValidator"
            )

    def to_agent_decision(
        self,
        intent: Intent,
        decision: Decision,
        proposal: Proposal | None,
    ) -> AgentDecision:
        if not isinstance(intent, Intent):
            raise TypeError(
                "intent must be an Intent"
            )

        if not isinstance(decision, Decision):
            raise TypeError(
                "decision must be a Decision"
            )

        if proposal is not None and not isinstance(
            proposal,
            Proposal,
        ):
            raise TypeError(
                "proposal must be a Proposal or None"
            )

        validation = self._validator.validate(
            intent,
            decision,
            proposal,
        )

        if not validation.valid:
            raise ValueError(
                "cannot adapt invalid semantic decision: "
                + "; ".join(
                    issue.code
                    for issue in validation.issues
                )
            )

        if decision.kind is DecisionKind.USE_WORKFLOW:
            if not isinstance(
                proposal,
                WorkflowProposal,
            ):
                raise TypeError(
                    "USE_WORKFLOW requires "
                    "a WorkflowProposal"
                )

            return AgentDecision(
                kind=AgentDecisionKind.RUN_WORKFLOW,
                workflow_id=proposal.workflow_id,
                parameters=proposal.parameters,
                metadata=decision.metadata,
            )

        if decision.kind is DecisionKind.ANSWER:
            return AgentDecision(
                kind=AgentDecisionKind.RESPOND,
                metadata=decision.metadata,
            )

        if decision.kind is DecisionKind.REQUEST_CLARIFICATION:
            return AgentDecision(
                kind=AgentDecisionKind.ASK_CLARIFICATION,
                metadata=decision.metadata,
            )

        if decision.kind is DecisionKind.DECLINE:
            return AgentDecision(
                kind=AgentDecisionKind.DECLINE,
                metadata=decision.metadata,
            )

        raise UnsupportedDecisionKindError(
            f"unsupported DecisionKind: "
            f"{decision.kind}"
        )