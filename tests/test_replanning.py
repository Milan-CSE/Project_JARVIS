from __future__ import annotations

import unittest

from ai_os.intelligence import (
    BoundedReplanningPipeline,
    PlanValidationPipeline,
    ReplanRequest,
    ReplannerContract,
    ReplanningResult,
    ReplanningStatus,
)
from ai_os.runtime.contracts import (
    ExecutionPlan,
    ExecutionStep,
)


class TrackingReplanner:
    def __init__(self, replacement):
        self.replacement = replacement
        self.calls = 0
        self.received_plans = []
        self.received_requests = []

    def replan(self, current_plan, request):
        self.calls += 1
        self.received_plans.append(current_plan)
        self.received_requests.append(request)
        return self.replacement


class WrongReplanner:
    def replan(self, current_plan, request):
        return "invalid"


class RaisingReplanner:
    def replan(self, current_plan, request):
        raise RuntimeError("replanner failed")


class MissingReplan:
    pass


class ReplanningTests(unittest.TestCase):

    def create_step(
        self,
        step_id="step:test",
        capability="test.capability",
    ):
        return ExecutionStep(
            step_id=step_id,
            capability=capability,
        )

    def create_plan(
        self,
        plan_id="plan:test",
        step_id="step:test",
        capability="test.capability",
    ):
        return ExecutionPlan(
            plan_id=plan_id,
            steps=(
                self.create_step(
                    step_id=step_id,
                    capability=capability,
                ),
            ),
        )

    def create_request(
        self,
        attempt=1,
        max_attempts=3,
        reason="execution_failure",
    ):
        return ReplanRequest(
            reason=reason,
            attempt=attempt,
            max_attempts=max_attempts,
        )

    # ---------------------------------------------------------------
    # Contract
    # ---------------------------------------------------------------

    def test_valid_replanner_matches_contract(self):
        current = self.create_plan()
        replacement = self.create_plan(
            plan_id="plan:replacement",
            step_id="step:new",
        )

        self.assertIsInstance(
            TrackingReplanner(replacement),
            ReplannerContract,
        )

    def test_missing_replan_does_not_match_contract(self):
        self.assertFalse(
            isinstance(
                MissingReplan(),
                ReplannerContract,
            )
        )

    def test_invalid_replanner_rejected(self):
        with self.assertRaises(TypeError):
            BoundedReplanningPipeline(
                object()
            )

    # ---------------------------------------------------------------
    # Request
    # ---------------------------------------------------------------

    def test_request_is_immutable(self):
        request = self.create_request()

        with self.assertRaises(AttributeError):
            request.reason = "changed"

    def test_request_metadata_is_immutable(self):
        request = ReplanRequest(
            reason="failure",
            attempt=1,
            max_attempts=3,
            metadata={"x": 1},
        )

        with self.assertRaises(TypeError):
            request.metadata["x"] = 2

    def test_empty_reason_rejected(self):
        with self.assertRaises(ValueError):
            ReplanRequest(
                reason="   ",
                attempt=1,
                max_attempts=3,
            )

    def test_invalid_attempt_type_rejected(self):
        with self.assertRaises(TypeError):
            ReplanRequest(
                reason="failure",
                attempt="1",
                max_attempts=3,
            )

    def test_invalid_attempt_value_rejected(self):
        with self.assertRaises(ValueError):
            ReplanRequest(
                reason="failure",
                attempt=0,
                max_attempts=3,
            )

    def test_invalid_max_attempts_type_rejected(self):
        with self.assertRaises(TypeError):
            ReplanRequest(
                reason="failure",
                attempt=1,
                max_attempts="3",
            )

    def test_invalid_max_attempts_value_rejected(self):
        with self.assertRaises(ValueError):
            ReplanRequest(
                reason="failure",
                attempt=1,
                max_attempts=0,
            )

    # ---------------------------------------------------------------
    # Successful replanning
    # ---------------------------------------------------------------

    def test_replanning_produces_replacement_plan(self):
        current = self.create_plan()

        replacement = self.create_plan(
            plan_id="plan:replacement",
            step_id="step:new",
        )

        replanner = TrackingReplanner(
            replacement
        )

        result = BoundedReplanningPipeline(
            replanner
        ).run(
            current,
            self.create_request(),
        )

        self.assertEqual(
            result.status,
            ReplanningStatus.REPLANNED,
        )

        self.assertIs(
            result.current_plan,
            current,
        )

        self.assertIs(
            result.replacement_plan,
            replacement,
        )

    def test_replanner_called_once(self):
        current = self.create_plan()

        replacement = self.create_plan(
            plan_id="plan:replacement",
        )

        replanner = TrackingReplanner(
            replacement
        )

        BoundedReplanningPipeline(
            replanner
        ).run(
            current,
            self.create_request(),
        )

        self.assertEqual(
            replanner.calls,
            1,
        )

    def test_exact_current_plan_is_forwarded(self):
        current = self.create_plan()

        replacement = self.create_plan(
            plan_id="plan:replacement",
        )

        replanner = TrackingReplanner(
            replacement
        )

        BoundedReplanningPipeline(
            replanner
        ).run(
            current,
            self.create_request(),
        )

        self.assertIs(
            replanner.received_plans[0],
            current,
        )

    def test_exact_request_is_forwarded(self):
        current = self.create_plan()

        replacement = self.create_plan(
            plan_id="plan:replacement",
        )

        request = self.create_request()

        replanner = TrackingReplanner(
            replacement
        )

        BoundedReplanningPipeline(
            replanner
        ).run(
            current,
            request,
        )

        self.assertIs(
            replanner.received_requests[0],
            request,
        )

    # ---------------------------------------------------------------
    # Bounds
    # ---------------------------------------------------------------

    def test_limit_is_enforced(self):
        current = self.create_plan()

        replacement = self.create_plan(
            plan_id="plan:replacement",
        )

        replanner = TrackingReplanner(
            replacement
        )

        request = self.create_request(
            attempt=4,
            max_attempts=3,
        )

        result = BoundedReplanningPipeline(
            replanner
        ).run(
            current,
            request,
        )

        self.assertEqual(
            result.status,
            ReplanningStatus.LIMIT_REACHED,
        )

        self.assertIsNone(
            result.replacement_plan,
        )

        self.assertEqual(
            replanner.calls,
            0,
        )

    def test_last_allowed_attempt_runs(self):
        current = self.create_plan()

        replacement = self.create_plan(
            plan_id="plan:last",
        )

        replanner = TrackingReplanner(
            replacement
        )

        result = BoundedReplanningPipeline(
            replanner
        ).run(
            current,
            self.create_request(
                attempt=3,
                max_attempts=3,
            ),
        )

        self.assertEqual(
            result.status,
            ReplanningStatus.REPLANNED,
        )

        self.assertEqual(
            replanner.calls,
            1,
        )

    # ---------------------------------------------------------------
    # Replacement integrity
    # ---------------------------------------------------------------

    def test_same_object_rejected(self):
        current = self.create_plan()

        replanner = TrackingReplanner(
            current
        )

        with self.assertRaises(ValueError):
            BoundedReplanningPipeline(
                replanner
            ).run(
                current,
                self.create_request(),
            )

    def test_same_plan_id_rejected(self):
        current = self.create_plan()

        replacement = self.create_plan(
            plan_id=current.plan_id,
            step_id="step:new",
        )

        replanner = TrackingReplanner(
            replacement
        )

        with self.assertRaises(ValueError):
            BoundedReplanningPipeline(
                replanner
            ).run(
                current,
                self.create_request(),
            )

    def test_wrong_replanner_result_rejected(self):
        with self.assertRaises(TypeError):
            BoundedReplanningPipeline(
                WrongReplanner()
            ).run(
                self.create_plan(),
                self.create_request(),
            )

    def test_replanner_exception_propagates(self):
        with self.assertRaises(RuntimeError):
            BoundedReplanningPipeline(
                RaisingReplanner()
            ).run(
                self.create_plan(),
                self.create_request(),
            )

    # ---------------------------------------------------------------
    # Input boundary
    # ---------------------------------------------------------------

    def test_invalid_current_plan_rejected(self):
        replacement = self.create_plan(
            plan_id="plan:replacement",
        )

        with self.assertRaises(TypeError):
            BoundedReplanningPipeline(
                TrackingReplanner(replacement)
            ).run(
                object(),
                self.create_request(),
            )

    def test_invalid_request_rejected(self):
        replacement = self.create_plan(
            plan_id="plan:replacement",
        )

        with self.assertRaises(TypeError):
            BoundedReplanningPipeline(
                TrackingReplanner(replacement)
            ).run(
                self.create_plan(),
                object(),
            )

    # ---------------------------------------------------------------
    # Immutability / reuse
    # ---------------------------------------------------------------

    def test_result_is_immutable(self):
        current = self.create_plan()

        replacement = self.create_plan(
            plan_id="plan:replacement",
        )

        result = BoundedReplanningPipeline(
            TrackingReplanner(replacement)
        ).run(
            current,
            self.create_request(),
        )

        with self.assertRaises(AttributeError):
            result.status = ReplanningStatus.LIMIT_REACHED

    def test_pipeline_is_reusable(self):
        first = self.create_plan(
            plan_id="plan:first",
        )

        second = self.create_plan(
            plan_id="plan:second",
        )

        first_replacement = self.create_plan(
            plan_id="plan:first:new",
        )

        second_replacement = self.create_plan(
            plan_id="plan:second:new",
        )

        first_result = BoundedReplanningPipeline(
            TrackingReplanner(first_replacement)
        ).run(
            first,
            self.create_request(),
        )

        second_result = BoundedReplanningPipeline(
            TrackingReplanner(second_replacement)
        ).run(
            second,
            self.create_request(),
        )

        self.assertIs(
            first_result.replacement_plan,
            first_replacement,
        )

        self.assertIs(
            second_result.replacement_plan,
            second_replacement,
        )

    # ---------------------------------------------------------------
    # Boundary enforcement
    # ---------------------------------------------------------------

    def test_pipeline_does_not_execute(self):
        pipeline = BoundedReplanningPipeline(
            TrackingReplanner(
                self.create_plan(
                    plan_id="plan:replacement"
                )
            )
        )

        self.assertFalse(
            hasattr(pipeline, "execute")
        )

        self.assertFalse(
            hasattr(pipeline, "execute_plan")
        )

    def test_pipeline_does_not_schedule(self):
        pipeline = BoundedReplanningPipeline(
            TrackingReplanner(
                self.create_plan(
                    plan_id="plan:replacement"
                )
            )
        )

        self.assertFalse(
            hasattr(pipeline, "schedule")
        )

        self.assertFalse(
            hasattr(pipeline, "scheduler")
        )

    def test_pipeline_does_not_use_workflow_runner(self):
        pipeline = BoundedReplanningPipeline(
            TrackingReplanner(
                self.create_plan(
                    plan_id="plan:replacement"
                )
            )
        )

        self.assertFalse(
            hasattr(pipeline, "workflow_runner")
        )

        self.assertFalse(
            hasattr(pipeline, "runner")
        )

    def test_replanning_result_does_not_execute_replacement(self):
        current = self.create_plan()

        replacement = self.create_plan(
            plan_id="plan:replacement"
        )

        result = BoundedReplanningPipeline(
            TrackingReplanner(replacement)
        ).run(
            current,
            self.create_request(),
        )

        self.assertIs(
            result.replacement_plan,
            replacement,
        )

        self.assertFalse(
            hasattr(
                result.replacement_plan,
                "execution_result",
            )
        )

    # ---------------------------------------------------------------
    # Explicit separation from result interpretation
    # ---------------------------------------------------------------

    def test_replanning_does_not_accept_execution_result(self):
        pipeline = BoundedReplanningPipeline(
            TrackingReplanner(
                self.create_plan(
                    plan_id="plan:replacement"
                )
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "interpret_result",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "process_execution_result",
            )
        )

    # ---------------------------------------------------------------
    # Result model
    # ---------------------------------------------------------------

    def test_result_type_is_correct(self):
        current = self.create_plan()

        replacement = self.create_plan(
            plan_id="plan:replacement"
        )

        result = BoundedReplanningPipeline(
            TrackingReplanner(replacement)
        ).run(
            current,
            self.create_request(),
        )

        self.assertIsInstance(
            result,
            ReplanningResult,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)