from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from ai_os.runtime.contracts import ExecutionResult


@dataclass(frozen=True, slots=True)
class AgentResponse:
    """Immutable interaction-level response."""

    request_id: str
    message: str | None = None
    execution_results: tuple[ExecutionResult, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str):
            raise TypeError("request_id must be a string")

        if not self.request_id.strip():
            raise ValueError(
                "request_id must not be empty"
            )

        if not isinstance(
            self.execution_results,
            tuple,
        ):
            object.__setattr__(
                self,
                "execution_results",
                tuple(self.execution_results),
            )

        if not all(
            isinstance(result, ExecutionResult)
            for result in self.execution_results
        ):
            raise TypeError(
                "execution_results must contain "
                "ExecutionResult instances"
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )