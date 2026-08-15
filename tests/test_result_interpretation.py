from __future__ import annotations

import unittest

from ai_os.intelligence import (
    DefaultResultInterpreter,
    ResultInterpretation,
    ResultInterpretationPipeline,
    ResultInterpretationResult,
    ResultInterpretationStatus,
    ResultInterpreterContract,
)
from ai_os.runtime.contracts import (
    ExecutionError,
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
    ExecutionStep,
)


class TrackingInterpreter:
    def __init__(self, interpretation):
        self.interpretation = interpretation
        self.calls = 0
        self.received_plans = []
        self.received_results = []

    def interpret(self, plan, results):
        self.calls += 1
        results = tuple(results)

        self.received_plans.append(plan)
        self.received_results.append(results)

        return self.interpretation


class WrongInterpreter:
    def interpret(self, plan, results):
        return "invalid"


class MissingInterpret:
    pass


class RaisingInterpreter:
    def interpret(self, plan, results):
        raise RuntimeError("interpreter failed")


class ResultInterpretationTests(unittest.TestCase):

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

    def create_plan(self, step_ids=None):
        if step_ids is None:
            step_ids = ("step:test",)

        steps = tuple(
            self.create_step(
                step_id=step_id,
                capability=f"test.{index}",
            )
            for index, step_id in enumerate(step_ids)
        )

        return ExecutionPlan(
            plan_id="plan:test",
            steps=steps,
        )

    def create_result(
        self,
        step_id="step:test",
        status=ExecutionStatus.COMPLETED,
        output=None,
        error=None,
        plan_id="plan:test",
    ):
        if (
            status is ExecutionStatus.FAILED
            and error is None
        ):
            error = ExecutionError(
                code="TEST_FAILURE",
                message="test failure",
            )

        return ExecutionResult(
            plan_id=plan_id,
            step_id=step_id,
            status=status,
            output=output,
            error=error,
        )

    def completed_result(self, step_id):
        return self.create_result(
            step_id=step_id,
            status=ExecutionStatus.COMPLETED,
            output={"ok": True},
        )

    def failed_result(self, step_id):
        return self.create_result(
            step_id=step_id,
            status=ExecutionStatus.FAILED,
        )

    def cancelled_result(self, step_id):
        return self.create_result(
            step_id=step_id,
            status=ExecutionStatus.CANCELLED,
        )

    def pending_result(self, step_id):
        return self.create_result(
            step_id=step_id,
            status=ExecutionStatus.PENDING,
        )

    def running_result(self, step_id):
        return self.create_result(
            step_id=step_id,
            status=ExecutionStatus.RUNNING,
        )

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def test_default_interpreter_matches_contract(self):
        self.assertIsInstance(
            DefaultResultInterpreter(),
            ResultInterpreterContract,
        )

    def test_missing_interpret_does_not_match_contract(self):
        self.assertFalse(
            isinstance(
                MissingInterpret(),
                ResultInterpreterContract,
            )
        )

    def test_invalid_interpreter_rejected(self):
        with self.assertRaises(TypeError):
            ResultInterpretationPipeline(
                interpreter=object(),
            )

    # ------------------------------------------------------------------
    # All completed
    # ------------------------------------------------------------------

    def test_all_completed(self):
        plan = self.create_plan(
            ("step:a", "step:b")
        )

        results = (
            self.completed_result("step:a"),
            self.completed_result("step:b"),
        )

        result = ResultInterpretationPipeline().run(
            plan,
            results,
        )

        self.assertEqual(
            result.interpretation.status,
            ResultInterpretationStatus.COMPLETED,
        )

        self.assertEqual(
            result.interpretation.total_steps,
            2,
        )

        self.assertEqual(
            result.interpretation.completed_steps,
            2,
        )

        self.assertEqual(
            result.interpretation.failed_steps,
            0,
        )

        self.assertEqual(
            result.interpretation.cancelled_steps,
            0,
        )

        self.assertEqual(
            result.interpretation.pending_steps,
            0,
        )

        self.assertEqual(
            result.interpretation.missing_steps,
            (),
        )

        self.assertFalse(
            result.interpretation.replan_recommended
        )

    # ------------------------------------------------------------------
    # Failure
    # ------------------------------------------------------------------

    def test_one_failed(self):
        plan = self.create_plan(
            ("step:a", "step:b")
        )

        results = (
            self.completed_result("step:a"),
            self.failed_result("step:b"),
        )

        result = ResultInterpretationPipeline().run(
            plan,
            results,
        )

        self.assertEqual(
            result.interpretation.status,
            ResultInterpretationStatus.FAILED,
        )

        self.assertEqual(
            result.interpretation.completed_steps,
            1,
        )

        self.assertEqual(
            result.interpretation.failed_steps,
            1,
        )

        self.assertTrue(
            result.interpretation.replan_recommended
        )

    def test_failed_plus_cancelled_becomes_failed(self):
        plan = self.create_plan(
            ("step:a", "step:b")
        )

        results = (
            self.failed_result("step:a"),
            self.cancelled_result("step:b"),
        )

        result = ResultInterpretationPipeline().run(
            plan,
            results,
        )

        self.assertEqual(
            result.interpretation.status,
            ResultInterpretationStatus.FAILED,
        )

        self.assertEqual(
            result.interpretation.failed_steps,
            1,
        )

        self.assertEqual(
            result.interpretation.cancelled_steps,
            1,
        )

        self.assertTrue(
            result.interpretation.replan_recommended
        )

    # ------------------------------------------------------------------
    # Cancellation
    # ------------------------------------------------------------------

    def test_only_cancelled(self):
        plan = self.create_plan(
            ("step:a", "step:b")
        )

        results = (
            self.cancelled_result("step:a"),
            self.cancelled_result("step:b"),
        )

        result = ResultInterpretationPipeline().run(
            plan,
            results,
        )

        self.assertEqual(
            result.interpretation.status,
            ResultInterpretationStatus.CANCELLED,
        )

        self.assertEqual(
            result.interpretation.cancelled_steps,
            2,
        )

        self.assertFalse(
            result.interpretation.replan_recommended
        )

    # ------------------------------------------------------------------
    # Pending / running
    # ------------------------------------------------------------------

    def test_pending_becomes_incomplete(self):
        plan = self.create_plan()

        result = ResultInterpretationPipeline().run(
            plan,
            (
                self.pending_result("step:test"),
            ),
        )

        self.assertEqual(
            result.interpretation.status,
            ResultInterpretationStatus.INCOMPLETE,
        )

        self.assertEqual(
            result.interpretation.pending_steps,
            1,
        )

    def test_running_becomes_incomplete(self):
        plan = self.create_plan()

        result = ResultInterpretationPipeline().run(
            plan,
            (
                self.running_result("step:test"),
            ),
        )

        self.assertEqual(
            result.interpretation.status,
            ResultInterpretationStatus.INCOMPLETE,
        )

        self.assertEqual(
            result.interpretation.pending_steps,
            1,
        )

    # ------------------------------------------------------------------
    # Missing / empty
    # ------------------------------------------------------------------

    def test_missing_result_becomes_incomplete(self):
        plan = self.create_plan(
            ("step:a", "step:b")
        )

        results = (
            self.completed_result("step:a"),
        )

        result = ResultInterpretationPipeline().run(
            plan,
            results,
        )

        self.assertEqual(
            result.interpretation.status,
            ResultInterpretationStatus.INCOMPLETE,
        )

        self.assertEqual(
            result.interpretation.completed_steps,
            1,
        )

        self.assertEqual(
            result.interpretation.missing_steps,
            ("step:b",),
        )

    def test_empty_result_collection_becomes_incomplete(self):
        plan = self.create_plan()

        result = ResultInterpretationPipeline().run(
            plan,
            (),
        )

        self.assertEqual(
            result.interpretation.status,
            ResultInterpretationStatus.INCOMPLETE,
        )

        self.assertEqual(
            result.interpretation.total_steps,
            1,
        )

        self.assertEqual(
            result.interpretation.missing_steps,
            ("step:test",),
        )

    # ------------------------------------------------------------------
    # Invalid results
    # ------------------------------------------------------------------

    def test_wrong_plan_id_rejected(self):
        plan = self.create_plan()

        result = self.create_result(
            plan_id="plan:wrong",
            step_id="step:test",
        )

        with self.assertRaises(ValueError):
            ResultInterpretationPipeline().run(
                plan,
                (result,),
            )

    def test_unknown_step_id_rejected(self):
        plan = self.create_plan(
            ("step:test",)
        )

        result = self.create_result(
            step_id="step:unknown",
        )

        with self.assertRaises(ValueError):
            ResultInterpretationPipeline().run(
                plan,
                (result,),
            )

    def test_duplicate_step_result_rejected(self):
        plan = self.create_plan(
            ("step:test",)
        )

        first = self.completed_result(
            "step:test"
        )

        second = self.completed_result(
            "step:test"
        )

        with self.assertRaises(ValueError):
            ResultInterpretationPipeline().run(
                plan,
                (first, second),
            )

    def test_wrong_result_type_rejected(self):
        plan = self.create_plan()

        with self.assertRaises(TypeError):
            ResultInterpretationPipeline().run(
                plan,
                ("invalid",),
            )

    def test_results_string_rejected(self):
        plan = self.create_plan()

        with self.assertRaises(TypeError):
            ResultInterpretationPipeline().run(
                plan,
                "invalid",
            )

    def test_invalid_plan_rejected(self):
        with self.assertRaises(TypeError):
            ResultInterpretationPipeline().run(
                object(),
                (),
            )

    # ------------------------------------------------------------------
    # Custom interpreter
    # ------------------------------------------------------------------

    def test_custom_interpreter(self):
        plan = self.create_plan()

        expected = ResultInterpretation(
            status=ResultInterpretationStatus.COMPLETED,
            total_steps=1,
            completed_steps=1,
            failed_steps=0,
            cancelled_steps=0,
            pending_steps=0,
            missing_steps=(),
            replan_recommended=False,
        )

        interpreter = TrackingInterpreter(
            expected
        )

        result = ResultInterpretationPipeline(
            interpreter=interpreter,
        ).run(
            plan,
            (
                self.completed_result("step:test"),
            ),
        )

        self.assertIs(
            result.interpretation,
            expected,
        )

    def test_interpreter_called_once(self):
        plan = self.create_plan()

        expected = ResultInterpretation(
            status=ResultInterpretationStatus.COMPLETED,
            total_steps=1,
            completed_steps=1,
            failed_steps=0,
            cancelled_steps=0,
            pending_steps=0,
            missing_steps=(),
            replan_recommended=False,
        )

        interpreter = TrackingInterpreter(
            expected
        )

        ResultInterpretationPipeline(
            interpreter=interpreter,
        ).run(
            plan,
            (
                self.completed_result("step:test"),
            ),
        )

        self.assertEqual(
            interpreter.calls,
            1,
        )

    def test_custom_interpreter_receives_exact_plan(self):
        plan = self.create_plan()

        expected = ResultInterpretation(
            status=ResultInterpretationStatus.COMPLETED,
            total_steps=1,
            completed_steps=1,
            failed_steps=0,
            cancelled_steps=0,
            pending_steps=0,
            missing_steps=(),
            replan_recommended=False,
        )

        interpreter = TrackingInterpreter(
            expected
        )

        ResultInterpretationPipeline(
            interpreter=interpreter,
        ).run(
            plan,
            (
                self.completed_result("step:test"),
            ),
        )

        self.assertIs(
            interpreter.received_plans[0],
            plan,
        )

    def test_custom_interpreter_receives_exact_results(self):
        plan = self.create_plan()

        execution_result = self.completed_result(
            "step:test"
        )

        expected = ResultInterpretation(
            status=ResultInterpretationStatus.COMPLETED,
            total_steps=1,
            completed_steps=1,
            failed_steps=0,
            cancelled_steps=0,
            pending_steps=0,
            missing_steps=(),
            replan_recommended=False,
        )

        interpreter = TrackingInterpreter(
            expected
        )

        ResultInterpretationPipeline(
            interpreter=interpreter,
        ).run(
            plan,
            (execution_result,),
        )

        received = interpreter.received_results[0]

        self.assertEqual(
            received,
            (execution_result,),
        )

    def test_wrong_interpreter_result_rejected(self):
        with self.assertRaises(TypeError):
            ResultInterpretationPipeline(
                interpreter=WrongInterpreter(),
            ).run(
                self.create_plan(),
                (),
            )

    def test_interpreter_exception_propagates(self):
        with self.assertRaises(RuntimeError):
            ResultInterpretationPipeline(
                interpreter=RaisingInterpreter(),
            ).run(
                self.create_plan(),
                (),
            )

    # ------------------------------------------------------------------
    # Exact plan/results preserved
    # ------------------------------------------------------------------

    def test_exact_plan_preserved(self):
        plan = self.create_plan()

        results = (
            self.completed_result("step:test"),
        )

        result = ResultInterpretationPipeline().run(
            plan,
            results,
        )

        self.assertIs(
            result.plan,
            plan,
        )

    def test_results_preserved(self):
        plan = self.create_plan()

        execution_result = self.completed_result(
            "step:test"
        )

        result = ResultInterpretationPipeline().run(
            plan,
            (execution_result,),
        )

        self.assertEqual(
            result.results,
            (execution_result,),
        )

        self.assertIs(
            result.results[0],
            execution_result,
        )

    # ------------------------------------------------------------------
    # Result immutability
    # ------------------------------------------------------------------

    def test_interpretation_is_immutable(self):
        plan = self.create_plan()

        result = ResultInterpretationPipeline().run(
            plan,
            (
                self.completed_result("step:test"),
            ),
        )

        with self.assertRaises(AttributeError):
            result.interpretation.status = (
                ResultInterpretationStatus.FAILED
            )

    def test_pipeline_result_is_immutable(self):
        plan = self.create_plan()

        result = ResultInterpretationPipeline().run(
            plan,
            (
                self.completed_result("step:test"),
            ),
        )

        with self.assertRaises(AttributeError):
            result.plan = None

    def test_interpretation_metadata_is_immutable(self):
        interpretation = ResultInterpretation(
            status=ResultInterpretationStatus.COMPLETED,
            total_steps=1,
            completed_steps=1,
            failed_steps=0,
            cancelled_steps=0,
            pending_steps=0,
            missing_steps=(),
            replan_recommended=False,
            metadata={"stage": "test"},
        )

        with self.assertRaises(TypeError):
            interpretation.metadata["x"] = 1

    def test_pipeline_metadata_is_immutable(self):
        plan = self.create_plan()

        result = ResultInterpretationResult(
            plan=plan,
            results=(
                self.completed_result("step:test"),
            ),
            interpretation=ResultInterpretation(
                status=(
                    ResultInterpretationStatus.COMPLETED
                ),
                total_steps=1,
                completed_steps=1,
                failed_steps=0,
                cancelled_steps=0,
                pending_steps=0,
                missing_steps=(),
                replan_recommended=False,
            ),
            metadata={"stage": "test"},
        )

        with self.assertRaises(TypeError):
            result.metadata["x"] = 1

    # ------------------------------------------------------------------
    # Boundary enforcement
    # ------------------------------------------------------------------

    def test_no_execute_method(self):
        interpreter = DefaultResultInterpreter()

        self.assertFalse(
            hasattr(
                interpreter,
                "execute",
            )
        )

    def test_no_replan_method(self):
        interpreter = DefaultResultInterpreter()

        self.assertFalse(
            hasattr(
                interpreter,
                "replan",
            )
        )

    def test_no_runtime_executor_dependency(self):
        interpreter = DefaultResultInterpreter()

        self.assertFalse(
            hasattr(
                interpreter,
                "runtime_executor",
            )
        )

        self.assertFalse(
            hasattr(
                interpreter,
                "executor",
            )
        )

    def test_no_workflow_runner_dependency(self):
        interpreter = DefaultResultInterpreter()

        self.assertFalse(
            hasattr(
                interpreter,
                "workflow_runner",
            )
        )

        self.assertFalse(
            hasattr(
                interpreter,
                "runner",
            )
        )

    def test_no_scheduler_dependency(self):
        interpreter = DefaultResultInterpreter()

        self.assertFalse(
            hasattr(
                interpreter,
                "scheduler",
            )
        )

    def test_no_memory_dependency(self):
        interpreter = DefaultResultInterpreter()

        self.assertFalse(
            hasattr(
                interpreter,
                "memory",
            )
        )

        self.assertFalse(
            hasattr(
                interpreter,
                "memory_store",
            )
        )

    def test_no_provider_dependency(self):
        interpreter = DefaultResultInterpreter()

        self.assertFalse(
            hasattr(
                interpreter,
                "provider",
            )
        )

        self.assertFalse(
            hasattr(
                interpreter,
                "model",
            )
        )

    # ------------------------------------------------------------------
    # No mutation
    # ------------------------------------------------------------------

    def test_plan_is_not_mutated(self):
        plan = self.create_plan(
            ("step:a", "step:b")
        )

        original_steps = plan.steps

        ResultInterpretationPipeline().run(
            plan,
            (
                self.completed_result("step:a"),
            ),
        )

        self.assertEqual(
            plan.steps,
            original_steps,
        )

    def test_execution_result_is_not_mutated(self):
        execution_result = self.completed_result(
            "step:test"
        )

        original_output = execution_result.output
        original_status = execution_result.status

        ResultInterpretationPipeline().run(
            self.create_plan(),
            (execution_result,),
        )

        self.assertEqual(
            execution_result.output,
            original_output,
        )

        self.assertEqual(
            execution_result.status,
            original_status,
        )

    # ------------------------------------------------------------------
    # Reusable interpreter
    # ------------------------------------------------------------------

    def test_interpreter_is_reusable(self):
        interpreter = DefaultResultInterpreter()

        first_plan = self.create_plan(
            ("step:first",)
        )

        second_plan = self.create_plan(
            ("step:second",)
        )

        first = interpreter.interpret(
            first_plan,
            (
                self.completed_result("step:first"),
            ),
        )

        second = interpreter.interpret(
            second_plan,
            (
                self.cancelled_result("step:second"),
            ),
        )

        self.assertEqual(
            first.status,
            ResultInterpretationStatus.COMPLETED,
        )

        self.assertEqual(
            second.status,
            ResultInterpretationStatus.CANCELLED,
        )

    def test_pipeline_is_reusable(self):
        pipeline = ResultInterpretationPipeline()

        first_plan = self.create_plan(
            ("step:first",)
        )

        second_plan = self.create_plan(
            ("step:second",)
        )

        first = pipeline.run(
            first_plan,
            (
                self.completed_result("step:first"),
            ),
        )

        second = pipeline.run(
            second_plan,
            (
                self.completed_result("step:second"),
            ),
        )

        self.assertEqual(
            first.interpretation.status,
            ResultInterpretationStatus.COMPLETED,
        )

        self.assertEqual(
            second.interpretation.status,
            ResultInterpretationStatus.COMPLETED,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)