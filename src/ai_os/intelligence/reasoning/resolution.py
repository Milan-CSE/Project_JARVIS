from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from ai_os.intelligence.reasoning.result import ReasoningResult


class ReasoningResolutionStatus(str, Enum):
    """Disposition of a ReasoningResult for Intent selection."""

    READY = "ready"
    CLARIFICATION_REQUIRED = "clarification_required"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class ReasoningResolutionIssue:
    """Structured issue affecting reasoning resolution."""

    code: str
    message: str
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.code, str):
            raise TypeError(
                "code must be a string"
            )

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
class ReasoningResolution:
    """Immutable readiness assessment for Intent selection."""

    status: ReasoningResolutionStatus
    candidate_index: int | None = None
    issues: tuple[ReasoningResolutionIssue, ...] = ()
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            ReasoningResolutionStatus,
        ):
            object.__setattr__(
                self,
                "status",
                ReasoningResolutionStatus(self.status),
            )

        if self.candidate_index is not None:
            if isinstance(
                self.candidate_index,
                bool,
            ):
                raise TypeError(
                    "candidate_index must be an integer or None"
                )

            if not isinstance(
                self.candidate_index,
                int,
            ):
                raise TypeError(
                    "candidate_index must be an integer or None"
                )

        if not isinstance(self.issues, tuple):
            object.__setattr__(
                self,
                "issues",
                tuple(self.issues),
            )

        if not all(
            isinstance(
                issue,
                ReasoningResolutionIssue,
            )
            for issue in self.issues
        ):
            raise TypeError(
                "issues must contain "
                "ReasoningResolutionIssue instances"
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


class ReasoningResolver:
    """Deterministically assesses whether reasoning can proceed."""

    def resolve(
        self,
        result: ReasoningResult,
        candidate_index: int | None = None,
    ) -> ReasoningResolution:
        if not isinstance(
            result,
            ReasoningResult,
        ):
            raise TypeError(
                "result must be a ReasoningResult"
            )

        candidates = result.intent_candidates

        if not candidates:
            return ReasoningResolution(
                status=ReasoningResolutionStatus.UNRESOLVED,
                issues=(
                    ReasoningResolutionIssue(
                        code="NO_INTENT_CANDIDATE",
                        message=(
                            "reasoning produced no "
                            "intent candidates"
                        ),
                    ),
                ),
            )

        if candidate_index is not None:
            if isinstance(
                candidate_index,
                bool,
            ):
                raise TypeError(
                    "candidate_index must be an integer "
                    "or None"
                )

            if not isinstance(
                candidate_index,
                int,
            ):
                raise TypeError(
                    "candidate_index must be an integer "
                    "or None"
                )

            if (
                candidate_index < 0
                or candidate_index >= len(candidates)
            ):
                raise IndexError(
                    "candidate_index is out of range"
                )

            return ReasoningResolution(
                status=ReasoningResolutionStatus.READY,
                candidate_index=candidate_index,
            )

        if len(candidates) > 1:
            return ReasoningResolution(
                status=(
                    ReasoningResolutionStatus
                    .CLARIFICATION_REQUIRED
                ),
                issues=(
                    ReasoningResolutionIssue(
                        code="MULTIPLE_INTENT_CANDIDATES",
                        message=(
                            "multiple intent candidates "
                            "require explicit selection"
                        ),
                        metadata={
                            "candidate_count": len(
                                candidates
                            ),
                        },
                    ),
                ),
            )

        return ReasoningResolution(
            status=ReasoningResolutionStatus.READY,
            candidate_index=0,
        )