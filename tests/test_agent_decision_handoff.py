from __future__ import annotations

import unittest

from ai_os.intelligence import (
    AgentDecisionHandoffPipeline,
    AgentDecisionHandoffResult,
    AgentDecisionHandoffStatus,
    Decision,
    DecisionAdapter,
    DecisionAdapterContract,
    DecisionKind,
    Intent,
    ProposalKind,
    SemanticValidationPipeline,
    SemanticValidationStatus,
    SemanticValidator,
    WorkflowProposal,
)

from ai_os.runtime.agents import AgentDecision


class TrackingAdapter:
    def __init__(self, result):
        self.result = result
        self.calls = 0
        self.received_intents = []
        self.received_decisions = []
        self.received_proposals = []

    def to_agent_decision(
        self,
        intent,
        decision,
        proposal,
    ):
        self.calls += 1
        self.received_intents.append(intent)
        self.received_decisions.append(decision)
        self.received_proposals.append(proposal)
        return self.result


class WrongAdapterResult:
    def to_agent_decision(
        self,
        intent,
        decision,
        proposal,
    ):
        return "invalid"


class MissingAdapter:
    pass


class AgentDecisionHandoffTests(unittest.TestCase):

    def create_intent(self):
        return Intent(
            intent_id="intent:test",
            goal="generate_report",
        )

    def create_decision(
        self,
        kind=DecisionKind.ANSWER,
    ):
        return Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=kind,
        )

    def create_workflow_proposal(
        self,
        decision_id="decision:test",
    ):
        return WorkflowProposal(
            proposal_id="proposal:test",
            decision_id=decision_id,
            kind=ProposalKind.WORKFLOW,
            workflow_id="workflow:test",
            parameters={"value": 42},
        )

    def create_validated(
        self,
        kind=DecisionKind.ANSWER,
    ):
        intent = self.create_intent()
        decision = self.create_decision(kind)

        proposal = None

        if kind is DecisionKind.USE_WORKFLOW:
            proposal = self.create_workflow_proposal(
                decision.decision_id
            )

        return SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            intent,
            decision,
            proposal,
        )

    def test_real_adapter_matches_contract(self):
        self.assertIsInstance(
            DecisionAdapter(),
            DecisionAdapterContract,
        )

    def test_invalid_adapter_rejected(self):
        with self.assertRaises(TypeError):
            AgentDecisionHandoffPipeline(
                adapter=object()
            )

    def test_missing_adapter_method_rejected(self):
        self.assertFalse(
            isinstance(
                MissingAdapter(),
                DecisionAdapterContract,
            )
        )

    def test_answer_is_handed_off(self):
        validated = self.create_validated(
            DecisionKind.ANSWER
        )

        result = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        self.assertEqual(
            result.status,
            AgentDecisionHandoffStatus.HANDED_OFF,
        )

        self.assertIsInstance(
            result.agent_decision,
            AgentDecision,
        )

    def test_decline_is_handed_off(self):
        validated = self.create_validated(
            DecisionKind.DECLINE
        )

        result = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        self.assertIsInstance(
            result.agent_decision,
            AgentDecision,
        )

    def test_clarification_is_handed_off(self):
        validated = self.create_validated(
            DecisionKind.REQUEST_CLARIFICATION
        )

        result = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        self.assertIsInstance(
            result.agent_decision,
            AgentDecision,
        )

    def test_workflow_is_handed_off(self):
        validated = self.create_validated(
            DecisionKind.USE_WORKFLOW
        )

        result = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        self.assertIsInstance(
            result.agent_decision,
            AgentDecision,
        )

    def test_rejected_validation_cannot_be_handed_off(self):
        intent = self.create_intent()

        decision = Decision(
            decision_id="decision:test",
            intent_id="different:intent",
            kind=DecisionKind.ANSWER,
        )

        validated = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            intent,
            decision,
            None,
        )

        self.assertEqual(
            validated.status,
            SemanticValidationStatus.REJECTED,
        )

        with self.assertRaises(ValueError):
            AgentDecisionHandoffPipeline(
                DecisionAdapter()
            ).run(validated)

    def test_exact_objects_are_forwarded(self):
        validated = self.create_validated()

        real_agent_decision = DecisionAdapter().to_agent_decision(
            validated.intent,
            validated.decision,
            validated.proposal,
        )

        adapter = TrackingAdapter(
            real_agent_decision
        )

        AgentDecisionHandoffPipeline(
            adapter
        ).run(validated)

        self.assertIs(
            adapter.received_intents[0],
            validated.intent,
        )

        self.assertIs(
            adapter.received_decisions[0],
            validated.decision,
        )

        self.assertIs(
            adapter.received_proposals[0],
            validated.proposal,
        )

    def test_adapter_called_once(self):
        validated = self.create_validated()

        real_agent_decision = DecisionAdapter().to_agent_decision(
            validated.intent,
            validated.decision,
            validated.proposal,
        )

        adapter = TrackingAdapter(
            real_agent_decision
        )

        AgentDecisionHandoffPipeline(
            adapter
        ).run(validated)

        self.assertEqual(
            adapter.calls,
            1,
        )

    def test_wrong_adapter_result_rejected(self):
        validated = self.create_validated()

        with self.assertRaises(TypeError):
            AgentDecisionHandoffPipeline(
                WrongAdapterResult()
            ).run(validated)

    def test_invalid_input_rejected(self):
        with self.assertRaises(TypeError):
            AgentDecisionHandoffPipeline(
                DecisionAdapter()
            ).run("invalid")

    def test_result_is_immutable(self):
        validated = self.create_validated()

        result = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        with self.assertRaises(AttributeError):
            result.status = AgentDecisionHandoffStatus.HANDED_OFF

    def test_result_metadata_is_immutable(self):
        validated = self.create_validated()

        result = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        with self.assertRaises(TypeError):
            result.metadata["changed"] = True

    def test_result_preserves_intent(self):
        validated = self.create_validated()

        result = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        self.assertIs(
            result.intent,
            validated.intent,
        )

    def test_result_preserves_decision(self):
        validated = self.create_validated()

        result = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        self.assertIs(
            result.decision,
            validated.decision,
        )

    def test_result_preserves_proposal(self):
        validated = self.create_validated(
            DecisionKind.USE_WORKFLOW
        )

        result = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        self.assertIs(
            result.proposal,
            validated.proposal,
        )

    def test_result_preserves_validation(self):
        validated = self.create_validated()

        result = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        self.assertIs(
            result.validation,
            validated,
        )

    def test_pipeline_does_not_execute_agent(self):
        pipeline = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        )

        self.assertFalse(
            hasattr(pipeline, "execute")
        )

        self.assertFalse(
            hasattr(pipeline, "run_agent")
        )

    def test_pipeline_has_no_runtime_api(self):
        pipeline = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        )

        self.assertFalse(
            hasattr(pipeline, "runtime")
        )

        self.assertFalse(
            hasattr(pipeline, "scheduler")
        )

        self.assertFalse(
            hasattr(pipeline, "task_executor")
        )

    def test_result_does_not_contain_execution_result(self):
        validated = self.create_validated()

        result = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        self.assertFalse(
            hasattr(result, "execution_result")
        )

    def test_pipeline_is_reusable(self):
        pipeline = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        )

        first = pipeline.run(
            self.create_validated(
                DecisionKind.ANSWER
            )
        )

        second = pipeline.run(
            self.create_validated(
                DecisionKind.DECLINE
            )
        )

        self.assertIsInstance(
            first.agent_decision,
            AgentDecision,
        )

        self.assertIsInstance(
            second.agent_decision,
            AgentDecision,
        )

    def test_agent_handoff_does_not_change_decision(self):
        validated = self.create_validated()

        original_kind = validated.decision.kind
        original_id = validated.decision.decision_id

        AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        self.assertEqual(
            validated.decision.kind,
            original_kind,
        )

        self.assertEqual(
            validated.decision.decision_id,
            original_id,
        )

    def test_agent_handoff_does_not_change_proposal(self):
        validated = self.create_validated(
            DecisionKind.USE_WORKFLOW
        )

        original_workflow_id = (
            validated.proposal.workflow_id
        )

        AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validated)

        self.assertEqual(
            validated.proposal.workflow_id,
            original_workflow_id,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)