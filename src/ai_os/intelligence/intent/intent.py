from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Intent:
    """Immutable semantic description of a desired outcome."""

    intent_id: str
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
        if not isinstance(self.intent_id, str):
            raise TypeError(
                "intent_id must be a string"
            )

        if not self.intent_id.strip():
            raise ValueError(
                "intent_id must not be empty"
            )

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
            MappingProxyType(
                dict(self.parameters)
            ),
        )

        object.__setattr__(
            self,
            "constraints",
            MappingProxyType(
                dict(self.constraints)
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )