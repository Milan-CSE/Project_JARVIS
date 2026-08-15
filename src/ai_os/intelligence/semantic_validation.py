from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from ai_os.intelligence.decision import (
    Decision,
    Proposal,
    SemanticValidator,
    ValidationResult,
)
from ai_os.intelligence.intent import Intent


@runtime_checkable
class SemanticValidatorContract(Protocol):
    """9.5.5 contract for Intent/Decision/Proposal validation."""

    def validate(
        self,
        intent: Intent,
        decision: Decision,
        proposal: Proposal | None,
    ) -> ValidationResult:
        ...


class SemanticValidationStatus(str, Enum):
    VALID = "valid"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class SemanticValidationResult:
    """Immutable result of the 9.5.5 semantic-validation stage."""

    status: SemanticValidationStatus
    intent: Intent
    decision: Decision
    proposal: Proposal | None
    validation: ValidationResult
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            SemanticValidationStatus,
        ):
            object.__setattr__(
                self,
                "status",
                SemanticValidationStatus(self.status),
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
            ValidationResult,
        ):
            raise TypeError(
                "validation must be a ValidationResult"
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

        expected_status = (
            SemanticValidationStatus.VALID
            if self.validation.valid
            else SemanticValidationStatus.REJECTED
        )

        if self.status is not expected_status:
            raise ValueError(
                "status does not match validation.valid"
            )


class SemanticValidationPipeline:
    """
    9.5.5 pipeline:

        Intent
           +
        Decision
           +
        Proposal | None
           ↓
        SemanticValidatorContract
           ↓
        ValidationResult
           ↓
        SemanticValidationResult

    This stage validates semantics only.
    It does not execute, authorize, or create AgentDecision.
    """

    def __init__(
        self,
        validator: SemanticValidatorContract,
    ) -> None:
        if not isinstance(
            validator,
            SemanticValidatorContract,
        ):
            raise TypeError(
                "validator must implement "
                "SemanticValidatorContract"
            )

        self._validator = validator

    def run(
        self,
        intent: Intent,
        decision: Decision,
        proposal: Proposal | None,
    ) -> SemanticValidationResult:
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

        if not isinstance(
            validation,
            ValidationResult,
        ):
            raise TypeError(
                "validator must return a ValidationResult"
            )

        status = (
            SemanticValidationStatus.VALID
            if validation.valid
            else SemanticValidationStatus.REJECTED
        )

        return SemanticValidationResult(
            status=status,
            intent=intent,
            decision=decision,
            proposal=proposal,
            validation=validation,
            metadata={
                "stage": "semantic_validation",
            },
        )