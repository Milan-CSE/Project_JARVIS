from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.runtime.workflows import Workflow


@runtime_checkable
class WorkflowResolver(Protocol):
    """Resolves a workflow identifier to a Workflow."""

    def resolve(
        self,
        workflow_id: str,
    ) -> Workflow | None:
        ...