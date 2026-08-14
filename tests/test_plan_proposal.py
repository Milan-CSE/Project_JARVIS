import unittest

from ai_os.intelligence import (
    PlanProposal,
    PlanStepProposal,
    Proposal,
    ProposalKind,
    WorkflowProposal,
)


class PlanProposalTests(unittest.TestCase):

    def create_step(
        self,
        step_id="step:a",
        capability="test.action",
        input=None,
        dependencies=(),
    ):
        return PlanStepProposal(
            step_id=step_id,
            capability=capability,
            input=input,
            dependencies=dependencies,
        )

    def create_plan(
        self,
        steps=(),
        proposal_id="proposal:plan",
        decision_id="decision:test",
    ):
        return PlanProposal(
            proposal_id=proposal_id,
            decision_id=decision_id,
            kind=ProposalKind.PLAN,
            steps=steps,
        )

    def test_plan_step_proposal_can_be_created(self):
        step = self.create_step()

        self.assertEqual(
            step.step_id,
            "step:a",
        )

        self.assertEqual(
            step.capability,
            "test.action",
        )

    def test_plan_proposal_can_be_created(self):
        step = self.create_step()

        proposal = self.create_plan(
            steps=(step,),
        )

        self.assertEqual(
            proposal.proposal_id,
            "proposal:plan",
        )

        self.assertEqual(
            proposal.decision_id,
            "decision:test",
        )

        self.assertEqual(
            proposal.kind,
            ProposalKind.PLAN,
        )

        self.assertEqual(
            proposal.steps,
            (step,),
        )

    def test_plan_kind_accepts_string(self):
        proposal = PlanProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind="plan",
        )

        self.assertEqual(
            proposal.kind,
            ProposalKind.PLAN,
        )

    def test_plan_steps_are_tuple(self):
        step = self.create_step()

        proposal = PlanProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.PLAN,
            steps=[step],
        )

        self.assertIsInstance(
            proposal.steps,
            tuple,
        )

    def test_empty_plan_is_allowed_as_untrusted_proposal(self):
        proposal = self.create_plan()

        self.assertEqual(
            proposal.steps,
            (),
        )

    def test_empty_step_id_rejected(self):
        with self.assertRaises(ValueError):
            self.create_step(
                step_id="",
            )

    def test_whitespace_step_id_rejected(self):
        with self.assertRaises(ValueError):
            self.create_step(
                step_id="   ",
            )

    def test_invalid_step_id_type_rejected(self):
        with self.assertRaises(TypeError):
            self.create_step(
                step_id=123,
            )

    def test_empty_capability_rejected(self):
        with self.assertRaises(ValueError):
            self.create_step(
                capability="",
            )

    def test_whitespace_capability_rejected(self):
        with self.assertRaises(ValueError):
            self.create_step(
                capability="   ",
            )

    def test_invalid_capability_type_rejected(self):
        with self.assertRaises(TypeError):
            self.create_step(
                capability=123,
            )

    def test_invalid_dependency_rejected(self):
        with self.assertRaises(TypeError):
            self.create_step(
                dependencies=("step:a", 123),
            )

    def test_empty_dependency_rejected(self):
        with self.assertRaises(TypeError):
            self.create_step(
                dependencies=("step:a", ""),
            )

    def test_duplicate_step_ids_rejected(self):
        first = self.create_step(
            step_id="step:a",
        )

        second = self.create_step(
            step_id="step:a",
            capability="test.other",
        )

        with self.assertRaises(ValueError):
            self.create_plan(
                steps=(
                    first,
                    second,
                ),
            )

    def test_different_step_ids_are_allowed(self):
        first = self.create_step(
            step_id="step:a",
        )

        second = self.create_step(
            step_id="step:b",
            capability="test.other",
        )

        proposal = self.create_plan(
            steps=(
                first,
                second,
            ),
        )

        self.assertEqual(
            len(proposal.steps),
            2,
        )

    def test_dependencies_are_preserved(self):
        step = self.create_step(
            step_id="step:b",
            dependencies=("step:a",),
        )

        self.assertEqual(
            step.dependencies,
            ("step:a",),
        )

    def test_missing_dependency_reference_allowed(self):
        step = self.create_step(
            step_id="step:b",
            dependencies=("step:missing",),
        )

        proposal = self.create_plan(
            steps=(step,),
        )

        self.assertEqual(
            proposal.steps[0].dependencies,
            ("step:missing",),
        )

    def test_cycle_is_allowed_at_construction(self):
        first = self.create_step(
            step_id="step:a",
            dependencies=("step:b",),
        )

        second = self.create_step(
            step_id="step:b",
            dependencies=("step:a",),
        )

        proposal = self.create_plan(
            steps=(
                first,
                second,
            ),
        )

        self.assertEqual(
            len(proposal.steps),
            2,
        )

    def test_unknown_capability_allowed_at_construction(self):
        step = self.create_step(
            capability="future.unknown.capability",
        )

        proposal = self.create_plan(
            steps=(step,),
        )

        self.assertEqual(
            proposal.steps[0].capability,
            "future.unknown.capability",
        )

    def test_nested_input_is_immutable(self):
        step = self.create_step(
            input={
                "options": {
                    "format": "pdf",
                },
                "tags": [
                    "sales",
                    "daily",
                ],
            },
        )

        with self.assertRaises(TypeError):
            step.input["options"]["format"] = "csv"

        with self.assertRaises(AttributeError):
            step.input["tags"].append("urgent")

    def test_constraints_are_immutable(self):
        step = PlanStepProposal(
            step_id="step:a",
            capability="test.action",
            constraints={
                "timeout": 10,
            },
        )

        with self.assertRaises(TypeError):
            step.constraints["timeout"] = 20

    def test_metadata_is_immutable(self):
        step = PlanStepProposal(
            step_id="step:a",
            capability="test.action",
            metadata={
                "source": "intelligence",
            },
        )

        with self.assertRaises(TypeError):
            step.metadata["source"] = "other"

    def test_plan_proposal_is_immutable(self):
        proposal = self.create_plan()

        with self.assertRaises(AttributeError):
            proposal.proposal_id = "changed"

    def test_plan_step_proposal_is_immutable(self):
        step = self.create_step()

        with self.assertRaises(AttributeError):
            step.step_id = "changed"

    def test_plan_does_not_contain_execution_step(self):
        step = self.create_step()
        proposal = self.create_plan(
            steps=(step,),
        )

        from ai_os.runtime.contracts import ExecutionStep

        self.assertNotIsInstance(
            proposal.steps[0],
            ExecutionStep,
        )

    def test_plan_step_does_not_execute(self):
        step = self.create_step()

        self.assertFalse(
            hasattr(step, "execute")
        )

        self.assertFalse(
            hasattr(step, "run")
        )

    def test_plan_proposal_does_not_execute(self):
        proposal = self.create_plan()

        self.assertFalse(
            hasattr(proposal, "execute")
        )

        self.assertFalse(
            hasattr(proposal, "run")
        )

    def test_plan_does_not_require_runtime(self):
        proposal = self.create_plan()

        self.assertFalse(
            hasattr(proposal, "runtime")
        )

        self.assertFalse(
            hasattr(proposal, "scheduler")
        )

        self.assertFalse(
            hasattr(proposal, "task_executor")
        )

        self.assertFalse(
            hasattr(proposal, "task_registry")
        )

    def test_plan_step_does_not_require_task(self):
        step = self.create_step()

        self.assertFalse(
            hasattr(step, "task")
        )

        self.assertFalse(
            hasattr(step, "task_executor")
        )

    def test_plan_does_not_contain_workflow_object(self):
        proposal = self.create_plan()

        self.assertFalse(
            hasattr(proposal, "workflow")
        )

    def test_plan_is_a_proposal(self):
        proposal = self.create_plan()

        self.assertIsInstance(
            proposal,
            Proposal,
        )

    def test_wrong_kind_rejected(self):
        with self.assertRaises(ValueError):
            PlanProposal(
                proposal_id="proposal:test",
                decision_id="decision:test",
                kind=ProposalKind.WORKFLOW,
            )

    def test_workflow_proposal_remains_separate(self):
        workflow = WorkflowProposal(
            proposal_id="proposal:workflow",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
        )

        self.assertIsInstance(
            workflow,
            WorkflowProposal,
        )

        self.assertNotIsInstance(
            workflow,
            PlanProposal,
        )

    def test_plan_step_metadata_is_preserved(self):
        step = PlanStepProposal(
            step_id="step:a",
            capability="test.action",
            metadata={
                "source": "planner",
            },
        )

        self.assertEqual(
            step.metadata["source"],
            "planner",
        )

    def test_plan_step_constraints_are_preserved(self):
        step = PlanStepProposal(
            step_id="step:a",
            capability="test.action",
            constraints={
                "max_retries": 2,
            },
        )

        self.assertEqual(
            step.constraints["max_retries"],
            2,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)