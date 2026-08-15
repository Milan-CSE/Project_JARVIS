from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from ai_os.intelligence.decision import (
    Decision,
    DecisionKind,
    Proposal,
    ProposalKind,
    WorkflowProposal,
)


@runtime_checkable
class ProposalGeneratorContract(Protocol):
    """9.5.4 contract for Decision → Proposal generation."""

    def generate(
        self,
        decision: Decision,
        proposal_id: str,
    ) -> Proposal | None:
        ...


class DecisionProposalStatus(str, Enum):
    PROPOSAL_CREATED = "proposal_created"
    NO_PROPOSAL_REQUIRED = "no_proposal_required"


@dataclass(frozen=True, slots=True)
class DecisionProposalResult:
    """Immutable result of the 9.5.4 Decision → Proposal pipeline."""

    status: DecisionProposalStatus
    decision: Decision
    proposal: Proposal | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            DecisionProposalStatus,
        ):
            object.__setattr__(
                self,
                "status",
                DecisionProposalStatus(self.status),
            )

        if not isinstance(
            self.decision,
            Decision,
        ):
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


class DecisionProposalPipeline:
    """
    9.5.4 pipeline:

        Decision
           ↓
        ProposalGeneratorContract
           ↓
        Proposal | None
           ↓
        DecisionProposalResult

    This stage does not perform semantic validation.
    That belongs to 9.5.5.
    """

    def __init__(
        self,
        proposal_generator: ProposalGeneratorContract,
    ) -> None:
        if not isinstance(
            proposal_generator,
            ProposalGeneratorContract,
        ):
            raise TypeError(
                "proposal_generator must implement "
                "ProposalGeneratorContract"
            )

        self._proposal_generator = proposal_generator

    def run(
        self,
        decision: Decision,
        proposal_id: str,
    ) -> DecisionProposalResult:
        # ---------------------------------------------------------------
        # Input validation
        # ---------------------------------------------------------------

        if not isinstance(
            decision,
            Decision,
        ):
            raise TypeError(
                "decision must be a Decision"
            )

        if not isinstance(
            proposal_id,
            str,
        ):
            raise TypeError(
                "proposal_id must be a string"
            )

        if not proposal_id.strip():
            raise ValueError(
                "proposal_id must not be empty or whitespace"
            )

        # ---------------------------------------------------------------
        # Decision → Proposal
        # ---------------------------------------------------------------

        proposal = self._proposal_generator.generate(
            decision,
            proposal_id,
        )

        # ---------------------------------------------------------------
        # Output boundary
        # ---------------------------------------------------------------

        if proposal is not None and not isinstance(
            proposal,
            Proposal,
        ):
            raise TypeError(
                "proposal_generator must return "
                "a Proposal or None"
            )

        # ---------------------------------------------------------------
        # Decision-kind mapping
        #
        # These are structural stage rules, not the full semantic
        # validation performed by SemanticValidator in 9.5.5.
        # ---------------------------------------------------------------

        if decision.kind is DecisionKind.USE_WORKFLOW:
            if proposal is None:
                raise ValueError(
                    "USE_WORKFLOW requires a Proposal"
                )

            if not isinstance(
                proposal,
                WorkflowProposal,
            ):
                raise TypeError(
                    "USE_WORKFLOW requires a WorkflowProposal"
                )

            return DecisionProposalResult(
                status=DecisionProposalStatus.PROPOSAL_CREATED,
                decision=decision,
                proposal=proposal,
                metadata={
                    "stage": "decision_to_proposal",
                },
            )

        # ANSWER / REQUEST_CLARIFICATION / DECLINE
        # must not create proposals in the current locked model.
        if proposal is not None:
            raise ValueError(
                f"{decision.kind.value} must not produce a proposal"
            )

        return DecisionProposalResult(
            status=DecisionProposalStatus.NO_PROPOSAL_REQUIRED,
            decision=decision,
            proposal=None,
            metadata={
                "stage": "decision_to_proposal",
            },
        )