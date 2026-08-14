from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from ai_os.intelligence.decision.proposal import (
    Proposal,
    ProposalKind,
)


def _freeze_value(value: Any) -> Any:
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


@dataclass(frozen=True, slots=True)
class PlanStepProposal:
    """Immutable candidate step produced by Intelligence."""

    step_id: str
    capability: str
    input: Any = None
    dependencies: tuple[str, ...] = ()
    constraints: Mapping[str, Any] = field(
        default_factory=dict
    )
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.step_id, str):
            raise TypeError(
                "step_id must be a string"
            )

        if not self.step_id.strip():
            raise ValueError(
                "step_id must not be empty"
            )

        if not isinstance(self.capability, str):
            raise TypeError(
                "capability must be a string"
            )

        if not self.capability.strip():
            raise ValueError(
                "capability must not be empty"
            )

        if not isinstance(
            self.dependencies,
            tuple,
        ):
            object.__setattr__(
                self,
                "dependencies",
                tuple(self.dependencies),
            )

        if not all(
            isinstance(dep, str)
            and dep.strip()
            for dep in self.dependencies
        ):
            raise TypeError(
                "dependencies must contain "
                "non-empty strings"
            )

        if not isinstance(
            self.constraints,
            Mapping,
        ):
            raise TypeError(
                "constraints must be a mapping"
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
            "input",
            _freeze_value(self.input),
        )

        object.__setattr__(
            self,
            "constraints",
            _freeze_mapping(self.constraints),
        )

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class PlanProposal(Proposal):
    """Immutable candidate execution graph proposed by Intelligence."""

    steps: tuple[PlanStepProposal, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProposalKind):
            object.__setattr__(
                self,
                "kind",
                ProposalKind(self.kind),
            )

        if self.kind is not ProposalKind.PLAN:
            raise ValueError(
                "PlanProposal kind must be PLAN"
            )

        if not isinstance(self.steps, tuple):
            object.__setattr__(
                self,
                "steps",
                tuple(self.steps),
            )

        if not all(
            isinstance(
                step,
                PlanStepProposal,
            )
            for step in self.steps
        ):
            raise TypeError(
                "steps must contain PlanStepProposal instances"
            )

        step_ids = [
            step.step_id
            for step in self.steps
        ]

        if len(step_ids) != len(set(step_ids)):
            raise ValueError(
                "PlanProposal contains duplicate step_id values"
            )

        Proposal.__post_init__(self)