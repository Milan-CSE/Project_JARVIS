import unittest

from ai_os.runtime.agents import (
    Agent,
    AgentDecision,
    AgentDecisionKind,
    AgentRequest,
    AgentResponse,
    AgentResolutionError,
    DefaultAgent,
    Intelligence,
    WorkflowResolver,
)
from ai_os.runtime.cancellation import CancellationSource
from ai_os.runtime.contracts import (
    ExecutionResult,
    ExecutionStatus,
    ExecutionStep,
)
from ai_os.runtime.workflows import (
    DefaultWorkflow,
    WorkflowRunner,
)


class FakeIntelligence:

    def __init__(self, decision):
        self.decision = decision

    def decide(
        self,
        request,
        cancellation_token=None,
    ):
        return self.decision


class FakeWorkflowResolver:

    def __init__(self, workflow=None):
        self.workflow = workflow
        self.received_ids = []

    def resolve(self, workflow_id):
        self.received_ids.append(workflow_id)
        return self.workflow


class FakeWorkflowRunner:

    def __init__(self):
        self.calls = []

    def execute(
        self,
        workflow,
        parameters=None,
        cancellation_token=None,
    ):
        self.calls.append(
            (
                workflow,
                parameters,
                cancellation_token,
            )
        )

        return (
            ExecutionResult(
                plan_id="plan:test",
                step_id="step:a",
                status=ExecutionStatus.COMPLETED,
                output={"ok": True},
            ),
        )


class MissingDecideIntelligence:
    pass


class MissingResolveWorkflow:
    pass


class MissingWorkflowRunner:
    pass


