from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Protocol, runtime_checkable

from ai_os.intelligence.result_interpretation import (
    ResultInterpretation,
    ResultInterpretationResult,
)


class MemoryFeedbackStatus(str, Enum):
    NO_UPDATE = "no_update"
    CANDIDATES = "candidates"


@dataclass(frozen=True, slots=True)
class MemoryCandidate:
    """Immutable proposal for information that may become memory."""

    content: str
    category: str
    confidence: float
    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError(
                "content must be a string"
            )

        if not self.content.strip():
            raise ValueError(
                "content must not be empty or whitespace"
            )

        if not isinstance(self.category, str):
            raise TypeError(
                "category must be a string"
            )

        if not self.category.strip():
            raise ValueError(
                "category must not be empty or whitespace"
            )

        if isinstance(self.confidence, bool) or not isinstance(
            self.confidence,
            (int, float),
        ):
            raise TypeError(
                "confidence must be a number"
            )

        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
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
            "confidence",
            float(self.confidence),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


@dataclass(frozen=True, slots=True)
class MemoryFeedbackResult:
    """Immutable result of the 9.10 memory-feedback stage."""

    status: MemoryFeedbackStatus
    source: ResultInterpretationResult
    candidates: tuple[MemoryCandidate, ...] = ()
    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            MemoryFeedbackStatus,
        ):
            object.__setattr__(
                self,
                "status",
                MemoryFeedbackStatus(self.status),
            )

        if not isinstance(
            self.source,
            ResultInterpretationResult,
        ):
            raise TypeError(
                "source must be a ResultInterpretationResult"
            )

        if not isinstance(
            self.candidates,
            tuple,
        ):
            object.__setattr__(
                self,
                "candidates",
                tuple(self.candidates),
            )

        if not all(
            isinstance(
                candidate,
                MemoryCandidate,
            )
            for candidate in self.candidates
        ):
            raise TypeError(
                "candidates must contain only "
                "MemoryCandidate instances"
            )

        seen: set[tuple[str, str]] = set()

        for candidate in self.candidates:
            identity = (
                candidate.category,
                candidate.content,
            )

            if identity in seen:
                raise ValueError(
                    "duplicate memory candidates are not allowed"
                )

            seen.add(identity)

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

        expected_status = (
            MemoryFeedbackStatus.CANDIDATES
            if self.candidates
            else MemoryFeedbackStatus.NO_UPDATE
        )

        if self.status is not expected_status:
            raise ValueError(
                "status does not match candidates"
            )


@runtime_checkable
class MemoryFeedbackEvaluatorContract(Protocol):
    """
    Contract for deciding whether interpreted results contain
    information worth proposing as persistent memory.
    """

    def evaluate(
        self,
        source: ResultInterpretationResult,
    ) -> Iterable[MemoryCandidate]:
        ...


class DefaultMemoryFeedbackEvaluator:
    """
    Conservative default evaluator.

    It deliberately proposes no persistent memory automatically.
    """

    def evaluate(
        self,
        source: ResultInterpretationResult,
    ) -> tuple[MemoryCandidate, ...]:
        if not isinstance(
            source,
            ResultInterpretationResult,
        ):
            raise TypeError(
                "source must be a ResultInterpretationResult"
            )

        return ()


class MemoryFeedbackPipeline:
    """
    9.10 boundary:

        ResultInterpretationResult
                  ↓
        MemoryFeedbackEvaluatorContract
                  ↓
          MemoryFeedbackResult

    No persistence occurs here.
    """

    def __init__(
        self,
        evaluator: MemoryFeedbackEvaluatorContract | None = None,
    ) -> None:
        if evaluator is None:
            evaluator = DefaultMemoryFeedbackEvaluator()

        if not isinstance(
            evaluator,
            MemoryFeedbackEvaluatorContract,
        ):
            raise TypeError(
                "evaluator must implement "
                "MemoryFeedbackEvaluatorContract"
            )

        self._evaluator = evaluator

    def run(
        self,
        source: ResultInterpretationResult,
    ) -> MemoryFeedbackResult:
        if not isinstance(
            source,
            ResultInterpretationResult,
        ):
            raise TypeError(
                "source must be a ResultInterpretationResult"
            )

        candidates = tuple(
            self._evaluator.evaluate(source)
        )

        if not all(
            isinstance(
                candidate,
                MemoryCandidate,
            )
            for candidate in candidates
        ):
            raise TypeError(
                "evaluator must return "
                "MemoryCandidate instances"
            )

        return MemoryFeedbackResult(
            status=(
                MemoryFeedbackStatus.CANDIDATES
                if candidates
                else MemoryFeedbackStatus.NO_UPDATE
            ),
            source=source,
            candidates=candidates,
            metadata={
                "stage": "memory_feedback",
            },
        )