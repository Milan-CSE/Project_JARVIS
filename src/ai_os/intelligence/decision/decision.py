from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
from enum import Enum


class DecisionKind(str, Enum):
    """Semantic decision made by Intelligence."""

    USE_WORKFLOW = "use_workflow"
    ANSWER = "answer"
    REQUEST_CLARIFICATION = "request_clarification"
    DECLINE = "decline"


@dataclass(frozen=True, slots=True)
class Decision:
    """Immutable semantic decision associated with an Intent."""

    decision_id: str
    intent_id: str
    kind: DecisionKind
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.decision_id, str):
            raise TypeError(
                "decision_id must be a string"
            )

        if not self.decision_id.strip():
            raise ValueError(
                "decision_id must not be empty"
            )

        if not isinstance(self.intent_id, str):
            raise TypeError(
                "intent_id must be a string"
            )

        if not self.intent_id.strip():
            raise ValueError(
                "intent_id must not be empty"
            )

        if not isinstance(self.kind, DecisionKind):
            object.__setattr__(
                self,
                "kind",
                DecisionKind(self.kind),
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