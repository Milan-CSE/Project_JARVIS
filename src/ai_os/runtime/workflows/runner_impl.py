from __future__ import annotations

from collections.abc import Mapping
from uuid import uuid4

from ai_os.runtime.cancellation import CancellationToken
from ai_os.runtime.contracts import ExecutionPlan, ExecutionResult
from ai_os.runtime.executor import RuntimeExecutor
from ai_os.runtime.workflows.workflow import Workflow


class DefaultWorkflowRunner:
    """Builds an ExecutionPlan from a Workflow and delegates to Runtime."""

    def __init__(
        self,
        runtime_executor: RuntimeExecutor,
    ) -> None:
        if not isinstance(runtime_executor, RuntimeExecutor):
            raise TypeError(
                "runtime_executor must implement "
                "RuntimeExecutor protocol"
            )

        self._runtime_executor = runtime_executor

    def execute(
        self,
        workflow: Workflow,
        parameters: Mapping[str, object] | None = None,
        cancellation_token: CancellationToken | None = None,
    ) -> tuple[ExecutionResult, ...]:
        if not isinstance(workflow, Workflow):
            raise TypeError(
                "workflow must implement Workflow protocol"
            )

        if parameters is None:
            parameters = {}

        if not isinstance(parameters, Mapping):
            raise TypeError(
                "parameters must be a mapping"
            )

        plan_id = f"plan:{uuid4().hex}"

        steps = tuple(
            workflow.build_steps(parameters)
        )

        if not steps:
            raise ValueError(
                "workflow produced no execution steps"
            )

        plan = ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
        )

        return self._runtime_executor.execute(
            plan,
            cancellation_token,
        )