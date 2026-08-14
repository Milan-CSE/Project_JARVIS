from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


def _freeze_value(value: Any) -> Any:
    """Recursively freeze common container types."""

    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                key: _freeze_value(item)
                for key, item in value.items()
            }
        )

    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze_value(item)
            for item in value
        )

    if isinstance(value, (set, frozenset)):
        return frozenset(
            _freeze_value(item)
            for item in value
        )

    return value


def _freeze_mapping(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    return MappingProxyType(
        {
            key: _freeze_value(item)
            for key, item in value.items()
        }
    )


class ProposalKind(str, Enum):
    """Type of concrete proposal."""

    WORKFLOW = "workflow"
    PLAN = "plan"


@dataclass(frozen=True, slots=True)
class Proposal:
    """Immutable, unvalidated candidate produced from a Decision."""

    proposal_id: str
    decision_id: str
    kind: ProposalKind
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.proposal_id, str):
            raise TypeError(
                "proposal_id must be a string"
            )

        if not self.proposal_id.strip():
            raise ValueError(
                "proposal_id must not be empty"
            )

        if not isinstance(self.decision_id, str):
            raise TypeError(
                "decision_id must be a string"
            )

        if not self.decision_id.strip():
            raise ValueError(
                "decision_id must not be empty"
            )

        if not isinstance(self.kind, ProposalKind):
            object.__setattr__(
                self,
                "kind",
                ProposalKind(self.kind),
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class WorkflowProposal(Proposal):
    """Immutable proposal to use an existing Workflow."""

    workflow_id: str = ""
    parameters: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        # Normalize first so both:
        # kind=ProposalKind.WORKFLOW
        # and:
        # kind="workflow"
        # are accepted.
        if not isinstance(self.kind, ProposalKind):
            object.__setattr__(
                self,
                "kind",
                ProposalKind(self.kind),
            )

        if self.kind is not ProposalKind.WORKFLOW:
            raise ValueError(
                "WorkflowProposal kind must be WORKFLOW"
            )

        if not isinstance(self.workflow_id, str):
            raise TypeError(
                "workflow_id must be a string"
            )

        if not self.workflow_id.strip():
            raise ValueError(
                "workflow_id must not be empty"
            )

        if not isinstance(self.parameters, Mapping):
            raise TypeError(
                "parameters must be a mapping"
            )

        # Explicit parent call avoids the dataclass-slots
        # zero-argument super() issue.
        Proposal.__post_init__(self)

        object.__setattr__(
            self,
            "parameters",
            _freeze_mapping(self.parameters),
        )