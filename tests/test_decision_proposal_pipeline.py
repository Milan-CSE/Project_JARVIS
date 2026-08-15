from __future__ import annotations

import unittest

from ai_os.intelligence import (
    Decision,
    DecisionKind,
    DecisionProposalPipeline,
    DecisionProposalResult,
    DecisionProposalStatus,
    PlanProposal,
    Proposal,
    ProposalGeneratorContract,
    ProposalKind,
    WorkflowProposal,
)


class TrackingProposalGenerator:
    def __init__(self, result):
        self.result = result
        self.calls = 0
        self.received_decisions = []
        self.received_proposal_ids = []

    def generate(
        self,
        decision,
        proposal_id,
    ):
        self.calls += 1
        self.received_decisions.append(decision)
        self.received_proposal_ids.append(proposal_id)
        return self.result


class WrongResultGenerator:
    def generate(
        self,
        decision,
        proposal_id,
    ):
        return "invalid"


class FailingGenerator:
    def generate(
        self,
        decision,
        proposal_id,
    ):
        raise RuntimeError("proposal generation failed")


class MissingGenerateGenerator:
    pass


class DecisionProposalPipelineTests(unittest.TestCase):

    def create_decision(
        self,
        kind=DecisionKind.ANSWER,
        decision_id="decision:test",
        intent_id="intent:test",
    ):
        return Decision(
            decision_id=decision_id,
            intent_id=intent_id,
            kind=kind,
        )

    def create_workflow_proposal(
        self,
        decision_id="decision:test",
        proposal_id="proposal:test",
        workflow_id="workflow:test",
    ):
        return WorkflowProposal(
            proposal_id=proposal_id,
            decision_id=decision_id,
            kind=ProposalKind.WORKFLOW,
            workflow_id=workflow_id,
            parameters={
                "value": 42,
            },
        )

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def test_valid_generator_matches_structural_contract(self):
        generator = TrackingProposalGenerator(None)

        self.assertIsInstance(
            generator,
            ProposalGeneratorContract,
        )

    def test_invalid_generator_does_not_match_contract(self):
        self.assertFalse(
            isinstance(
                object(),
                ProposalGeneratorContract,
            )
        )

    def test_missing_generate_method_does_not_match_contract(self):
        generator = MissingGenerateGenerator()

        self.assertFalse(
            isinstance(
                generator,
                ProposalGeneratorContract,
            )
        )

    def test_pipeline_rejects_invalid_generator(self):
        with self.assertRaises(TypeError):
            DecisionProposalPipeline(
                proposal_generator=object(),
            )

    # ------------------------------------------------------------------
    # ANSWER
    # ------------------------------------------------------------------

    def test_answer_requires_no_proposal(self):
        generator = TrackingProposalGenerator(None)

        pipeline = DecisionProposalPipeline(
            proposal_generator=generator,
        )

        decision = self.create_decision(
            DecisionKind.ANSWER
        )

        result = pipeline.run(
            decision,
            "proposal:test",
        )

        self.assertIsInstance(
            result,
            DecisionProposalResult,
        )

        self.assertEqual(
            result.status,
            DecisionProposalStatus.NO_PROPOSAL_REQUIRED,
        )

        self.assertIs(
            result.decision,
            decision,
        )

        self.assertIsNone(
            result.proposal,
        )

    # ------------------------------------------------------------------
    # REQUEST_CLARIFICATION
    # ------------------------------------------------------------------

    def test_request_clarification_requires_no_proposal(self):
        generator = TrackingProposalGenerator(None)

        pipeline = DecisionProposalPipeline(
            proposal_generator=generator,
        )

        decision = self.create_decision(
            DecisionKind.REQUEST_CLARIFICATION
        )

        result = pipeline.run(
            decision,
            "proposal:test",
        )

        self.assertEqual(
            result.status,
            DecisionProposalStatus.NO_PROPOSAL_REQUIRED,
        )

        self.assertIsNone(
            result.proposal,
        )

    # ------------------------------------------------------------------
    # DECLINE
    # ------------------------------------------------------------------

    def test_decline_requires_no_proposal(self):
        generator = TrackingProposalGenerator(None)

        pipeline = DecisionProposalPipeline(
            proposal_generator=generator,
        )

        decision = self.create_decision(
            DecisionKind.DECLINE
        )

        result = pipeline.run(
            decision,
            "proposal:test",
        )

        self.assertEqual(
            result.status,
            DecisionProposalStatus.NO_PROPOSAL_REQUIRED,
        )

        self.assertIsNone(
            result.proposal,
        )

    # ------------------------------------------------------------------
    # USE_WORKFLOW
    # ------------------------------------------------------------------

    def test_use_workflow_requires_workflow_proposal(self):
        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW
        )

        proposal = self.create_workflow_proposal(
            decision_id=decision.decision_id,
        )

        generator = TrackingProposalGenerator(
            proposal
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=generator,
        )

        result = pipeline.run(
            decision,
            proposal.proposal_id,
        )

        self.assertEqual(
            result.status,
            DecisionProposalStatus.PROPOSAL_CREATED,
        )

        self.assertIs(
            result.proposal,
            proposal,
        )

        self.assertIs(
            result.decision,
            decision,
        )

    def test_use_workflow_without_proposal_is_rejected(self):
        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        with self.assertRaises(ValueError):
            pipeline.run(
                decision,
                "proposal:test",
            )

    def test_use_workflow_rejects_non_workflow_proposal(self):
        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW
        )

        wrong_proposal = PlanProposal(
            proposal_id="proposal:test",
            decision_id=decision.decision_id,
            kind=ProposalKind.PLAN,
            steps=(),
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(
                wrong_proposal
            )
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                decision,
                "proposal:test",
            )

    # ------------------------------------------------------------------
    # Non-workflow decisions must not produce proposals
    # ------------------------------------------------------------------

    def test_answer_rejects_unexpected_proposal(self):
        decision = self.create_decision(
            DecisionKind.ANSWER
        )

        proposal = self.create_workflow_proposal(
            decision_id=decision.decision_id,
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(
                proposal
            )
        )

        with self.assertRaises(ValueError):
            pipeline.run(
                decision,
                "proposal:test",
            )

    def test_request_clarification_rejects_unexpected_proposal(self):
        decision = self.create_decision(
            DecisionKind.REQUEST_CLARIFICATION
        )

        proposal = self.create_workflow_proposal(
            decision_id=decision.decision_id,
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(
                proposal
            )
        )

        with self.assertRaises(ValueError):
            pipeline.run(
                decision,
                "proposal:test",
            )

    def test_decline_rejects_unexpected_proposal(self):
        decision = self.create_decision(
            DecisionKind.DECLINE
        )

        proposal = self.create_workflow_proposal(
            decision_id=decision.decision_id,
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(
                proposal
            )
        )

        with self.assertRaises(ValueError):
            pipeline.run(
                decision,
                "proposal:test",
            )

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------

    def test_invalid_decision_rejected(self):
        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                "invalid",
                "proposal:test",
            )

    def test_none_decision_rejected(self):
        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                None,
                "proposal:test",
            )

    def test_empty_proposal_id_rejected(self):
        decision = self.create_decision(
            DecisionKind.ANSWER
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        with self.assertRaises(ValueError):
            pipeline.run(
                decision,
                "",
            )

    def test_whitespace_proposal_id_rejected(self):
        decision = self.create_decision(
            DecisionKind.ANSWER
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        with self.assertRaises(ValueError):
            pipeline.run(
                decision,
                "   ",
            )

    def test_invalid_proposal_id_type_rejected(self):
        decision = self.create_decision(
            DecisionKind.ANSWER
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                decision,
                123,
            )

    # ------------------------------------------------------------------
    # Generator interaction
    # ------------------------------------------------------------------

    def test_generator_called_exactly_once(self):
        generator = TrackingProposalGenerator(None)

        pipeline = DecisionProposalPipeline(
            proposal_generator=generator,
        )

        pipeline.run(
            self.create_decision(
                DecisionKind.ANSWER
            ),
            "proposal:test",
        )

        self.assertEqual(
            generator.calls,
            1,
        )

    def test_generator_receives_exact_decision(self):
        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW
        )

        proposal = self.create_workflow_proposal(
            decision_id=decision.decision_id,
        )

        generator = TrackingProposalGenerator(
            proposal
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=generator,
        )

        pipeline.run(
            decision,
            proposal.proposal_id,
        )

        self.assertIs(
            generator.received_decisions[0],
            decision,
        )

    def test_generator_receives_exact_proposal_id(self):
        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW
        )

        proposal = self.create_workflow_proposal(
            decision_id=decision.decision_id,
            proposal_id="proposal:123",
        )

        generator = TrackingProposalGenerator(
            proposal
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=generator,
        )

        pipeline.run(
            decision,
            "proposal:123",
        )

        self.assertEqual(
            generator.received_proposal_ids,
            ["proposal:123"],
        )

    # ------------------------------------------------------------------
    # Output boundary
    # ------------------------------------------------------------------

    def test_invalid_generator_result_rejected(self):
        pipeline = DecisionProposalPipeline(
            proposal_generator=WrongResultGenerator()
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                self.create_decision(
                    DecisionKind.ANSWER
                ),
                "proposal:test",
            )

    def test_generator_failure_propagates(self):
        pipeline = DecisionProposalPipeline(
            proposal_generator=FailingGenerator()
        )

        with self.assertRaises(RuntimeError):
            pipeline.run(
                self.create_decision(
                    DecisionKind.ANSWER
                ),
                "proposal:test",
            )

    # ------------------------------------------------------------------
    # Semantic relationships preserved
    # ------------------------------------------------------------------

    def test_workflow_proposal_preserves_decision_id(self):
        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW
        )

        proposal = self.create_workflow_proposal(
            decision_id=decision.decision_id,
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(
                proposal
            )
        )

        result = pipeline.run(
            decision,
            proposal.proposal_id,
        )

        self.assertEqual(
            result.proposal.decision_id,
            decision.decision_id,
        )

    def test_workflow_proposal_id_is_preserved(self):
        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW
        )

        proposal = self.create_workflow_proposal(
            decision_id=decision.decision_id,
            proposal_id="proposal:123",
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(
                proposal
            )
        )

        result = pipeline.run(
            decision,
            "proposal:123",
        )

        self.assertEqual(
            result.proposal.proposal_id,
            "proposal:123",
        )

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------

    def test_result_is_immutable(self):
        decision = self.create_decision(
            DecisionKind.ANSWER
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        result = pipeline.run(
            decision,
            "proposal:test",
        )

        with self.assertRaises(AttributeError):
            result.status = DecisionProposalStatus.PROPOSAL_CREATED

    def test_result_metadata_is_immutable(self):
        decision = self.create_decision(
            DecisionKind.ANSWER
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        result = pipeline.run(
            decision,
            "proposal:test",
        )

        with self.assertRaises(TypeError):
            result.metadata["changed"] = True

    def test_decision_is_not_mutated(self):
        decision = self.create_decision(
            DecisionKind.ANSWER
        )

        original_id = decision.decision_id
        original_intent_id = decision.intent_id
        original_kind = decision.kind

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        pipeline.run(
            decision,
            "proposal:test",
        )

        self.assertEqual(
            decision.decision_id,
            original_id,
        )

        self.assertEqual(
            decision.intent_id,
            original_intent_id,
        )

        self.assertEqual(
            decision.kind,
            original_kind,
        )

    # ------------------------------------------------------------------
    # Boundary enforcement
    # ------------------------------------------------------------------

    def test_pipeline_has_no_agent_decision(self):
        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "agent_decision",
            )
        )

    def test_pipeline_has_no_runtime(self):
        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "runtime",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "scheduler",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "task_executor",
            )
        )

    def test_pipeline_has_no_execution_api(self):
        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "execute",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "run_task",
            )
        )

    def test_pipeline_has_no_validator(self):
        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "validator",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "_validator",
            )
        )

    def test_result_has_no_agent_decision(self):
        result = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        ).run(
            self.create_decision(
                DecisionKind.ANSWER
            ),
            "proposal:test",
        )

        self.assertFalse(
            hasattr(
                result,
                "agent_decision",
            )
        )

    def test_result_has_no_execution_plan(self):
        result = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(None)
        ).run(
            self.create_decision(
                DecisionKind.ANSWER
            ),
            "proposal:test",
        )

        self.assertFalse(
            hasattr(
                result,
                "execution_plan",
            )
        )

    # ------------------------------------------------------------------
    # Reusability
    # ------------------------------------------------------------------

    def test_pipeline_is_reusable(self):
        first_decision = self.create_decision(
            DecisionKind.ANSWER,
            decision_id="decision:one",
        )

        second_decision = self.create_decision(
            DecisionKind.DECLINE,
            decision_id="decision:two",
        )

        generator = TrackingProposalGenerator(None)

        pipeline = DecisionProposalPipeline(
            proposal_generator=generator,
        )

        first = pipeline.run(
            first_decision,
            "proposal:one",
        )

        second = pipeline.run(
            second_decision,
            "proposal:two",
        )

        self.assertIs(
            first.decision,
            first_decision,
        )

        self.assertIs(
            second.decision,
            second_decision,
        )

        self.assertEqual(
            generator.calls,
            2,
        )

    # ------------------------------------------------------------------
    # No planning semantics invented
    # ------------------------------------------------------------------

    def test_plan_proposal_is_not_accepted_for_use_workflow(self):
        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW
        )

        plan = PlanProposal(
            proposal_id="proposal:test",
            decision_id=decision.decision_id,
            kind=ProposalKind.PLAN,
            steps=(),
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(
                plan
            )
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                decision,
                "proposal:test",
            )

    def test_answer_does_not_activate_plan_proposal(self):
        decision = self.create_decision(
            DecisionKind.ANSWER
        )

        plan = PlanProposal(
            proposal_id="proposal:test",
            decision_id=decision.decision_id,
            kind=ProposalKind.PLAN,
            steps=(),
        )

        pipeline = DecisionProposalPipeline(
            proposal_generator=TrackingProposalGenerator(
                plan
            )
        )

        with self.assertRaises(ValueError):
            pipeline.run(
                decision,
                "proposal:test",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)