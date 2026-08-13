from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType

from ai_os.runtime.contracts import ExecutionStep


@dataclass(frozen=True, slots=True)
class DefaultWorkflow:
    """Immutable reusable workflow definition."""

    workflow_id: str
    version: str
    steps: tuple[ExecutionStep, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.workflow_id, str):
            raise TypeError("workflow_id must be a string")

        if not self.workflow_id.strip():
            raise ValueError("workflow_id must not be empty")

        if not isinstance(self.version, str):
            raise TypeError("version must be a string")

        if not self.version.strip():
            raise ValueError("version must not be empty")

        if not isinstance(self.steps, tuple):
            object.__setattr__(
                self,
                "steps",
                tuple(self.steps),
            )

        if not self.steps:
            raise ValueError(
                "workflow must contain at least one step"
            )

        if not all(
            isinstance(step, ExecutionStep)
            for step in self.steps
        ):
            raise TypeError(
                "workflow steps must be ExecutionStep instances"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    def build_steps(
        self,
        parameters: Mapping[str, object],
    ) -> Sequence[ExecutionStep]:
        if not isinstance(parameters, Mapping):
            raise TypeError(
                "parameters must be a mapping"
            )

        # The initial Workflow layer is deliberately declarative.
        # Parameters are supplied to the workflow boundary, but
        # Workflow must not mutate existing ExecutionSteps.
        return self.steps