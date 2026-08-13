import unittest

from ai_os.runtime.contracts import ExecutionStatus, ExecutionStep
from ai_os.runtime.executor_impl import DefaultRuntimeExecutor
from ai_os.runtime.scheduling import DependencyScheduler
from ai_os.runtime.tasks import (
    DefaultTaskExecutor,
    DefaultTaskRegistry,
)
from ai_os.runtime.workflows import (
    DefaultWorkflow,
    DefaultWorkflowRunner,
)


class WorkflowRuntimeIntegrationTests(unittest.TestCase):

    def test_workflow_executes_through_runtime(self):
        executed = []

        class TestTask:

            @property
            def capability(self):
                return "test.action"

            def execute(self, step):
                executed.append(step.step_id)
                return {"step": step.step_id}

        registry = DefaultTaskRegistry()
        registry.register(TestTask())
        registry.freeze()

        runtime = DefaultRuntimeExecutor(
            DependencyScheduler(),
            DefaultTaskExecutor(registry),
        )

        workflow = DefaultWorkflow(
            workflow_id="workflow.test",
            version="1.0",
            steps=(
                ExecutionStep(
                    step_id="step:a",
                    capability="test.action",
                ),
            ),
        )

        runner = DefaultWorkflowRunner(runtime)

        results = runner.execute(workflow)

        self.assertEqual(
            executed,
            ["step:a"],
        )

        self.assertEqual(
            results[0].status,
            ExecutionStatus.COMPLETED,
        )

        self.assertEqual(
            results[0].output,
            {"step": "step:a"},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)