import unittest

from ai_os.intelligence import (
    Proposal,
    ProposalKind,
    WorkflowProposal,
)


class ProposalTests(unittest.TestCase):

    def test_workflow_proposal_can_be_created(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.sales_report",
        )

        self.assertEqual(
            proposal.proposal_id,
            "proposal:test",
        )

        self.assertEqual(
            proposal.decision_id,
            "decision:test",
        )

        self.assertEqual(
            proposal.kind,
            ProposalKind.WORKFLOW,
        )

        self.assertEqual(
            proposal.workflow_id,
            "workflow.sales_report",
        )

    def test_workflow_proposal_accepts_string_kind(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind="workflow",
            workflow_id="workflow.test",
        )

        self.assertEqual(
            proposal.kind,
            ProposalKind.WORKFLOW,
        )

    def test_base_proposal_can_be_created(self):
        proposal = Proposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
        )

        self.assertEqual(
            proposal.kind,
            ProposalKind.WORKFLOW,
        )

    def test_empty_proposal_id_rejected(self):
        with self.assertRaises(ValueError):
            Proposal(
                proposal_id="",
                decision_id="decision:test",
                kind=ProposalKind.WORKFLOW,
            )

    def test_empty_decision_id_rejected(self):
        with self.assertRaises(ValueError):
            Proposal(
                proposal_id="proposal:test",
                decision_id="",
                kind=ProposalKind.WORKFLOW,
            )

    def test_empty_workflow_id_rejected(self):
        with self.assertRaises(ValueError):
            WorkflowProposal(
                proposal_id="proposal:test",
                decision_id="decision:test",
                kind=ProposalKind.WORKFLOW,
                workflow_id="",
            )

    def test_invalid_workflow_id_type_rejected(self):
        with self.assertRaises(TypeError):
            WorkflowProposal(
                proposal_id="proposal:test",
                decision_id="decision:test",
                kind=ProposalKind.WORKFLOW,
                workflow_id=123,
            )

    def test_invalid_kind_rejected(self):
        with self.assertRaises(ValueError):
            Proposal(
                proposal_id="proposal:test",
                decision_id="decision:test",
                kind="delete_everything",
            )

    def test_workflow_proposal_rejects_wrong_kind(self):
        with self.assertRaises(ValueError):
            WorkflowProposal(
                proposal_id="proposal:test",
                decision_id="decision:test",
                kind="not_a_workflow",
                workflow_id="workflow.test",
            )

    def test_metadata_defaults_to_empty(self):
        proposal = Proposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
        )

        self.assertEqual(
            dict(proposal.metadata),
            {},
        )

    def test_parameters_default_to_empty(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
        )

        self.assertEqual(
            dict(proposal.parameters),
            {},
        )

    def test_metadata_is_immutable(self):
        proposal = Proposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            metadata={
                "source": "test",
            },
        )

        with self.assertRaises(TypeError):
            proposal.metadata["source"] = "changed"

    def test_parameters_are_immutable(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
            parameters={
                "date": "today",
            },
        )

        with self.assertRaises(TypeError):
            proposal.parameters["date"] = "tomorrow"

    def test_nested_parameters_are_immutable(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
            parameters={
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
            proposal.parameters["options"]["format"] = "csv"

        with self.assertRaises(AttributeError):
            proposal.parameters["tags"].append("urgent")

    def test_nested_metadata_is_immutable(self):
        proposal = Proposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            metadata={
                "trace": {
                    "source": "intelligence",
                },
            },
        )

        with self.assertRaises(TypeError):
            proposal.metadata["trace"]["source"] = "other"

    def test_proposal_is_immutable(self):
        proposal = Proposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
        )

        with self.assertRaises(AttributeError):
            proposal.decision_id = "changed"

    def test_workflow_proposal_is_immutable(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
        )

        with self.assertRaises(AttributeError):
            proposal.workflow_id = "changed"

    def test_proposal_does_not_contain_execution_plan(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
        )

        self.assertFalse(
            hasattr(proposal, "plan_id")
        )

        self.assertFalse(
            hasattr(proposal, "steps")
        )

    def test_proposal_does_not_execute(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
        )

        self.assertFalse(
            hasattr(proposal, "execute")
        )

        self.assertFalse(
            hasattr(proposal, "run")
        )

    def test_proposal_does_not_require_runtime(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
        )

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

    def test_proposal_does_not_contain_workflow_object(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
        )

        self.assertFalse(
            hasattr(proposal, "workflow")
        )

    def test_unknown_workflow_is_allowed_at_construction(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.unknown",
        )

        self.assertEqual(
            proposal.workflow_id,
            "workflow.unknown",
        )

    def test_proposal_does_not_contain_authorization(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
        )

        self.assertFalse(
            hasattr(proposal, "authorized")
        )

        self.assertFalse(
            hasattr(proposal, "permission")
        )

    def test_proposal_does_not_contain_model_provider(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
        )

        self.assertFalse(
            hasattr(proposal, "model")
        )

        self.assertFalse(
            hasattr(proposal, "provider")
        )

    def test_proposal_does_not_contain_reasoning(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
        )

        self.assertFalse(
            hasattr(proposal, "reasoning")
        )

        self.assertFalse(
            hasattr(proposal, "chain_of_thought")
        )

    def test_proposal_can_reference_different_decisions(self):
        first = WorkflowProposal(
            proposal_id="proposal:1",
            decision_id="decision:1",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.a",
        )

        second = WorkflowProposal(
            proposal_id="proposal:2",
            decision_id="decision:2",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.b",
        )

        self.assertNotEqual(
            first.decision_id,
            second.decision_id,
        )

    def test_proposal_creation_does_not_resolve_workflow(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.unknown",
        )

        self.assertEqual(
            proposal.workflow_id,
            "workflow.unknown",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)