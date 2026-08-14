from __future__ import annotations

from dataclasses import dataclass, field as dataclasss_field
from types import MappingProxyType
from typing import Any, Mapping

from ai_os.intelligence.decision.decision import (
    Decision,
    DecisionKind,
)
from ai_os.intelligence.decision.proposal import (
    Proposal,
    ProposalKind,
    WorkflowProposal,
)
from ai_os.intelligence.intent.intent import Intent


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One deterministic semantic validation issue."""

    code: str
    message: str
    field: str | None = None
    metadata: Mapping[str, Any] = dataclasss_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.code, str):
            raise TypeError("code must be a string")

        if not self.code.strip():
            raise ValueError(
                "code must not be empty"
            )

        if not isinstance(self.message, str):
            raise TypeError(
                "message must be a string"
            )

        if not self.message.strip():
            raise ValueError(
                "message must not be empty"
            )

        if self.field is not None:
            if not isinstance(self.field, str):
                raise TypeError(
                    "field must be a string or None"
                )

            if not self.field.strip():
                raise ValueError(
                    "field must not be empty"
                )

        if not isinstance(self.metadata, Mapping):
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


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Immutable result of semantic validation."""

    valid: bool
    issues: tuple[ValidationIssue, ...] = ()
    metadata: Mapping[str, Any] = dataclasss_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.valid, bool):
            raise TypeError(
                "valid must be a bool"
            )

        if not isinstance(self.issues, tuple):
            object.__setattr__(
                self,
                "issues",
                tuple(self.issues),
            )

        if not all(
            isinstance(issue, ValidationIssue)
            for issue in self.issues
        ):
            raise TypeError(
                "issues must contain ValidationIssue instances"
            )

        if not isinstance(self.metadata, Mapping):
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


class SemanticValidator:
    """Pure validator for Intent/Decision/Proposal relationships."""

    def validate(
        self,
        intent: Intent,
        decision: Decision,
        proposal: Proposal | None,
    ) -> ValidationResult:

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

        issues: list[ValidationIssue] = []

        if decision.intent_id != intent.intent_id:
            issues.append(
                ValidationIssue(
                    code="INTENT_MISMATCH",
                    message=(
                        "decision does not reference "
                        "the supplied intent"
                    ),
                    field="decision.intent_id",
                    metadata={
                        "expected": intent.intent_id,
                        "actual": decision.intent_id,
                    },
                )
            )

        if decision.kind is DecisionKind.USE_WORKFLOW:
            if proposal is None:
                issues.append(
                    ValidationIssue(
                        code="REQUIRED_PROPOSAL_MISSING",
                        message=(
                            "USE_WORKFLOW requires "
                            "a proposal"
                        ),
                        field="proposal",
                    )
                )
            else:
                if proposal.decision_id != decision.decision_id:
                    issues.append(
                        ValidationIssue(
                            code="PROPOSAL_DECISION_MISMATCH",
                            message=(
                                "proposal does not reference "
                                "the supplied decision"
                            ),
                            field="proposal.decision_id",
                            metadata={
                                "expected": decision.decision_id,
                                "actual": proposal.decision_id,
                            },
                        )
                    )

                if proposal.kind is not ProposalKind.WORKFLOW:
                    issues.append(
                        ValidationIssue(
                            code="PROPOSAL_KIND_MISMATCH",
                            message=(
                                "USE_WORKFLOW requires "
                                "a WORKFLOW proposal"
                            ),
                            field="proposal.kind",
                        )
                    )

        else:
            if proposal is not None:
                issues.append(
                    ValidationIssue(
                        code="UNEXPECTED_PROPOSAL",
                        message=(
                            f"{decision.kind.value} "
                            "must not contain a proposal"
                        ),
                        field="proposal",
                    )
                )

        return ValidationResult(
            valid=not issues,
            issues=tuple(issues),
        )