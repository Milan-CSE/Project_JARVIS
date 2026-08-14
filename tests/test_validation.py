import unittest

from ai_os.intelligence import (
    Decision,
    DecisionKind,
    Intent,
    ProposalKind,
    SemanticValidator,
    ValidationIssue,
    ValidationResult,
    WorkflowProposal,
)


class SemanticValidationTests(unittest.TestCase):

    def create_intent(
        self,
        intent_id="intent:test",
    ):
        return Intent(
            intent_id=intent_id,
            goal="generate_sales_report",
        )

    def create_decision(
        self,
        decision_id="decision:test",
        intent_id="intent:test",
        kind=DecisionKind.USE_WORKFLOW,
    ):
        return Decision(
            decision_id=decision_id,
            intent_id=intent_id,
            kind=kind,
        )

    def create_workflow_proposal(
        self,
        proposal_id="proposal:test",
        decision_id="decision:test",
        workflow_id="workflow.sales_report",
    ):
        return WorkflowProposal(
            proposal_id=proposal_id,
            decision_id=decision_id,
            kind=ProposalKind.WORKFLOW,
            workflow_id=workflow_id,
        )

    def test_valid_use_workflow(self):
        intent = self.create_intent()
        decision = self.create_decision()
        proposal = self.create_workflow_proposal()

        result = SemanticValidator().validate(
            intent,
            decision,
            proposal,
        )

        self.assertTrue(result.valid)
        self.assertEqual(result.issues, ())

    def test_intent_mismatch_rejected(self):
        intent = self.create_intent(
            intent_id="intent:one"
        )

        decision = self.create_decision(
            intent_id="intent:two"
        )

        proposal = self.create_workflow_proposal()

        result = SemanticValidator().validate(
            intent,
            decision,
            proposal,
        )

        self.assertFalse(result.valid)

        codes = {
            issue.code
            for issue in result.issues
        }

        self.assertIn(
            "INTENT_MISMATCH",
            codes,
        )

    def test_proposal_decision_mismatch_rejected(self):
        intent = self.create_intent()

        decision = self.create_decision(
            decision_id="decision:one"
        )

        proposal = self.create_workflow_proposal(
            decision_id="decision:two"
        )

        result = SemanticValidator().validate(
            intent,
            decision,
            proposal,
        )

        self.assertFalse(result.valid)

        codes = {
            issue.code
            for issue in result.issues
        }

        self.assertIn(
            "PROPOSAL_DECISION_MISMATCH",
            codes,
        )

    def test_use_workflow_without_proposal_rejected(self):
        intent = self.create_intent()
        decision = self.create_decision()

        result = SemanticValidator().validate(
            intent,
            decision,
            None,
        )

        self.assertFalse(result.valid)

        self.assertEqual(
            result.issues[0].code,
            "REQUIRED_PROPOSAL_MISSING",
        )

    def test_answer_without_proposal_is_valid(self):
        intent = self.create_intent()

        decision = self.create_decision(
            kind=DecisionKind.ANSWER,
        )

        result = SemanticValidator().validate(
            intent,
            decision,
            None,
        )

        self.assertTrue(result.valid)

    def test_clarification_without_proposal_is_valid(self):
        intent = self.create_intent()

        decision = self.create_decision(
            kind=DecisionKind.REQUEST_CLARIFICATION,
        )

        result = SemanticValidator().validate(
            intent,
            decision,
            None,
        )

        self.assertTrue(result.valid)

    def test_decline_without_proposal_is_valid(self):
        intent = self.create_intent()

        decision = self.create_decision(
            kind=DecisionKind.DECLINE,
        )

        result = SemanticValidator().validate(
            intent,
            decision,
            None,
        )

        self.assertTrue(result.valid)

    def test_answer_with_proposal_rejected(self):
        intent = self.create_intent()

        decision = self.create_decision(
            kind=DecisionKind.ANSWER,
        )

        proposal = self.create_workflow_proposal()

        result = SemanticValidator().validate(
            intent,
            decision,
            proposal,
        )

        self.assertFalse(result.valid)

        self.assertEqual(
            result.issues[0].code,
            "UNEXPECTED_PROPOSAL",
        )

    def test_clarification_with_proposal_rejected(self):
        intent = self.create_intent()

        decision = self.create_decision(
            kind=DecisionKind.REQUEST_CLARIFICATION,
        )

        proposal = self.create_workflow_proposal()

        result = SemanticValidator().validate(
            intent,
            decision,
            proposal,
        )

        self.assertFalse(result.valid)

    def test_decline_with_proposal_rejected(self):
        intent = self.create_intent()

        decision = self.create_decision(
            kind=DecisionKind.DECLINE,
        )

        proposal = self.create_workflow_proposal()

        result = SemanticValidator().validate(
            intent,
            decision,
            proposal,
        )

        self.assertFalse(result.valid)

    def test_validator_does_not_resolve_workflow(self):
        intent = self.create_intent()
        decision = self.create_decision()

        proposal = self.create_workflow_proposal(
            workflow_id="workflow.unknown"
        )

        result = SemanticValidator().validate(
            intent,
            decision,
            proposal,
        )

        self.assertTrue(result.valid)

    def test_validation_result_is_immutable(self):
        result = ValidationResult(
            valid=True,
        )

        with self.assertRaises(AttributeError):
            result.valid = False

    def test_validation_issue_is_immutable(self):
        issue = ValidationIssue(
            code="TEST",
            message="test",
        )

        with self.assertRaises(AttributeError):
            issue.code = "OTHER"

    def test_invalid_validator_input_rejected(self):
        with self.assertRaises(TypeError):
            SemanticValidator().validate(
                "invalid",
                self.create_decision(),
                None,
            )

    def test_invalid_decision_input_rejected(self):
        with self.assertRaises(TypeError):
            SemanticValidator().validate(
                self.create_intent(),
                "invalid",
                None,
            )

    def test_invalid_proposal_input_rejected(self):
        with self.assertRaises(TypeError):
            SemanticValidator().validate(
                self.create_intent(),
                self.create_decision(),
                "invalid",
            )

    def test_validator_does_not_execute(self):
        validator = SemanticValidator()

        self.assertFalse(
            hasattr(validator, "execute")
        )

        self.assertFalse(
            hasattr(validator, "run")
        )

    def test_validator_does_not_require_runtime(self):
        validator = SemanticValidator()

        self.assertFalse(
            hasattr(validator, "runtime")
        )

        self.assertFalse(
            hasattr(validator, "scheduler")
        )

        self.assertFalse(
            hasattr(validator, "task_executor")
        )

        self.assertFalse(
            hasattr(validator, "task_registry")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)