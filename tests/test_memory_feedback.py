from __future__ import annotations

import unittest

from ai_os.intelligence import (
    DefaultMemoryFeedbackEvaluator,
    MemoryCandidate,
    MemoryFeedbackEvaluatorContract,
    MemoryFeedbackPipeline,
    MemoryFeedbackResult,
    MemoryFeedbackStatus,
    ResultInterpretationPipeline,
)
from ai_os.runtime.contracts import (
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
    ExecutionStep,
    ExecutionError,
)


class TrackingEvaluator:
    def __init__(self, candidates):
        self.candidates = tuple(candidates)
        self.calls = 0
        self.received_sources = []

    def evaluate(self, source):
        self.calls += 1
        self.received_sources.append(source)
        return self.candidates


class WrongEvaluator:
    def evaluate(self, source):
        return ("invalid",)


class MissingEvaluate:
    pass


class RaisingEvaluator:
    def evaluate(self, source):
        raise RuntimeError("memory evaluator failed")


class MemoryFeedbackTests(unittest.TestCase):

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def create_step(
        self,
        step_id="step:test",
        capability="test.action",
    ):
        return ExecutionStep(
            step_id=step_id,
            capability=capability,
        )

    def create_plan(
        self,
        step_ids=("step:test",),
    ):
        return ExecutionPlan(
            plan_id="plan:test",
            steps=tuple(
                self.create_step(
                    step_id=step_id,
                    capability=f"test.action{index}",
                )
                for index, step_id in enumerate(step_ids)
            ),
        )

    def create_execution_result(
        self,
        step_id="step:test",
        status=ExecutionStatus.COMPLETED,
        output=None,
    ):
        error = None

        if status is ExecutionStatus.FAILED:
            error = ExecutionError(
                code="TEST_FAILURE",
                message="test failure",
            )

        return ExecutionResult(
            plan_id="plan:test",
            step_id=step_id,
            status=status,
            output=output,
            error=error,
        )

    def create_interpretation_source(
        self,
        step_ids=("step:test",),
        results=None,
    ):
        plan = self.create_plan(step_ids)

        if results is None:
            results = tuple(
                self.create_execution_result(
                    step_id=step_id,
                    status=ExecutionStatus.COMPLETED,
                    output={"ok": True},
                )
                for step_id in step_ids
            )

        return ResultInterpretationPipeline().run(
            plan,
            results,
        )

    def create_candidate(
        self,
        content="User prefers dark mode",
        category="user_preference",
        confidence=0.95,
        metadata=None,
    ):
        return MemoryCandidate(
            content=content,
            category=category,
            confidence=confidence,
            metadata=metadata or {},
        )

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def test_default_evaluator_matches_contract(self):
        evaluator = DefaultMemoryFeedbackEvaluator()

        self.assertIsInstance(
            evaluator,
            MemoryFeedbackEvaluatorContract,
        )

    def test_missing_evaluate_does_not_match_contract(self):
        self.assertFalse(
            isinstance(
                MissingEvaluate(),
                MemoryFeedbackEvaluatorContract,
            )
        )

    def test_invalid_evaluator_rejected(self):
        with self.assertRaises(TypeError):
            MemoryFeedbackPipeline(
                evaluator=object(),
            )

    # ------------------------------------------------------------------
    # Default conservative behavior
    # ------------------------------------------------------------------

    def test_default_evaluator_returns_no_candidates(self):
        source = self.create_interpretation_source()

        result = MemoryFeedbackPipeline().run(source)

        self.assertEqual(
            result.status,
            MemoryFeedbackStatus.NO_UPDATE,
        )

        self.assertEqual(
            result.candidates,
            (),
        )

    def test_default_evaluator_is_conservative_after_success(self):
        source = self.create_interpretation_source()

        result = MemoryFeedbackPipeline().run(source)

        self.assertEqual(
            result.status,
            MemoryFeedbackStatus.NO_UPDATE,
        )

    def test_default_evaluator_does_not_infer_memory_from_execution(self):
        source = self.create_interpretation_source(
            results=(
                self.create_execution_result(
                    output={
                        "user_preference": "dark_mode",
                    },
                ),
            ),
        )

        result = MemoryFeedbackPipeline().run(source)

        self.assertEqual(
            result.candidates,
            (),
        )

    # ------------------------------------------------------------------
    # Candidate creation
    # ------------------------------------------------------------------

    def test_candidate_is_created(self):
        candidate = self.create_candidate()

        self.assertEqual(
            candidate.content,
            "User prefers dark mode",
        )

        self.assertEqual(
            candidate.category,
            "user_preference",
        )

        self.assertEqual(
            candidate.confidence,
            0.95,
        )

    def test_candidate_confidence_is_normalized_to_float(self):
        candidate = self.create_candidate(
            confidence=1,
        )

        self.assertIsInstance(
            candidate.confidence,
            float,
        )

        self.assertEqual(
            candidate.confidence,
            1.0,
        )

    def test_empty_candidate_content_rejected(self):
        with self.assertRaises(ValueError):
            self.create_candidate(
                content="   ",
            )

    def test_empty_candidate_category_rejected(self):
        with self.assertRaises(ValueError):
            self.create_candidate(
                category="   ",
            )

    def test_invalid_candidate_content_type_rejected(self):
        with self.assertRaises(TypeError):
            self.create_candidate(
                content=123,
            )

    def test_invalid_candidate_category_type_rejected(self):
        with self.assertRaises(TypeError):
            self.create_candidate(
                category=123,
            )

    def test_invalid_confidence_type_rejected(self):
        with self.assertRaises(TypeError):
            self.create_candidate(
                confidence="0.9",
            )

    def test_negative_confidence_rejected(self):
        with self.assertRaises(ValueError):
            self.create_candidate(
                confidence=-0.01,
            )

    def test_confidence_above_one_rejected(self):
        with self.assertRaises(ValueError):
            self.create_candidate(
                confidence=1.01,
            )

    def test_boolean_confidence_rejected(self):
        with self.assertRaises(TypeError):
            self.create_candidate(
                confidence=True,
            )

    # ------------------------------------------------------------------
    # Custom evaluator
    # ------------------------------------------------------------------

    def test_custom_evaluator_is_used(self):
        source = self.create_interpretation_source()

        candidate = self.create_candidate()

        evaluator = TrackingEvaluator(
            (candidate,),
        )

        result = MemoryFeedbackPipeline(
            evaluator=evaluator,
        ).run(source)

        self.assertEqual(
            result.status,
            MemoryFeedbackStatus.CANDIDATES,
        )

        self.assertEqual(
            result.candidates,
            (candidate,),
        )

    def test_evaluator_called_once(self):
        source = self.create_interpretation_source()

        evaluator = TrackingEvaluator(
            (),
        )

        MemoryFeedbackPipeline(
            evaluator=evaluator,
        ).run(source)

        self.assertEqual(
            evaluator.calls,
            1,
        )

    def test_exact_source_is_forwarded(self):
        source = self.create_interpretation_source()

        evaluator = TrackingEvaluator(
            (),
        )

        MemoryFeedbackPipeline(
            evaluator=evaluator,
        ).run(source)

        self.assertIs(
            evaluator.received_sources[0],
            source,
        )

    def test_wrong_evaluator_result_rejected(self):
        source = self.create_interpretation_source()

        with self.assertRaises(TypeError):
            MemoryFeedbackPipeline(
                evaluator=WrongEvaluator(),
            ).run(source)

    def test_evaluator_exception_propagates(self):
        source = self.create_interpretation_source()

        with self.assertRaises(RuntimeError):
            MemoryFeedbackPipeline(
                evaluator=RaisingEvaluator(),
            ).run(source)

    # ------------------------------------------------------------------
    # Multiple candidates
    # ------------------------------------------------------------------

    def test_multiple_candidates_are_preserved(self):
        source = self.create_interpretation_source()

        first = self.create_candidate(
            content="User prefers dark mode",
            category="user_preference",
            confidence=0.95,
        )

        second = self.create_candidate(
            content="User prefers Python",
            category="user_preference",
            confidence=0.9,
        )

        evaluator = TrackingEvaluator(
            (
                first,
                second,
            ),
        )

        result = MemoryFeedbackPipeline(
            evaluator=evaluator,
        ).run(source)

        self.assertEqual(
            result.status,
            MemoryFeedbackStatus.CANDIDATES,
        )

        self.assertEqual(
            result.candidates,
            (
                first,
                second,
            ),
        )

    def test_duplicate_candidates_rejected(self):
        source = self.create_interpretation_source()

        candidate = self.create_candidate()

        evaluator = TrackingEvaluator(
            (
                candidate,
                candidate,
            ),
        )

        with self.assertRaises(ValueError):
            MemoryFeedbackPipeline(
                evaluator=evaluator,
            ).run(source)

    def test_same_content_different_category_is_allowed(self):
        source = self.create_interpretation_source()

        first = self.create_candidate(
            content="Python",
            category="user_preference",
            confidence=0.9,
        )

        second = self.create_candidate(
            content="Python",
            category="project_context",
            confidence=0.8,
        )

        evaluator = TrackingEvaluator(
            (
                first,
                second,
            ),
        )

        result = MemoryFeedbackPipeline(
            evaluator=evaluator,
        ).run(source)

        self.assertEqual(
            result.status,
            MemoryFeedbackStatus.CANDIDATES,
        )

        self.assertEqual(
            len(result.candidates),
            2,
        )

    # ------------------------------------------------------------------
    # Source/result boundary
    # ------------------------------------------------------------------

    def test_invalid_source_rejected(self):
        with self.assertRaises(TypeError):
            MemoryFeedbackPipeline().run(
                object(),
            )

    def test_source_is_preserved_exactly(self):
        source = self.create_interpretation_source()

        evaluator = TrackingEvaluator(
            (),
        )

        result = MemoryFeedbackPipeline(
            evaluator=evaluator,
        ).run(source)

        self.assertIs(
            result.source,
            source,
        )

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------

    def test_candidate_is_immutable(self):
        candidate = self.create_candidate()

        with self.assertRaises(AttributeError):
            candidate.content = "changed"

    def test_candidate_metadata_is_immutable(self):
        candidate = self.create_candidate(
            metadata={
                "source": "test",
            },
        )

        with self.assertRaises(TypeError):
            candidate.metadata["source"] = "changed"

    def test_feedback_result_is_immutable(self):
        source = self.create_interpretation_source()

        result = MemoryFeedbackPipeline().run(source)

        with self.assertRaises(AttributeError):
            result.status = MemoryFeedbackStatus.CANDIDATES

    def test_feedback_result_metadata_is_immutable(self):
        source = self.create_interpretation_source()

        result = MemoryFeedbackResult(
            status=MemoryFeedbackStatus.NO_UPDATE,
            source=source,
            metadata={
                "stage": "test",
            },
        )

        with self.assertRaises(TypeError):
            result.metadata["stage"] = "changed"

    # ------------------------------------------------------------------
    # No persistence
    # ------------------------------------------------------------------

    def test_pipeline_has_no_store_method(self):
        pipeline = MemoryFeedbackPipeline()

        self.assertFalse(
            hasattr(
                pipeline,
                "store",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "persist",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "save",
            )
        )

    def test_evaluator_has_no_storage_api(self):
        evaluator = DefaultMemoryFeedbackEvaluator()

        self.assertFalse(
            hasattr(
                evaluator,
                "store",
            )
        )

        self.assertFalse(
            hasattr(
                evaluator,
                "persist",
            )
        )

    def test_pipeline_has_no_memory_store(self):
        pipeline = MemoryFeedbackPipeline()

        self.assertFalse(
            hasattr(
                pipeline,
                "memory_store",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "database",
            )
        )

    # ------------------------------------------------------------------
    # No execution/replanning/runtime dependencies
    # ------------------------------------------------------------------

    def test_pipeline_has_no_execute(self):
        pipeline = MemoryFeedbackPipeline()

        self.assertFalse(
            hasattr(
                pipeline,
                "execute",
            )
        )

    def test_pipeline_has_no_replan(self):
        pipeline = MemoryFeedbackPipeline()

        self.assertFalse(
            hasattr(
                pipeline,
                "replan",
            )
        )

    def test_pipeline_has_no_runtime_executor(self):
        pipeline = MemoryFeedbackPipeline()

        self.assertFalse(
            hasattr(
                pipeline,
                "runtime_executor",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "executor",
            )
        )

    def test_pipeline_has_no_workflow_runner(self):
        pipeline = MemoryFeedbackPipeline()

        self.assertFalse(
            hasattr(
                pipeline,
                "workflow_runner",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "runner",
            )
        )

    def test_pipeline_has_no_provider(self):
        pipeline = MemoryFeedbackPipeline()

        self.assertFalse(
            hasattr(
                pipeline,
                "provider",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "model",
            )
        )

    # ------------------------------------------------------------------
    # No mutation of source
    # ------------------------------------------------------------------

    def test_source_is_not_mutated(self):
        source = self.create_interpretation_source()

        original_plan = source.plan
        original_results = source.results
        original_interpretation = source.interpretation

        candidate = self.create_candidate()

        MemoryFeedbackPipeline(
            evaluator=TrackingEvaluator(
                (candidate,),
            ),
        ).run(source)

        self.assertIs(
            source.plan,
            original_plan,
        )

        self.assertEqual(
            source.results,
            original_results,
        )

        self.assertIs(
            source.interpretation,
            original_interpretation,
        )

    # ------------------------------------------------------------------
    # Failure / cancelled result behavior
    # ------------------------------------------------------------------

    def test_failed_execution_does_not_automatically_create_memory(self):
        plan = self.create_plan()

        source = ResultInterpretationPipeline().run(
            plan,
            (
                self.create_execution_result(
                    status=ExecutionStatus.FAILED,
                ),
            ),
        )

        result = MemoryFeedbackPipeline().run(source)

        self.assertEqual(
            result.status,
            MemoryFeedbackStatus.NO_UPDATE,
        )

        self.assertEqual(
            result.candidates,
            (),
        )

    def test_cancelled_execution_does_not_automatically_create_memory(self):
        plan = self.create_plan()

        source = ResultInterpretationPipeline().run(
            plan,
            (
                self.create_execution_result(
                    status=ExecutionStatus.CANCELLED,
                ),
            ),
        )

        result = MemoryFeedbackPipeline().run(source)

        self.assertEqual(
            result.status,
            MemoryFeedbackStatus.NO_UPDATE,
        )

        self.assertEqual(
            result.candidates,
            (),
        )

    # ------------------------------------------------------------------
    # Reusability
    # ------------------------------------------------------------------

    def test_default_evaluator_is_reusable(self):
        evaluator = DefaultMemoryFeedbackEvaluator()

        first_source = self.create_interpretation_source(
            step_ids=("step:first",),
            results=(
                self.create_execution_result(
                    step_id="step:first",
                ),
            ),
        )

        second_source = self.create_interpretation_source(
            step_ids=("step:second",),
            results=(
                self.create_execution_result(
                    step_id="step:second",
                ),
            ),
        )

        first = evaluator.evaluate(first_source)
        second = evaluator.evaluate(second_source)

        self.assertEqual(
            first,
            (),
        )

        self.assertEqual(
            second,
            (),
        )

    def test_pipeline_is_reusable(self):
        pipeline = MemoryFeedbackPipeline()

        first_source = self.create_interpretation_source(
            step_ids=("step:first",),
            results=(
                self.create_execution_result(
                    step_id="step:first",
                ),
            ),
        )

        second_source = self.create_interpretation_source(
            step_ids=("step:second",),
            results=(
                self.create_execution_result(
                    step_id="step:second",
                ),
            ),
        )

        first = pipeline.run(first_source)
        second = pipeline.run(second_source)

        self.assertEqual(
            first.status,
            MemoryFeedbackStatus.NO_UPDATE,
        )

        self.assertEqual(
            second.status,
            MemoryFeedbackStatus.NO_UPDATE,
        )

    # ------------------------------------------------------------------
    # Result model
    # ------------------------------------------------------------------

    def test_feedback_result_type_is_correct(self):
        source = self.create_interpretation_source()

        result = MemoryFeedbackPipeline().run(source)

        self.assertIsInstance(
            result,
            MemoryFeedbackResult,
        )

    def test_candidate_result_status_matches_candidates(self):
        source = self.create_interpretation_source()

        candidate = self.create_candidate()

        result = MemoryFeedbackPipeline(
            evaluator=TrackingEvaluator(
                (candidate,),
            ),
        ).run(source)

        self.assertEqual(
            result.status,
            MemoryFeedbackStatus.CANDIDATES,
        )

        self.assertGreater(
            len(result.candidates),
            0,
        )

    def test_empty_candidates_status_is_no_update(self):
        source = self.create_interpretation_source()

        result = MemoryFeedbackPipeline().run(source)

        self.assertEqual(
            result.status,
            MemoryFeedbackStatus.NO_UPDATE,
        )

        self.assertEqual(
            len(result.candidates),
            0,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)