import json
import unittest

from ai_os.runtime.contracts import (
    ExecutionError,
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
    ExecutionStep,
    artifact_ref,
    step_output_ref,
)
from ai_os.runtime.contracts.errors import InvalidPlanError, InvalidResultError


class RuntimeContractTests(unittest.TestCase):
    def test_simple_plan(self):
        step = ExecutionStep(
            step_id="S1",
            capability="web.search",
            input={"query": "Python 3.13"},
        )
        plan = ExecutionPlan(plan_id="P1", steps=(step,))

        self.assertEqual(plan.plan_id, "P1")
        self.assertEqual(plan.steps[0].capability, "web.search")

    def test_sequential_data_reference(self):
        search = ExecutionStep(
            step_id="S1",
            capability="web.search",
            input={"query": "Python 3.13"},
        )
        email = ExecutionStep(
            step_id="S2",
            capability="email.send",
            input={"body": step_output_ref("S1")},
            dependencies=("S1",),
        )
        plan = ExecutionPlan(plan_id="P1", steps=(search, email))

        self.assertEqual(
            plan.steps[1].input["body"]["$ref"],
            "steps.S1.output",
        )

    def test_parallel_steps_are_allowed(self):
        first = ExecutionStep("S1", "weather.get")
        second = ExecutionStep("S2", "news.search")
        plan = ExecutionPlan("P1", (first, second))

        self.assertEqual(plan.steps[0].dependencies, ())
        self.assertEqual(plan.steps[1].dependencies, ())

    def test_unknown_dependency_is_rejected(self):
        step = ExecutionStep("S1", "web.search", dependencies=("S9",))
        with self.assertRaises(InvalidPlanError):
            ExecutionPlan("P1", (step,))

    def test_dependency_cycle_is_rejected(self):
        first = ExecutionStep("S1", "web.search", dependencies=("S2",))
        second = ExecutionStep("S2", "email.send", dependencies=("S1",))

        with self.assertRaises(InvalidPlanError):
            ExecutionPlan("P1", (first, second))

    def test_failure_result_requires_error(self):
        with self.assertRaises(InvalidResultError):
            ExecutionResult(
                plan_id="P1",
                step_id="S1",
                status=ExecutionStatus.FAILED,
            )

    def test_failed_result(self):
        result = ExecutionResult(
            plan_id="P1",
            step_id="S1",
            status=ExecutionStatus.FAILED,
            error=ExecutionError(
                code="CAPABILITY_NOT_FOUND",
                message="Capability is unavailable",
            ),
        )

        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertEqual(result.error.code, "CAPABILITY_NOT_FOUND")

    def test_cancelled_result(self):
        result = ExecutionResult(
            plan_id="P1",
            step_id="S1",
            status=ExecutionStatus.CANCELLED,
        )
        self.assertEqual(result.status, ExecutionStatus.CANCELLED)

    def test_artifact_reference_is_serializable(self):
        step = ExecutionStep(
            "S1",
            "document.summarize",
            input={"document": artifact_ref("artifact-123")},
        )
        plan = ExecutionPlan("P1", (step,))

        payload = json.loads(plan.to_json())
        self.assertEqual(
            payload["steps"][0]["input"]["document"]["type"],
            "artifact",
        )
        self.assertEqual(
            payload["steps"][0]["input"]["document"]["id"],
            "artifact-123",
        )

    def test_plan_round_trip(self):
        step = ExecutionStep(
            "S1",
            "web.search",
            input={"query": "AI-OS"},
            constraints={"timeout_seconds": 30, "max_retries": 2},
            metadata={"source": "test"},
        )
        plan = ExecutionPlan("P1", (step,), metadata={"source": "unit-test"})

        restored = ExecutionPlan.from_json(plan.to_json())

        self.assertEqual(restored.to_dict(), plan.to_dict())

    def test_result_round_trip(self):
        result = ExecutionResult(
            plan_id="P1",
            step_id="S1",
            status=ExecutionStatus.COMPLETED,
            output={"answer": "done"},
        )

        restored = ExecutionResult.from_json(result.to_json())

        self.assertEqual(restored.to_dict(), result.to_dict())

    def test_contracts_are_immutable(self):
        step = ExecutionStep("S1", "web.search", input={"query": "test"})
        plan = ExecutionPlan("P1", (step,))

        with self.assertRaises((AttributeError, TypeError)):
            step.capability = "email.send"

        with self.assertRaises(TypeError):
            step.input["query"] = "changed"

        with self.assertRaises((AttributeError, TypeError)):
            plan.plan_id = "P2"

    def test_invalid_capability_is_rejected(self):
        with self.assertRaises(ValueError):
            ExecutionStep("S1", "Web Search")

    def test_non_json_input_is_rejected(self):
        with self.assertRaises(TypeError):
            ExecutionStep("S1", "web.search", input={"bad": object()})


if __name__ == "__main__":
    unittest.main(verbosity=2)
