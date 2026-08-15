from __future__ import annotations

import unittest

from ai_os.intelligence import (
    Decision,
    DecisionKind,
    Intent,
    Proposal,
    ProposalKind,
    SemanticValidationPipeline,
    SemanticValidationResult,
    SemanticValidationStatus,
    SemanticValidator,
    SemanticValidatorContract,
    ValidationResult,
    WorkflowProposal,
)


class TrackingValidator:
    def __init__(self, result: ValidationResult):
        self.result = result
        self.calls = 0
        self.received_intents = []
        self.received_decisions = []
        self.received_proposals = []

    def validate(self, intent, decision, proposal):
        self.calls += 1
        self.received_intents.append(intent)
        self.received_decisions.append(decision)
        self.received_proposals.append(proposal)
        return self.result


class WrongValidatorResult:
    def validate(self, intent, decision, proposal):
        return "invalid"


class RaisingValidator:
    def validate(self, intent, decision, proposal):
        raise RuntimeError("validator failed")


class MissingValidateValidator:
    pass


class SemanticValidationPipelineTests(unittest.TestCase):

    def create_intent(
        self,
        intent_id="intent:test",
        goal="generate_report",
    ):
        return Intent(
            intent_id=intent_id,
            goal=goal,
        )

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
        )

    def test_real_validator_matches_contract(self):
        self.assertIsInstance(
            SemanticValidator(),
            SemanticValidatorContract,
        )

    def test_invalid_validator_rejected(self):
        with self.assertRaises(TypeError):
            SemanticValidationPipeline(
                validator=object(),
            )

    def test_missing_validate_rejected(self):
        self.assertFalse(
            isinstance(
                MissingValidateValidator(),
                SemanticValidatorContract,
            )
        )

    def test_valid_answer(self):
        intent = self.create_intent()
        decision = self.create_decision(
            DecisionKind.ANSWER
        )

        pipeline = SemanticValidationPipeline(
            SemanticValidator()
        )

        result = pipeline.run(
            intent,
            decision,
            None,
        )

        self.assertEqual(
            result.status,
            SemanticValidationStatus.VALID,
        )

        self.assertTrue(
            result.validation.valid
        )

    def test_valid_workflow(self):
        intent = self.create_intent()

        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW
        )

        proposal = self.create_workflow_proposal(
            decision_id=decision.decision_id
        )

        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            intent,
            decision,
            proposal,
        )

        self.assertEqual(
            result.status,
            SemanticValidationStatus.VALID,
        )

        self.assertTrue(
            result.validation.valid
        )

    def test_invalid_intent_decision_relationship_is_rejected(self):
        intent = self.create_intent(
            intent_id="intent:one"
        )

        decision = self.create_decision(
            intent_id="intent:two"
        )

        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            intent,
            decision,
            None,
        )

        self.assertEqual(
            result.status,
            SemanticValidationStatus.REJECTED,
        )

        self.assertFalse(
            result.validation.valid
        )

    def test_missing_workflow_proposal_is_rejected(self):
        intent = self.create_intent()

        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW
        )

        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            intent,
            decision,
            None,
        )

        self.assertEqual(
            result.status,
            SemanticValidationStatus.REJECTED,
        )

    def test_proposal_decision_mismatch_is_rejected(self):
        intent = self.create_intent()

        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW,
            decision_id="decision:one",
        )

        proposal = self.create_workflow_proposal(
            decision_id="decision:two"
        )

        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            intent,
            decision,
            proposal,
        )

        self.assertEqual(
            result.status,
            SemanticValidationStatus.REJECTED,
        )

    def test_proposal_kind_mismatch_is_rejected(self):
        intent = self.create_intent()

        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW
        )

        proposal = Proposal(
            proposal_id="proposal:test",
            decision_id=decision.decision_id,
            kind=ProposalKind.PLAN,
        )

        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            intent,
            decision,
            proposal,
        )

        self.assertEqual(
            result.status,
            SemanticValidationStatus.REJECTED,
        )

    def test_unexpected_proposal_is_rejected(self):
        intent = self.create_intent()

        decision = self.create_decision(
            DecisionKind.ANSWER
        )

        proposal = self.create_workflow_proposal(
            decision_id=decision.decision_id
        )

        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            intent,
            decision,
            proposal,
        )

        self.assertEqual(
            result.status,
            SemanticValidationStatus.REJECTED,
        )

    def test_request_clarification_without_proposal_is_valid(self):
        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            self.create_intent(),
            self.create_decision(
                DecisionKind.REQUEST_CLARIFICATION
            ),
            None,
        )

        self.assertEqual(
            result.status,
            SemanticValidationStatus.VALID,
        )

    def test_decline_without_proposal_is_valid(self):
        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            self.create_intent(),
            self.create_decision(
                DecisionKind.DECLINE
            ),
            None,
        )

        self.assertEqual(
            result.status,
            SemanticValidationStatus.VALID,
        )

    def test_validator_receives_exact_objects(self):
        intent = self.create_intent()
        decision = self.create_decision()

        validation = ValidationResult(
            valid=True
        )

        validator = TrackingValidator(
            validation
        )

        SemanticValidationPipeline(
            validator
        ).run(
            intent,
            decision,
            None,
        )

        self.assertIs(
            validator.received_intents[0],
            intent,
        )

        self.assertIs(
            validator.received_decisions[0],
            decision,
        )

        self.assertIsNone(
            validator.received_proposals[0]
        )

    def test_validator_called_once(self):
        validator = TrackingValidator(
            ValidationResult(valid=True)
        )

        SemanticValidationPipeline(
            validator
        ).run(
            self.create_intent(),
            self.create_decision(),
            None,
        )

        self.assertEqual(
            validator.calls,
            1,
        )

    def test_wrong_validator_result_rejected(self):
        with self.assertRaises(TypeError):
            SemanticValidationPipeline(
                WrongValidatorResult()
            ).run(
                self.create_intent(),
                self.create_decision(),
                None,
            )

    def test_validator_exception_propagates(self):
        with self.assertRaises(RuntimeError):
            SemanticValidationPipeline(
                RaisingValidator()
            ).run(
                self.create_intent(),
                self.create_decision(),
                None,
            )

    def test_invalid_intent_rejected(self):
        with self.assertRaises(TypeError):
            SemanticValidationPipeline(
                SemanticValidator()
            ).run(
                "invalid",
                self.create_decision(),
                None,
            )

    def test_invalid_decision_rejected(self):
        with self.assertRaises(TypeError):
            SemanticValidationPipeline(
                SemanticValidator()
            ).run(
                self.create_intent(),
                "invalid",
                None,
            )

    def test_invalid_proposal_rejected(self):
        with self.assertRaises(TypeError):
            SemanticValidationPipeline(
                SemanticValidator()
            ).run(
                self.create_intent(),
                self.create_decision(),
                "invalid",
            )

    def test_result_is_immutable(self):
        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            self.create_intent(),
            self.create_decision(),
            None,
        )

        with self.assertRaises(AttributeError):
            result.status = SemanticValidationStatus.REJECTED

    def test_result_metadata_is_immutable(self):
        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            self.create_intent(),
            self.create_decision(),
            None,
        )

        with self.assertRaises(TypeError):
            result.metadata["changed"] = True

    def test_result_preserves_exact_intent(self):
        intent = self.create_intent()

        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            intent,
            self.create_decision(),
            None,
        )

        self.assertIs(
            result.intent,
            intent,
        )

    def test_result_preserves_exact_decision(self):
        decision = self.create_decision()

        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            self.create_intent(),
            decision,
            None,
        )

        self.assertIs(
            result.decision,
            decision,
        )

    def test_result_preserves_exact_proposal(self):
        decision = self.create_decision(
            DecisionKind.USE_WORKFLOW
        )

        proposal = self.create_workflow_proposal(
            decision_id=decision.decision_id
        )

        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            self.create_intent(),
            decision,
            proposal,
        )

        self.assertIs(
            result.proposal,
            proposal,
        )

    def test_pipeline_has_no_agent_decision(self):
        pipeline = SemanticValidationPipeline(
            SemanticValidator()
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "agent_decision",
            )
        )

    def test_pipeline_has_no_runtime(self):
        pipeline = SemanticValidationPipeline(
            SemanticValidator()
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

    def test_pipeline_has_no_execution_api(self):
        pipeline = SemanticValidationPipeline(
            SemanticValidator()
        )

        self.assertFalse(
            hasattr(pipeline, "execute")
        )

        self.assertFalse(
            hasattr(pipeline, "run_task")
        )

    def test_pipeline_has_no_proposal_generator(self):
        pipeline = SemanticValidationPipeline(
            SemanticValidator()
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "proposal_generator",
            )
        )

    def test_result_has_no_agent_decision(self):
        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            self.create_intent(),
            self.create_decision(),
            None,
        )

        self.assertFalse(
            hasattr(
                result,
                "agent_decision",
            )
        )

    def test_result_has_no_execution_plan(self):
        result = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            self.create_intent(),
            self.create_decision(),
            None,
        )

        self.assertFalse(
            hasattr(
                result,
                "execution_plan",
            )
        )

    def test_pipeline_is_reusable(self):
        pipeline = SemanticValidationPipeline(
            SemanticValidator()
        )

        first_intent = self.create_intent(
            "intent:first"
        )

        first_decision = self.create_decision(
            intent_id="intent:first",
            decision_id="decision:first",
        )

        second_intent = self.create_intent(
            "intent:second"
        )

        second_decision = self.create_decision(
            intent_id="intent:second",
            decision_id="decision:second",
        )

        first = pipeline.run(
            first_intent,
            first_decision,
            None,
        )

        second = pipeline.run(
            second_intent,
            second_decision,
            None,
        )

        self.assertIs(
            first.intent,
            first_intent,
        )

        self.assertIs(
            second.intent,
            second_intent,
        )

        self.assertIs(
            first.decision,
            first_decision,
        )

        self.assertIs(
            second.decision,
            second_decision,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)