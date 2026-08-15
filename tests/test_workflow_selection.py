from __future__ import annotations

import unittest

from ai_os.intelligence import (
    DefaultWorkflowSelector,
    PlanValidationPipeline,
    WorkflowSelectionPipeline,
    WorkflowSelectionResult,
    WorkflowSelectionStatus,
    WorkflowSelectorContract,
)
from ai_os.runtime.contracts import ExecutionPlan, ExecutionStep
from ai_os.runtime.workflows.workflow import Workflow
from ai_os.runtime.workflows.workflow_impl import DefaultWorkflow


class TrackingSelector:
    def __init__(self, result):
        self.result = result
        self.calls = 0
        self.received_plans = []
        self.received_workflows = []

    def select(
        self,
        plan,
        workflows,
        requested_workflow_id=None,
    ):
        self.calls += 1
        self.received_plans.append(plan)
        self.received_workflows.append(tuple(workflows))
        return self.result


class WrongSelector:
    def select(
        self,
        plan,
        workflows,
        requested_workflow_id=None,
    ):
        return "invalid"


class MissingSelect:
    pass


class WorkflowSelectionTests(unittest.TestCase):

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
        metadata=None,
    ):
        return ExecutionPlan(
            plan_id=plan_id,
            steps=(
                self.create_step(),
            ),
            metadata=metadata or {},
        )

    def create_workflow(
        self,
        workflow_id="workflow:test",
        version="1.0",
    ):
        return DefaultWorkflow(
            workflow_id=workflow_id,
            version=version,
            steps=(
                self.create_step(),
            ),
        )

    def validated_plan(self, metadata=None):
        plan = self.create_plan(
            metadata=metadata
        )

        return PlanValidationPipeline().run(
            plan
        )

    # ---------------------------------------------------------------
    # Contract
    # ---------------------------------------------------------------

    def test_default_selector_matches_contract(self):
        self.assertIsInstance(
            DefaultWorkflowSelector(),
            WorkflowSelectorContract,
        )

    def test_missing_select_does_not_match_contract(self):
        self.assertFalse(
            isinstance(
                MissingSelect(),
                WorkflowSelectorContract,
            )
        )

    def test_invalid_selector_rejected(self):
        with self.assertRaises(TypeError):
            WorkflowSelectionPipeline(
                selector=object()
            )

    # ---------------------------------------------------------------
    # Explicit selection
    # ---------------------------------------------------------------

    def test_explicit_workflow_id_selects_exact_workflow(self):
        first = self.create_workflow(
            "workflow:first"
        )

        second = self.create_workflow(
            "workflow:second"
        )

        result = WorkflowSelectionPipeline().run(
            self.validated_plan(),
            (first, second),
            requested_workflow_id="workflow:second",
        )

        self.assertEqual(
            result.status,
            WorkflowSelectionStatus.SELECTED,
        )

        self.assertIs(
            result.selected_workflow,
            second,
        )

    def test_missing_requested_workflow_returns_not_found(self):
        workflow = self.create_workflow(
            "workflow:one"
        )

        result = WorkflowSelectionPipeline().run(
            self.validated_plan(),
            (workflow,),
            requested_workflow_id="workflow:missing",
        )

        self.assertEqual(
            result.status,
            WorkflowSelectionStatus.NOT_FOUND,
        )

        self.assertIsNone(
            result.selected_workflow
        )

    # ---------------------------------------------------------------
    # Plan metadata routing
    # ---------------------------------------------------------------

    def test_plan_metadata_workflow_id_is_used(self):
        workflow = self.create_workflow(
            "workflow:metadata"
        )

        result = WorkflowSelectionPipeline().run(
            self.validated_plan(
                metadata={
                    "workflow_id": "workflow:metadata"
                }
            ),
            (workflow,),
        )

        self.assertEqual(
            result.status,
            WorkflowSelectionStatus.SELECTED,
        )

        self.assertIs(
            result.selected_workflow,
            workflow,
        )

    def test_explicit_id_overrides_plan_metadata(self):
        first = self.create_workflow(
            "workflow:metadata"
        )

        second = self.create_workflow(
            "workflow:explicit"
        )

        result = WorkflowSelectionPipeline().run(
            self.validated_plan(
                metadata={
                    "workflow_id": "workflow:metadata"
                }
            ),
            (first, second),
            requested_workflow_id="workflow:explicit",
        )

        self.assertIs(
            result.selected_workflow,
            second,
        )

    # ---------------------------------------------------------------
    # Candidate cardinality
    # ---------------------------------------------------------------

    def test_zero_candidates_returns_not_found(self):
        result = WorkflowSelectionPipeline().run(
            self.validated_plan(),
            (),
        )

        self.assertEqual(
            result.status,
            WorkflowSelectionStatus.NOT_FOUND,
        )

    def test_one_candidate_is_selected(self):
        workflow = self.create_workflow()

        result = WorkflowSelectionPipeline().run(
            self.validated_plan(),
            (workflow,),
        )

        self.assertEqual(
            result.status,
            WorkflowSelectionStatus.SELECTED,
        )

        self.assertIs(
            result.selected_workflow,
            workflow,
        )

    def test_multiple_candidates_without_identity_are_ambiguous(self):
        first = self.create_workflow(
            "workflow:first"
        )

        second = self.create_workflow(
            "workflow:second"
        )

        result = WorkflowSelectionPipeline().run(
            self.validated_plan(),
            (first, second),
        )

        self.assertEqual(
            result.status,
            WorkflowSelectionStatus.AMBIGUOUS,
        )

        self.assertIsNone(
            result.selected_workflow
        )

    def test_duplicate_workflow_id_is_ambiguous(self):
        first = self.create_workflow(
            "workflow:test",
            "1.0",
        )

        second = self.create_workflow(
            "workflow:test",
            "2.0",
        )

        result = WorkflowSelectionPipeline().run(
            self.validated_plan(),
            (first, second),
            requested_workflow_id="workflow:test",
        )

        self.assertEqual(
            result.status,
            WorkflowSelectionStatus.AMBIGUOUS,
        )

        self.assertIsNone(
            result.selected_workflow
        )

    # ---------------------------------------------------------------
    # Version behavior
    # ---------------------------------------------------------------

    def test_version_is_not_used_as_implicit_ranking(self):
        older = self.create_workflow(
            "workflow:test",
            "1.0",
        )

        newer = self.create_workflow(
            "workflow:test",
            "99.0",
        )

        result = WorkflowSelectionPipeline().run(
            self.validated_plan(),
            (older, newer),
        )

        self.assertEqual(
            result.status,
            WorkflowSelectionStatus.AMBIGUOUS,
        )

    # ---------------------------------------------------------------
    # Validation boundary
    # ---------------------------------------------------------------

    def test_invalid_plan_validation_is_rejected(self):
        plan = self.create_plan()

        # Construct a rejected result directly so the test does not
        # violate the frozen ExecutionPlan constructor contract.
        from ai_os.intelligence import (
            PlanValidationIssue,
            PlanValidationResult,
            PlanValidationStatus,
        )

        rejected = PlanValidationResult(
            status=PlanValidationStatus.REJECTED,
            plan=plan,
            issues=(
                PlanValidationIssue(
                    code="TEST_REJECTION",
                    message="test rejection",
                ),
            ),
        )

        with self.assertRaises(ValueError):
            WorkflowSelectionPipeline().run(
                rejected,
                (),
            )

    def test_invalid_validation_type_rejected(self):
        with self.assertRaises(TypeError):
            WorkflowSelectionPipeline().run(
                object(),
                (),
            )

    # ---------------------------------------------------------------
    # Candidate validation
    # ---------------------------------------------------------------

    def test_invalid_workflow_candidate_rejected(self):
        with self.assertRaises(TypeError):
            WorkflowSelectionPipeline().run(
                self.validated_plan(),
                (object(),),
            )

    def test_empty_requested_id_rejected(self):
        workflow = self.create_workflow()

        with self.assertRaises(ValueError):
            WorkflowSelectionPipeline().run(
                self.validated_plan(),
                (workflow,),
                requested_workflow_id="   ",
            )

    def test_invalid_requested_id_type_rejected(self):
        workflow = self.create_workflow()

        with self.assertRaises(TypeError):
            WorkflowSelectionPipeline().run(
                self.validated_plan(),
                (workflow,),
                requested_workflow_id=123,
            )

    def test_invalid_metadata_workflow_id_type_rejected(self):
        with self.assertRaises(TypeError):
            WorkflowSelectionPipeline().run(
                self.validated_plan(
                    metadata={
                        "workflow_id": 123
                    }
                ),
                (self.create_workflow(),),
            )

    # ---------------------------------------------------------------
    # Delegation
    # ---------------------------------------------------------------

    def test_custom_selector_is_called_once(self):
        validation = self.validated_plan()
        workflow = self.create_workflow()

        expected = WorkflowSelectionResult(
            status=WorkflowSelectionStatus.SELECTED,
            plan=validation.plan,
            selected_workflow=workflow,
        )

        selector = TrackingSelector(
            expected
        )

        result = WorkflowSelectionPipeline(
            selector=selector
        ).run(
            validation,
            (workflow,),
        )

        self.assertEqual(
            selector.calls,
            1,
        )

        self.assertIs(
            result,
            expected,
        )

        self.assertIs(
            selector.received_plans[0],
            validation.plan,
        )

    def test_wrong_selector_result_rejected(self):
        with self.assertRaises(TypeError):
            WorkflowSelectionPipeline(
                selector=WrongSelector()
            ).run(
                self.validated_plan(),
                (),
            )

    def test_selector_must_preserve_exact_plan(self):
        validation = self.validated_plan()

        different_plan = self.create_plan(
            "plan:different"
        )

        selector = TrackingSelector(
            WorkflowSelectionResult(
                status=WorkflowSelectionStatus.NOT_FOUND,
                plan=different_plan,
            )
        )

        with self.assertRaises(ValueError):
            WorkflowSelectionPipeline(
                selector=selector
            ).run(
                validation,
                (),
            )

    # ---------------------------------------------------------------
    # Immutability / preservation
    # ---------------------------------------------------------------

    def test_result_is_immutable(self):
        workflow = self.create_workflow()

        result = WorkflowSelectionPipeline().run(
            self.validated_plan(),
            (workflow,),
        )

        with self.assertRaises(AttributeError):
            result.status = WorkflowSelectionStatus.NOT_FOUND

    def test_result_metadata_is_immutable(self):
        workflow = self.create_workflow()

        result = WorkflowSelectionPipeline().run(
            self.validated_plan(),
            (workflow,),
        )

        with self.assertRaises(TypeError):
            result.metadata["changed"] = True

    def test_exact_plan_is_preserved(self):
        validation = self.validated_plan()
        workflow = self.create_workflow()

        result = WorkflowSelectionPipeline().run(
            validation,
            (workflow,),
        )

        self.assertIs(
            result.plan,
            validation.plan,
        )

    def test_exact_workflow_is_preserved(self):
        workflow = self.create_workflow()

        result = WorkflowSelectionPipeline().run(
            self.validated_plan(),
            (workflow,),
        )

        self.assertIs(
            result.selected_workflow,
            workflow,
        )

    # ---------------------------------------------------------------
    # Boundary enforcement
    # ---------------------------------------------------------------

    def test_selector_does_not_execute(self):
        selector = DefaultWorkflowSelector()

        self.assertFalse(
            hasattr(selector, "execute")
        )

        self.assertFalse(
            hasattr(selector, "run")
        )

    def test_selector_does_not_build_steps(self):
        selector = DefaultWorkflowSelector()

        self.assertFalse(
            hasattr(selector, "build_steps")
        )

    def test_selector_does_not_use_runner(self):
        selector = DefaultWorkflowSelector()

        self.assertFalse(
            hasattr(selector, "runner")
        )

        self.assertFalse(
            hasattr(selector, "workflow_runner")
        )

    def test_selector_does_not_replan(self):
        selector = DefaultWorkflowSelector()

        self.assertFalse(
            hasattr(selector, "replan")
        )

    def test_pipeline_has_no_execution_api(self):
        pipeline = WorkflowSelectionPipeline()

        self.assertFalse(
            hasattr(pipeline, "execute")
        )

        self.assertFalse(
            hasattr(pipeline, "run_task")
        )

    def test_pipeline_is_reusable(self):
        pipeline = WorkflowSelectionPipeline()

        first = self.create_workflow(
            "workflow:first"
        )

        second = self.create_workflow(
            "workflow:second"
        )

        first_result = pipeline.run(
            self.validated_plan(),
            (first,),
        )

        second_result = pipeline.run(
            self.validated_plan(),
            (second,),
        )

        self.assertIs(
            first_result.selected_workflow,
            first,
        )

        self.assertIs(
            second_result.selected_workflow,
            second,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)