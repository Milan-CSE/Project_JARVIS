from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from ai_os.runtime.cancellation import CancellationToken
from ai_os.runtime.contracts import ExecutionResult
from ai_os.runtime.workflows.workflow import Workflow


@runtime_checkable
class WorkflowRunner(Protocol):
    """Contract for turning a Workflow into a Runtime execution."""

    def execute(
        self,
        workflow: Workflow,
        parameters: Mapping[str, object] | None = None,
        cancellation_token: CancellationToken | None = None,
    ) -> tuple[ExecutionResult, ...]:
        ...