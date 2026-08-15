from __future__ import annotations

import unittest

from ai_os.intelligence import (
    DefaultPlanValidator,
    PlanValidationIssue,
    PlanValidationPipeline,
    PlanValidationResult,
    PlanValidationStatus,
    PlanValidatorContract,
)
from ai_os.runtime.contracts import (
    ExecutionPlan,
    ExecutionStep,
)


class TrackingValidator:
    def __init__(self, result):
        self.result = result
        self.calls = 0
        self.received_plans = []

    def validate(self, plan):
        self.calls += 1
        self.received_plans.append(plan)
        return self.result


class WrongValidatorResult:
    def validate(self, plan):
        return "invalid"


class RaisingValidator:
    def validate(self, plan):
        raise RuntimeError("validator failed")


class MissingValidate:
    pass


class PlanValidationTests(unittest.TestCase):

    def create_step(
        self,
        step_id="step:test",
        capability="test.capability",
        dependencies=(),
    ):
        return ExecutionStep(
            step_id=step_id,
            capability=capability,
            dependencies=dependencies,
        )

    def create_plan(
        self,
        plan_id="plan:test",
        steps=None,
    ):
        if steps is None:
            steps = (
                self.create_step(),
            )

        return ExecutionPlan(
            plan_id=plan_id,
            steps=steps,
        )

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def test_default_validator_matches_contract(self):
        validator = DefaultPlanValidator()

        self.assertIsInstance(
            validator,
            PlanValidatorContract,
        )

    def test_invalid_validator_does_not_match_contract(self):
        self.assertFalse(
            isinstance(
                object(),
                PlanValidatorContract,
            )
        )

    def test_missing_validate_does_not_match_contract(self):
        self.assertFalse(
            isinstance(
                MissingValidate(),
                PlanValidatorContract,
            )
        )

    def test_pipeline_rejects_invalid_validator(self):
        with self.assertRaises(TypeError):
            PlanValidationPipeline(
                validator=object(),
            )

    # ------------------------------------------------------------------
    # Valid plans
    # ------------------------------------------------------------------

    def test_single_step_plan_is_valid(self):
        plan = self.create_plan()

        result = PlanValidationPipeline().run(plan)

        self.assertIsInstance(
            result,
            PlanValidationResult,
        )

        self.assertEqual(
            result.status,
            PlanValidationStatus.VALID,
        )

        self.assertEqual(
            result.issues,
            (),
        )

    def test_empty_plan_is_rejected_by_execution_plan_contract(self):
        with self.assertRaises(Exception):
            ExecutionPlan(
                plan_id="plan:test",
                steps=(),
            )

    def test_multiple_independent_steps_are_valid(self):
        first = self.create_step(
            step_id="step:a",
            capability="test.a",
        )

        second = self.create_step(
            step_id="step:b",
            capability="test.b",
        )

        plan = self.create_plan(
            steps=(first, second),
        )

        result = PlanValidationPipeline().run(plan)

        self.assertEqual(
            result.status,
            PlanValidationStatus.VALID,
        )

    def test_valid_dependency_chain_is_valid(self):
        first = self.create_step(
            step_id="step:a",
            capability="test.a",
        )

        second = self.create_step(
            step_id="step:b",
            capability="test.b",
            dependencies=("step:a",),
        )

        third = self.create_step(
            step_id="step:c",
            capability="test.c",
            dependencies=("step:b",),
        )

        plan = self.create_plan(
            steps=(
                first,
                second,
                third,
            ),
        )

        result = PlanValidationPipeline().run(plan)

        self.assertEqual(
            result.status,
            PlanValidationStatus.VALID,
        )

        self.assertEqual(
            result.issues,
            (),
        )

    def test_valid_parallel_dependencies_are_valid(self):
        root = self.create_step(
            step_id="step:a",
            capability="test.a",
        )

        branch_one = self.create_step(
            step_id="step:b",
            capability="test.b",
            dependencies=("step:a",),
        )

        branch_two = self.create_step(
            step_id="step:c",
            capability="test.c",
            dependencies=("step:a",),
        )

        plan = self.create_plan(
            steps=(
                root,
                branch_one,
                branch_two,
            ),
        )

        result = PlanValidationPipeline().run(plan)

        self.assertEqual(
            result.status,
            PlanValidationStatus.VALID,
        )

    # ------------------------------------------------------------------
    # Step identity
    # ------------------------------------------------------------------

    def test_duplicate_step_id_is_rejected_by_execution_plan_contract(self):
        first = ExecutionStep(
            step_id="step:a",
            capability="test.a",
        )

        second = ExecutionStep(
            step_id="step:a",
            capability="test.b",
        )

        with self.assertRaises(Exception):
            ExecutionPlan(
                plan_id="plan:test",
                steps=(
                    first,
                    second,
                ),
            )

    def test_empty_step_id_is_rejected_by_execution_step_contract(self):
        with self.assertRaises(Exception):
            ExecutionStep(
                step_id="",
                capability="test.capability",
            )

    # ------------------------------------------------------------------
    # Capability
    # ------------------------------------------------------------------

    def test_empty_capability_is_rejected_by_execution_step_contract(self):
        with self.assertRaises(Exception):
            ExecutionStep(
                step_id="step:test",
                capability="",
            )

    # ------------------------------------------------------------------
    # Dependency validation
    # ------------------------------------------------------------------

    def test_unknown_dependency_is_rejected_by_execution_plan_contract(self):
        step = ExecutionStep(
            step_id="step:a",
            capability="test.capability",
        )

        invalid_step = ExecutionStep(
            step_id="step:b",
            capability="test.other",
            dependencies=("step:missing",),
        )

        with self.assertRaises(Exception):
            ExecutionPlan(
                plan_id="plan:test",
                steps=(
                    step,
                    invalid_step,
                ),
            )

    def test_self_dependency_is_rejected_by_execution_step_contract(self):
        with self.assertRaises(Exception):
            ExecutionStep(
                step_id="step:a",
                capability="test.capability",
                dependencies=("step:a",),
            )

    def test_duplicate_dependency_is_rejected_by_execution_step_contract(self):
        with self.assertRaises(Exception):
            ExecutionStep(
                step_id="step:b",
                capability="test.capability",
                dependencies=(
                    "step:a",
                    "step:a",
                ),
            )

    def test_dependency_cycle_is_rejected_by_execution_plan_contract(self):
        first = ExecutionStep(
            step_id="step:a",
            capability="test.a",
            dependencies=("step:b",),
        )

        second = ExecutionStep(
            step_id="step:b",
            capability="test.b",
            dependencies=("step:a",),
        )

        with self.assertRaises(Exception):
            ExecutionPlan(
                plan_id="plan:test",
                steps=(
                    first,
                    second,
                ),
            )

    def test_long_dependency_chain_is_valid(self):
        steps = []

        previous = None

        for index in range(20):
            step_id = f"step:{index}"

            dependencies = (
                ()
                if previous is None
                else (previous,)
            )

            steps.append(
                self.create_step(
                    step_id=step_id,
                    capability=f"test.{index}",
                    dependencies=dependencies,
                )
            )

            previous = step_id

        plan = self.create_plan(
            steps=tuple(steps),
        )

        result = PlanValidationPipeline().run(plan)

        self.assertEqual(
            result.status,
            PlanValidationStatus.VALID,
        )

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------

    def test_invalid_plan_rejected(self):
        with self.assertRaises(TypeError):
            PlanValidationPipeline().run(
                object()
            )

    def test_none_plan_rejected(self):
        with self.assertRaises(TypeError):
            PlanValidationPipeline().run(
                None
            )

    # ------------------------------------------------------------------
    # Validator delegation
    # ------------------------------------------------------------------

    def test_custom_validator_is_called_once(self):
        plan = self.create_plan()

        expected = PlanValidationResult(
            status=PlanValidationStatus.VALID,
            plan=plan,
        )

        validator = TrackingValidator(
            expected
        )

        result = PlanValidationPipeline(
            validator=validator,
        ).run(plan)

        self.assertEqual(
            validator.calls,
            1,
        )

        self.assertIs(
            validator.received_plans[0],
            plan,
        )

        self.assertIs(
            result,
            expected,
        )

    def test_validator_receives_exact_plan(self):
        plan = self.create_plan()

        expected = PlanValidationResult(
            status=PlanValidationStatus.VALID,
            plan=plan,
        )

        validator = TrackingValidator(
            expected
        )

        PlanValidationPipeline(
            validator=validator,
        ).run(plan)

        self.assertIs(
            validator.received_plans[0],
            plan,
        )

    def test_wrong_validator_result_is_rejected(self):
        with self.assertRaises(TypeError):
            PlanValidationPipeline(
                validator=WrongValidatorResult()
            ).run(
                self.create_plan()
            )

    def test_validator_exception_propagates(self):
        with self.assertRaises(RuntimeError):
            PlanValidationPipeline(
                validator=RaisingValidator()
            ).run(
                self.create_plan()
            )

    def test_validator_must_preserve_exact_plan(self):
        plan = self.create_plan()

        different_plan = self.create_plan(
            plan_id="plan:different",
        )

        validator = TrackingValidator(
            PlanValidationResult(
                status=PlanValidationStatus.VALID,
                plan=different_plan,
            )
        )

        with self.assertRaises(ValueError):
            PlanValidationPipeline(
                validator=validator
            ).run(plan)

    # ------------------------------------------------------------------
    # Result correctness
    # ------------------------------------------------------------------

    def test_result_preserves_exact_plan(self):
        plan = self.create_plan()

        result = PlanValidationPipeline().run(plan)

        self.assertIs(
            result.plan,
            plan,
        )

    def test_rejected_result_contains_issues(self):
        plan = self.create_plan()

        issue = PlanValidationIssue(
            code="TEST_REJECTION",
            message="test rejection",
            field="plan",
        )

        result = PlanValidationResult(
            status=PlanValidationStatus.REJECTED,
            plan=plan,
            issues=(issue,),
        )

        self.assertEqual(
            result.status,
            PlanValidationStatus.REJECTED,
        )

        self.assertGreater(
            len(result.issues),
            0,
        )

    def test_issue_is_correct_type(self):
        issue = PlanValidationIssue(
            code="TEST",
            message="test issue",
            field="plan.steps",
        )

        self.assertIsInstance(
            issue,
            PlanValidationIssue,
        )

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------

    def test_result_is_immutable(self):
        result = PlanValidationPipeline().run(
            self.create_plan()
        )

        with self.assertRaises(AttributeError):
            result.status = PlanValidationStatus.REJECTED

    def test_issue_is_immutable(self):
        issue = PlanValidationIssue(
            code="TEST",
            message="test issue",
        )

        with self.assertRaises(AttributeError):
            issue.message = "changed"

        def test_result_metadata_is_immutable(self):
            result = PlanValidationResult(
                status=PlanValidationStatus.VALID,
                plan=self.create_plan(),
                metadata={"stage": "test"},
            )

            with self.assertRaises(TypeError):
                result.metadata["changed"] = True

    def test_issue_metadata_is_immutable(self):
        issue = PlanValidationIssue(
            code="TEST",
            message="test",
            metadata={"x": 1},
        )

        with self.assertRaises(TypeError):
            issue.metadata["x"] = 2

    # ------------------------------------------------------------------
    # Boundary enforcement
    # ------------------------------------------------------------------

    def test_validator_does_not_execute(self):
        validator = DefaultPlanValidator()

        self.assertFalse(
            hasattr(
                validator,
                "execute",
            )
        )

    def test_validator_does_not_schedule(self):
        validator = DefaultPlanValidator()

        self.assertFalse(
            hasattr(
                validator,
                "schedule",
            )
        )

        self.assertFalse(
            hasattr(
                validator,
                "get_ready_steps",
            )
        )

    def test_validator_does_not_replan(self):
        validator = DefaultPlanValidator()

        self.assertFalse(
            hasattr(
                validator,
                "replan",
            )
        )

    def test_validator_does_not_select_workflow(self):
        validator = DefaultPlanValidator()

        self.assertFalse(
            hasattr(
                validator,
                "select_workflow",
            )
        )

    def test_validator_does_not_require_runtime(self):
        validator = DefaultPlanValidator()

        self.assertFalse(
            hasattr(
                validator,
                "runtime",
            )
        )

        self.assertFalse(
            hasattr(
                validator,
                "executor",
            )
        )

    def test_validator_does_not_require_scheduler(self):
        validator = DefaultPlanValidator()

        self.assertFalse(
            hasattr(
                validator,
                "scheduler",
            )
        )

    def test_validator_does_not_require_task_registry(self):
        validator = DefaultPlanValidator()

        self.assertFalse(
            hasattr(
                validator,
                "task_registry",
            )
        )

    def test_pipeline_does_not_execute_plan(self):
        pipeline = PlanValidationPipeline()

        self.assertFalse(
            hasattr(
                pipeline,
                "execute",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "run_plan",
            )
        )

    # ------------------------------------------------------------------
    # Non-mutation / reusability
    # ------------------------------------------------------------------

    def test_plan_is_not_mutated(self):
        first = self.create_step(
            step_id="step:a",
        )

        second = self.create_step(
            step_id="step:b",
            dependencies=("step:a",),
        )

        plan = self.create_plan(
            steps=(
                first,
                second,
            ),
        )

        original_steps = plan.steps

        result = PlanValidationPipeline().run(plan)

        self.assertEqual(
            plan.steps,
            original_steps,
        )

        self.assertEqual(
            result.plan.steps,
            original_steps,
        )

    def test_validator_is_reusable(self):
        validator = DefaultPlanValidator()

        first = validator.validate(
            self.create_plan(
                plan_id="plan:first",
            )
        )

        second = validator.validate(
            self.create_plan(
                plan_id="plan:second",
            )
        )

        self.assertEqual(
            first.status,
            PlanValidationStatus.VALID,
        )

        self.assertEqual(
            second.status,
            PlanValidationStatus.VALID,
        )

        self.assertEqual(
            first.plan.plan_id,
            "plan:first",
        )

        self.assertEqual(
            second.plan.plan_id,
            "plan:second",
        )

    def test_pipeline_is_reusable(self):
        pipeline = PlanValidationPipeline()

        first = pipeline.run(
            self.create_plan(
                plan_id="plan:first",
            )
        )

        second = pipeline.run(
            self.create_plan(
                plan_id="plan:second",
            )
        )

        self.assertEqual(
            first.status,
            PlanValidationStatus.VALID,
        )

        self.assertEqual(
            second.status,
            PlanValidationStatus.VALID,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)