from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from ai_os.intelligence.context import ContextSource


def _freeze_value(value: Any) -> Any:
    """Recursively snapshot and freeze common data containers."""

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


class UncertaintyLevel(str, Enum):
    """Qualitative reasoning uncertainty."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ReasoningObservation:
    """Descriptive observation derived from Context."""

    value: Any
    source: ContextSource
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.source, ContextSource):
            object.__setattr__(
                self,
                "source",
                ContextSource(self.source),
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "value",
            _freeze_value(self.value),
        )

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class Ambiguity:
    """One ambiguity discovered during reasoning."""

    description: str
    candidates: tuple[Any, ...] = ()
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.description, str):
            raise TypeError(
                "description must be a string"
            )

        if not self.description.strip():
            raise ValueError(
                "description must not be empty"
            )

        if not isinstance(self.candidates, tuple):
            object.__setattr__(
                self,
                "candidates",
                tuple(self.candidates),
            )

        object.__setattr__(
            self,
            "candidates",
            tuple(
                _freeze_value(candidate)
                for candidate in self.candidates
            ),
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
class MissingInformation:
    """Information needed but not available to Reasoning."""

    name: str
    description: str | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError(
                "name must be a string"
            )

        if not self.name.strip():
            raise ValueError(
                "name must not be empty"
            )

        if self.description is not None:
            if not isinstance(self.description, str):
                raise TypeError(
                    "description must be a string or None"
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
class IntentCandidate:
    """Plausible interpretation of a desired outcome."""

    goal: str
    parameters: Mapping[str, Any] = field(
        default_factory=dict
    )
    constraints: Mapping[str, Any] = field(
        default_factory=dict
    )
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.goal, str):
            raise TypeError(
                "goal must be a string"
            )

        if not self.goal.strip():
            raise ValueError(
                "goal must not be empty"
            )

        if not isinstance(self.parameters, Mapping):
            raise TypeError(
                "parameters must be a mapping"
            )

        if not isinstance(self.constraints, Mapping):
            raise TypeError(
                "constraints must be a mapping"
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "parameters",
            _freeze_mapping(self.parameters),
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
class ReasoningUncertainty:
    """Qualitative uncertainty associated with reasoning."""

    level: UncertaintyLevel
    reasons: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.level, UncertaintyLevel):
            object.__setattr__(
                self,
                "level",
                UncertaintyLevel(self.level),
            )

        if not isinstance(self.reasons, tuple):
            object.__setattr__(
                self,
                "reasons",
                tuple(self.reasons),
            )

        if not all(
            isinstance(reason, str) and reason.strip()
            for reason in self.reasons
        ):
            raise TypeError(
                "reasons must contain non-empty strings"
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
class ReasoningResult:
    """Immutable structured output from one reasoning operation."""

    interpretation: str = ""
    observations: tuple[ReasoningObservation, ...] = ()
    ambiguities: tuple[Ambiguity, ...] = ()
    missing_information: tuple[MissingInformation, ...] = ()
    intent_candidates: tuple[IntentCandidate, ...] = ()
    uncertainty: ReasoningUncertainty | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.interpretation, str):
            raise TypeError(
                "interpretation must be a string"
            )

        if not isinstance(self.observations, tuple):
            object.__setattr__(
                self,
                "observations",
                tuple(self.observations),
            )

        if not all(
            isinstance(
                observation,
                ReasoningObservation,
            )
            for observation in self.observations
        ):
            raise TypeError(
                "observations must contain "
                "ReasoningObservation instances"
            )

        if not isinstance(self.ambiguities, tuple):
            object.__setattr__(
                self,
                "ambiguities",
                tuple(self.ambiguities),
            )

        if not all(
            isinstance(
                ambiguity,
                Ambiguity,
            )
            for ambiguity in self.ambiguities
        ):
            raise TypeError(
                "ambiguities must contain Ambiguity instances"
            )

        if not isinstance(
            self.missing_information,
            tuple,
        ):
            object.__setattr__(
                self,
                "missing_information",
                tuple(self.missing_information),
            )

        if not all(
            isinstance(
                item,
                MissingInformation,
            )
            for item in self.missing_information
        ):
            raise TypeError(
                "missing_information must contain "
                "MissingInformation instances"
            )

        if not isinstance(
            self.intent_candidates,
            tuple,
        ):
            object.__setattr__(
                self,
                "intent_candidates",
                tuple(self.intent_candidates),
            )

        if not all(
            isinstance(
                candidate,
                IntentCandidate,
            )
            for candidate in self.intent_candidates
        ):
            raise TypeError(
                "intent_candidates must contain "
                "IntentCandidate instances"
            )

        if self.uncertainty is not None:
            if not isinstance(
                self.uncertainty,
                ReasoningUncertainty,
            ):
                raise TypeError(
                    "uncertainty must be "
                    "ReasoningUncertainty or None"
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