import unittest

from ai_os.runtime.contracts import (
    ExecutionResult,
    ExecutionStatus,
    ExecutionStep,
)
from ai_os.runtime.workflows import (
    DefaultWorkflow,
    DefaultWorkflowRunner,
    WorkflowRunner,
)


class FakeRuntimeExecutor:

    def __init__(self):
        self.received_plan = None
        self.received_token = None

    def execute(
        self,
        plan,
        cancellation_token=None,
    ):
        self.received_plan = plan
        self.received_token = cancellation_token

        return tuple(
            ExecutionResult(
                plan_id=plan.plan_id,
                step_id=step.step_id,
                status=ExecutionStatus.COMPLETED,
                output={"ok": True},
            )
            for step in plan.steps
        )


class MissingExecuteRuntime:
    pass


class WorkflowRunnerTests(unittest.TestCase):

    def create_workflow(self):
        step = ExecutionStep(
            step_id="step:a",
            capability="test.action",
        )

        return DefaultWorkflow(
            workflow_id="workflow.test",
            version="1.0",
            steps=(step,),
        )

    def test_valid_runner_matches_protocol(self):
        runtime = FakeRuntimeExecutor()

        runner = DefaultWorkflowRunner(runtime)

        self.assertIsInstance(
            runner,
            WorkflowRunner,
        )

    def test_invalid_runtime_executor_rejected(self):
        with self.assertRaises(TypeError):
            DefaultWorkflowRunner(
                MissingExecuteRuntime()
            )

    def test_runner_creates_execution_plan(self):
        runtime = FakeRuntimeExecutor()

        runner = DefaultWorkflowRunner(runtime)

        workflow = self.create_workflow()

        results = runner.execute(workflow)

        self.assertEqual(
            len(results),
            1,
        )

        self.assertIsNotNone(
            runtime.received_plan
        )

        self.assertEqual(
            runtime.received_plan.steps,
            workflow.steps,
        )

    def test_plan_id_is_unique_per_run(self):
        runtime = FakeRuntimeExecutor()

        runner = DefaultWorkflowRunner(runtime)

        workflow = self.create_workflow()

        runner.execute(workflow)
        first_plan_id = runtime.received_plan.plan_id

        runner.execute(workflow)
        second_plan_id = runtime.received_plan.plan_id

        self.assertNotEqual(
            first_plan_id,
            second_plan_id,
        )

    def test_runner_returns_runtime_results_unchanged(self):
        runtime = FakeRuntimeExecutor()

        runner = DefaultWorkflowRunner(runtime)

        results = runner.execute(
            self.create_workflow()
        )

        self.assertEqual(
            results[0].status,
            ExecutionStatus.COMPLETED,
        )

        self.assertEqual(
            results[0].output,
            {"ok": True},
        )

    def test_cancellation_token_is_forwarded(self):
        class FakeToken:
            @property
            def is_cancelled(self):
                return False

        runtime = FakeRuntimeExecutor()

        runner = DefaultWorkflowRunner(runtime)

        token = FakeToken()

        runner.execute(
            self.create_workflow(),
            cancellation_token=token,
        )

        self.assertIs(
            runtime.received_token,
            token,
        )

    def test_workflow_does_not_get_runtime_internals(self):
        runtime = FakeRuntimeExecutor()

        runner = DefaultWorkflowRunner(runtime)

        workflow = self.create_workflow()

        runner.execute(workflow)

        self.assertFalse(
            hasattr(workflow, "scheduler")
        )

        self.assertFalse(
            hasattr(workflow, "task_executor")
        )

        self.assertFalse(
            hasattr(workflow, "registry")
        )

    def test_runner_does_not_resolve_tasks(self):
        runtime = FakeRuntimeExecutor()

        runner = DefaultWorkflowRunner(runtime)

        workflow = self.create_workflow()

        runner.execute(workflow)

        self.assertFalse(
            hasattr(runner, "registry")
        )

        self.assertFalse(
            hasattr(runner, "task_registry")
        )

    def test_runner_does_not_require_engine(self):
        runtime = FakeRuntimeExecutor()

        runner = DefaultWorkflowRunner(runtime)

        self.assertFalse(
            hasattr(runner, "engine")
        )

    def test_runner_does_not_require_intelligence(self):
        runtime = FakeRuntimeExecutor()

        runner = DefaultWorkflowRunner(runtime)

        self.assertFalse(
            hasattr(runner, "reason")
        )

        self.assertFalse(
            hasattr(runner, "think")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)