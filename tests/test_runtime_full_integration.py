import unittest

from ai_os.runtime.agents import (
    AgentDecision,
    AgentDecisionKind,
    AgentRequest,
    DefaultAgent,
)
from ai_os.runtime.contracts import (
    ExecutionStatus,
    ExecutionStep,
)
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


class TestTask:

    def __init__(
        self,
        capability,
        executed,
        failing=False,
    ):
        self._capability = capability
        self._executed = executed
        self._failing = failing

    @property
    def capability(self):
        return self._capability

    def execute(self, step):
        self._executed.append(step.step_id)

        if self._failing:
            raise RuntimeError("task failed")

        return {
            "step_id": step.step_id,
            "capability": step.capability,
        }


class FakeIntelligence:

    def __init__(self, decision):
        self._decision = decision

    def decide(
        self,
        request,
        cancellation_token=None,
    ):
        return self._decision


class FakeWorkflowResolver:

    def __init__(self, workflow):
        self._workflow = workflow

    def resolve(self, workflow_id):
        if self._workflow is None:
            return None

        if self._workflow.workflow_id != workflow_id:
            return None

        return self._workflow


class RuntimeFullIntegrationTests(unittest.TestCase):

    def create_runtime(
        self,
        tasks,
        executed,
    ):
        registry = DefaultTaskRegistry()

        for task in tasks:
            registry.register(task)

        registry.freeze()

        task_executor = DefaultTaskExecutor(
            registry
        )

        scheduler = DependencyScheduler()

        return DefaultRuntimeExecutor(
            scheduler,
            task_executor,
        )

    def test_agent_to_runtime_end_to_end(self):
        executed = []

        task = TestTask(
            "test.action",
            executed,
        )

        runtime = self.create_runtime(
            [task],
            executed,
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

        runner = DefaultWorkflowRunner(
            runtime
        )

        agent = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.RUN_WORKFLOW,
                    workflow_id="workflow.test",
                )
            ),
            FakeWorkflowResolver(workflow),
            runner,
        )

        response = agent.handle(
            AgentRequest(
                request_id="request:test",
                input="run workflow",
            )
        )

        self.assertEqual(
            executed,
            ["step:a"],
        )

        self.assertEqual(
            len(response.execution_results),
            1,
        )

        result = response.execution_results[0]

        self.assertEqual(
            result.plan_id.startswith("plan:"),
            True,
        )

        self.assertEqual(
            result.step_id,
            "step:a",
        )

        self.assertEqual(
            result.status,
            ExecutionStatus.COMPLETED,
        )

    def test_dependency_chain_runs_end_to_end(self):
        executed = []

        tasks = [
            TestTask(
                "test.a",
                executed,
            ),
            TestTask(
                "test.b",
                executed,
            ),
            TestTask(
                "test.c",
                executed,
            ),
        ]

        runtime = self.create_runtime(
            tasks,
            executed,
        )

        workflow = DefaultWorkflow(
            workflow_id="workflow.chain",
            version="1.0",
            steps=(
                ExecutionStep(
                    step_id="step:a",
                    capability="test.a",
                ),
                ExecutionStep(
                    step_id="step:b",
                    capability="test.b",
                    dependencies=("step:a",),
                ),
                ExecutionStep(
                    step_id="step:c",
                    capability="test.c",
                    dependencies=("step:b",),
                ),
            ),
        )

        runner = DefaultWorkflowRunner(
            runtime
        )

        results = runner.execute(
            workflow
        )

        self.assertEqual(
            executed,
            [
                "step:a",
                "step:b",
                "step:c",
            ],
        )

        self.assertEqual(
            tuple(result.step_id for result in results),
            (
                "step:a",
                "step:b",
                "step:c",
            ),
        )

        self.assertTrue(
            all(
                result.status
                is ExecutionStatus.COMPLETED
                for result in results
            )
        )

    def test_failure_and_dependent_cancellation_end_to_end(self):
        executed = []

        tasks = [
            TestTask(
                "test.a",
                executed,
            ),
            TestTask(
                "test.b",
                executed,
                failing=True,
            ),
            TestTask(
                "test.d",
                executed,
            ),
        ]

        runtime = self.create_runtime(
            tasks,
            executed,
        )

        workflow = DefaultWorkflow(
            workflow_id="workflow.failure",
            version="1.0",
            steps=(
                ExecutionStep(
                    step_id="step:a",
                    capability="test.a",
                ),
                ExecutionStep(
                    step_id="step:b",
                    capability="test.b",
                    dependencies=("step:a",),
                ),
                ExecutionStep(
                    step_id="step:c",
                    capability="test.d",
                    dependencies=("step:b",),
                ),
                ExecutionStep(
                    step_id="step:d",
                    capability="test.d",
                ),
            ),
        )

        results = DefaultWorkflowRunner(
            runtime
        ).execute(workflow)

        by_step = {
            result.step_id: result
            for result in results
        }

        self.assertEqual(
            by_step["step:a"].status,
            ExecutionStatus.COMPLETED,
        )

        self.assertEqual(
            by_step["step:b"].status,
            ExecutionStatus.FAILED,
        )

        self.assertEqual(
            by_step["step:c"].status,
            ExecutionStatus.CANCELLED,
        )

        self.assertEqual(
            by_step["step:d"].status,
            ExecutionStatus.COMPLETED,
        )

        self.assertEqual(
            executed[0],
            "step:a",
)

        self.assertEqual(
            set(executed[1:]),
            {
            "step:b",
            "step:d",
            },
)

    def test_unknown_capability_fails_end_to_end(self):
        executed = []

        runtime = self.create_runtime(
            [],
            executed,
        )

        workflow = DefaultWorkflow(
            workflow_id="workflow.unknown",
            version="1.0",
            steps=(
                ExecutionStep(
                    step_id="step:a",
                    capability="test.unknown",
                ),
            ),
        )

        results = DefaultWorkflowRunner(
            runtime
        ).execute(workflow)

        self.assertEqual(
            results[0].status,
            ExecutionStatus.FAILED,
        )

        self.assertIsNotNone(
            results[0].error,
        )

    def test_engine_is_not_required_end_to_end(self):
        executed = []

        runtime = self.create_runtime(
            [
                TestTask(
                    "test.action",
                    executed,
                )
            ],
            executed,
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

        runner = DefaultWorkflowRunner(
            runtime
        )

        agent = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.RUN_WORKFLOW,
                    workflow_id="workflow.test",
                )
            ),
            FakeWorkflowResolver(workflow),
            runner,
        )

        response = agent.handle(
            AgentRequest(
                request_id="request:test",
                input="run",
            )
        )

        self.assertEqual(
            response.execution_results[0].status,
            ExecutionStatus.COMPLETED,
        )

    def test_intelligence_only_decides_and_does_not_execute_tasks(self):
        executed = []

        intelligence = FakeIntelligence(
            AgentDecision(
                kind=AgentDecisionKind.RUN_WORKFLOW,
                workflow_id="workflow.test",
            )
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

        runtime = self.create_runtime(
            [
                TestTask(
                    "test.action",
                    executed,
                )
            ],
            executed,
        )

        agent = DefaultAgent(
            intelligence,
            FakeWorkflowResolver(workflow),
            DefaultWorkflowRunner(runtime),
        )

        response = agent.handle(
            AgentRequest(
                request_id="request:test",
                input="run",
            )
        )

        self.assertEqual(
            executed,
            ["step:a"],
        )

        self.assertEqual(
            response.execution_results[0].status,
            ExecutionStatus.COMPLETED,
        )

    def test_workflow_definition_is_reusable(self):
        executed = []

        runtime = self.create_runtime(
            [
                TestTask(
                    "test.action",
                    executed,
                )
            ],
            executed,
        )

        workflow = DefaultWorkflow(
            workflow_id="workflow.repeat",
            version="1.0",
            steps=(
                ExecutionStep(
                    step_id="step:a",
                    capability="test.action",
                ),
            ),
        )

        runner = DefaultWorkflowRunner(runtime)

        first = runner.execute(workflow)
        second = runner.execute(workflow)

        self.assertNotEqual(
            first[0].plan_id,
            second[0].plan_id,
        )

        self.assertEqual(
            executed,
            [
                "step:a",
                "step:a",
            ],
        )

    def test_runtime_results_remain_immutable_through_agent(self):
        executed = []

        runtime = self.create_runtime(
            [
                TestTask(
                    "test.action",
                    executed,
                )
            ],
            executed,
        )

        workflow = DefaultWorkflow(
            workflow_id="workflow.immutable",
            version="1.0",
            steps=(
                ExecutionStep(
                    step_id="step:a",
                    capability="test.action",
                ),
            ),
        )

        response = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.RUN_WORKFLOW,
                    workflow_id="workflow.immutable",
                )
            ),
            FakeWorkflowResolver(workflow),
            DefaultWorkflowRunner(runtime),
        ).handle(
            AgentRequest(
                request_id="request:test",
                input="run",
            )
        )

        result = response.execution_results[0]

        with self.assertRaises(AttributeError):
            result.status = ExecutionStatus.FAILED


if __name__ == "__main__":
    unittest.main(verbosity=2)