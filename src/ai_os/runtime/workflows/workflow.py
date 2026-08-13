from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable

from ai_os.runtime.contracts import ExecutionStep


@runtime_checkable
class Workflow(Protocol):
    """Contract for a reusable declarative workflow definition."""

    @property
    def workflow_id(self) -> str:
        ...

    @property
    def version(self) -> str:
        ...

    @property
    def metadata(self) -> Mapping[str, object]:
        ...

    def build_steps(
        self,
        parameters: Mapping[str, object],
    ) -> Sequence[ExecutionStep]:
        ...