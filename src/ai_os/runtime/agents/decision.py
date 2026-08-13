from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class AgentDecisionKind(str, Enum):
    RUN_WORKFLOW = "run_workflow"
    ASK_CLARIFICATION = "ask_clarification"
    RESPOND = "respond"
    DECLINE = "decline"


@dataclass(frozen=True, slots=True)
class AgentDecision:
    """Decision returned by the Intelligence boundary."""

    kind: AgentDecisionKind
    workflow_id: str | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)
    message: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AgentDecisionKind):
            object.__setattr__(
                self,
                "kind",
                AgentDecisionKind(self.kind),
            )

        if not isinstance(self.parameters, Mapping):
            raise TypeError("parameters must be a mapping")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        if self.kind is AgentDecisionKind.RUN_WORKFLOW:
            if not isinstance(self.workflow_id, str):
                raise TypeError(
                    "RUN_WORKFLOW requires a string workflow_id"
                )

            if not self.workflow_id.strip():
                raise ValueError(
                    "workflow_id must not be empty"
                )

        object.__setattr__(
            self,
            "parameters",
            MappingProxyType(dict(self.parameters)),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )