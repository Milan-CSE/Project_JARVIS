from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.runtime.cancellation import CancellationToken
from ai_os.runtime.contracts import (
    ExecutionPlan,
    ExecutionResult,
)


@runtime_checkable
class RuntimeExecutor(Protocol):
    """Contract for orchestrating execution of an ExecutionPlan."""

    def execute(
        self,
        plan: ExecutionPlan,
        cancellation_token: CancellationToken | None = None,
    ) -> tuple[ExecutionResult, ...]:
        ...