class AgentTests(unittest.TestCase):

    def create_request(self):
        return AgentRequest(
            request_id="request:test",
            input="hello",
        )

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

    def test_intelligence_protocol_is_structural(self):
        intelligence = FakeIntelligence(
            AgentDecision(
                kind=AgentDecisionKind.RESPOND,
                message="hello",
            )
        )

        self.assertIsInstance(
            intelligence,
            Intelligence,
        )

    def test_agent_protocol_is_structural(self):
        agent = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.RESPOND,
                    message="hello",
                )
            ),
            FakeWorkflowResolver(),
            FakeWorkflowRunner(),
        )

        self.assertIsInstance(
            agent,
            Agent,
        )

    def test_invalid_intelligence_rejected(self):
        with self.assertRaises(TypeError):
            DefaultAgent(
                MissingDecideIntelligence(),
                FakeWorkflowResolver(),
                FakeWorkflowRunner(),
            )

    def test_invalid_workflow_resolver_rejected(self):
        with self.assertRaises(TypeError):
            DefaultAgent(
                FakeIntelligence(
                    AgentDecision(
                        kind=AgentDecisionKind.RESPOND,
                        message="hello",
                    )
                ),
                MissingResolveWorkflow(),
                FakeWorkflowRunner(),
            )

    def test_invalid_workflow_runner_rejected(self):
        with self.assertRaises(TypeError):
            DefaultAgent(
                FakeIntelligence(
                    AgentDecision(
                        kind=AgentDecisionKind.RESPOND,
                        message="hello",
                    )
                ),
                FakeWorkflowResolver(),
                MissingWorkflowRunner(),
            )

    def test_respond_decision_does_not_execute_workflow(self):
        runner = FakeWorkflowRunner()

        agent = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.RESPOND,
                    message="hello",
                )
            ),
            FakeWorkflowResolver(),
            runner,
        )

        response = agent.handle(
            self.create_request()
        )

        self.assertEqual(
            response.message,
            "hello",
        )

        self.assertEqual(
            runner.calls,
            [],
        )

    def test_ask_clarification_does_not_execute_workflow(self):
        runner = FakeWorkflowRunner()

        agent = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.ASK_CLARIFICATION,
                    message="Please clarify.",
                )
            ),
            FakeWorkflowResolver(),
            runner,
        )

        response = agent.handle(
            self.create_request()
        )

        self.assertEqual(
            response.message,
            "Please clarify.",
        )

        self.assertEqual(
            runner.calls,
            [],
        )

    def test_decline_does_not_execute_workflow(self):
        runner = FakeWorkflowRunner()

        agent = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.DECLINE,
                    message="I cannot do that.",
                )
            ),
            FakeWorkflowResolver(),
            runner,
        )

        response = agent.handle(
            self.create_request()
        )

        self.assertEqual(
            response.message,
            "I cannot do that.",
        )

        self.assertEqual(
            runner.calls,
            [],
        )

    def test_run_workflow_resolves_and_runs_workflow(self):
        workflow = self.create_workflow()
        resolver = FakeWorkflowResolver(workflow)
        runner = FakeWorkflowRunner()

        agent = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.RUN_WORKFLOW,
                    workflow_id="workflow.test",
                    parameters={
                        "date": "today",
                    },
                )
            ),
            resolver,
            runner,
        )

        response = agent.handle(
            self.create_request()
        )

        self.assertEqual(
            resolver.received_ids,
            ["workflow.test"],
        )

        self.assertEqual(
            len(runner.calls),
            1,
        )

        self.assertEqual(
            runner.calls[0][1],
            {"date": "today"},
        )

        self.assertEqual(
            response.execution_results[0].status,
            ExecutionStatus.COMPLETED,
        )

    def test_unknown_workflow_rejected(self):
        agent = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.RUN_WORKFLOW,
                    workflow_id="workflow.unknown",
                )
            ),
            FakeWorkflowResolver(None),
            FakeWorkflowRunner(),
        )

        with self.assertRaises(
            AgentResolutionError
        ):
            agent.handle(
                self.create_request()
            )

    def test_runtime_results_are_not_mutated(self):
        workflow = self.create_workflow()
        runner = FakeWorkflowRunner()

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
            self.create_request()
        )

        result = response.execution_results[0]

        self.assertIsInstance(
            result,
            ExecutionResult,
        )

        self.assertEqual(
            result.status,
            ExecutionStatus.COMPLETED,
        )

    def test_agent_does_not_expose_runtime_internals(self):
        agent = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.RESPOND,
                    message="hello",
                )
            ),
            FakeWorkflowResolver(),
            FakeWorkflowRunner(),
        )

        self.assertFalse(
            hasattr(agent, "scheduler")
        )

        self.assertFalse(
            hasattr(agent, "task_executor")
        )

        self.assertFalse(
            hasattr(agent, "registry")
        )

    def test_agent_does_not_require_engine(self):
        agent = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.RESPOND,
                    message="hello",
                )
            ),
            FakeWorkflowResolver(),
            FakeWorkflowRunner(),
        )

        self.assertFalse(
            hasattr(agent, "engine")
        )

    def test_agent_does_not_require_intelligence_internally(self):
        # This test means the Agent does not expose reasoning methods;
        # Intelligence remains an injected boundary.
        agent = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.RESPOND,
                    message="hello",
                )
            ),
            FakeWorkflowResolver(),
            FakeWorkflowRunner(),
        )

        self.assertFalse(
            hasattr(agent, "reason")
        )

        self.assertFalse(
            hasattr(agent, "think")
        )

    def test_cancellation_prevents_execution_after_decision(self):
        source = CancellationSource()
        source.cancel()

        runner = FakeWorkflowRunner()

        agent = DefaultAgent(
            FakeIntelligence(
                AgentDecision(
                    kind=AgentDecisionKind.RUN_WORKFLOW,
                    workflow_id="workflow.test",
                )
            ),
            FakeWorkflowResolver(
                self.create_workflow()
            ),
            runner,
        )

        response = agent.handle(
            self.create_request(),
            source.token,
        )

        self.assertEqual(
            runner.calls,
            [],
        )

        self.assertEqual(
            response.metadata["termination_reason"],
            "explicit_cancellation",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)