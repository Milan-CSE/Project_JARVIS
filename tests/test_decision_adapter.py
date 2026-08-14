import unittest

from ai_os.intelligence import (
    Decision,
    DecisionAdapter,
    DecisionKind,
    Intent,
    ProposalKind,
    UnsupportedDecisionKindError,
    WorkflowProposal,
)
from ai_os.runtime.agents import (
    AgentDecision,
    AgentDecisionKind,
)


class DecisionAdapterTests(unittest.TestCase):

    def create_intent(self):
        return Intent(
            intent_id="intent:test",
            goal="generate_report",
        )

    def create_decision(
        self,
        kind=DecisionKind.USE_WORKFLOW,
        decision_id="decision:test",
    ):
        return Decision(
            decision_id=decision_id,
            intent_id="intent:test",
            kind=kind,
        )

    def create_proposal(
        self,
        decision_id="decision:test",
    ):
        return WorkflowProposal(
            proposal_id="proposal:test",
            decision_id=decision_id,
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.test",
            parameters={
                "date": "today",
            },
        )

    def test_use_workflow_maps_to_run_workflow(self):
        result = DecisionAdapter().to_agent_decision(
            self.create_intent(),
            self.create_decision(),
            self.create_proposal(),
        )

        self.assertIsInstance(
            result,
            AgentDecision,
        )

        self.assertEqual(
            result.kind,
            AgentDecisionKind.RUN_WORKFLOW,
        )

        self.assertEqual(
            result.workflow_id,
            "workflow.test",
        )

        self.assertEqual(
            dict(result.parameters),
            {"date": "today"},
        )

    def test_answer_maps_to_respond(self):
        result = DecisionAdapter().to_agent_decision(
            self.create_intent(),
            self.create_decision(
                kind=DecisionKind.ANSWER,
            ),
            None,
        )

        self.assertEqual(
            result.kind,
            AgentDecisionKind.RESPOND,
        )

        self.assertIsNone(
            result.message,
        )

    def test_clarification_maps_to_ask_clarification(self):
        result = DecisionAdapter().to_agent_decision(
            self.create_intent(),
            self.create_decision(
                kind=DecisionKind.REQUEST_CLARIFICATION,
            ),
            None,
        )

        self.assertEqual(
            result.kind,
            AgentDecisionKind.ASK_CLARIFICATION,
        )

    def test_decline_maps_to_decline(self):
        result = DecisionAdapter().to_agent_decision(
            self.create_intent(),
            self.create_decision(
                kind=DecisionKind.DECLINE,
            ),
            None,
        )

        self.assertEqual(
            result.kind,
            AgentDecisionKind.DECLINE,
        )

    def test_use_workflow_without_proposal_rejected(self):
        with self.assertRaises(ValueError):
            DecisionAdapter().to_agent_decision(
                self.create_intent(),
                self.create_decision(),
                None,
            )

    def test_answer_with_proposal_rejected(self):
        with self.assertRaises(ValueError):
            DecisionAdapter().to_agent_decision(
                self.create_intent(),
                self.create_decision(
                    kind=DecisionKind.ANSWER,
                ),
                self.create_proposal(),
            )

    def test_invalid_intent_decision_relationship_rejected(self):
        bad_decision = Decision(
            decision_id="decision:test",
            intent_id="intent:other",
            kind=DecisionKind.ANSWER,
        )

        with self.assertRaises(ValueError):
            DecisionAdapter().to_agent_decision(
                self.create_intent(),
                bad_decision,
                None,
            )

    def test_invalid_proposal_decision_relationship_rejected(self):
        bad_proposal = self.create_proposal(
            decision_id="decision:other",
        )

        with self.assertRaises(ValueError):
            DecisionAdapter().to_agent_decision(
                self.create_intent(),
                self.create_decision(),
                bad_proposal,
            )

    def test_unknown_workflow_is_not_resolved(self):
        proposal = WorkflowProposal(
            proposal_id="proposal:test",
            decision_id="decision:test",
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow.unknown",
        )

        result = DecisionAdapter().to_agent_decision(
            self.create_intent(),
            self.create_decision(),
            proposal,
        )

        self.assertEqual(
            result.workflow_id,
            "workflow.unknown",
        )

    def test_metadata_is_preserved(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.ANSWER,
            metadata={
                "source": "rule_engine",
            },
        )

        result = DecisionAdapter().to_agent_decision(
            self.create_intent(),
            decision,
            None,
        )

        self.assertEqual(
            result.metadata["source"],
            "rule_engine",
        )

    def test_adapter_does_not_execute(self):
        adapter = DecisionAdapter()

        self.assertFalse(
            hasattr(adapter, "execute")
        )

        self.assertFalse(
            hasattr(adapter, "run")
        )

    def test_adapter_does_not_require_runtime(self):
        adapter = DecisionAdapter()

        self.assertFalse(
            hasattr(adapter, "runtime")
        )

        self.assertFalse(
            hasattr(adapter, "scheduler")
        )

        self.assertFalse(
            hasattr(adapter, "task_executor")
        )

        self.assertFalse(
            hasattr(adapter, "task_registry")
        )

    def test_adapter_does_not_require_engine(self):
        adapter = DecisionAdapter()

        self.assertFalse(
            hasattr(adapter, "engine")
        )

    def test_adapter_does_not_call_workflow_resolver(self):
        proposal = self.create_proposal()
        result = DecisionAdapter().to_agent_decision(
            self.create_intent(),
            self.create_decision(),
            proposal,
        )

        self.assertEqual(
            result.workflow_id,
            proposal.workflow_id,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)