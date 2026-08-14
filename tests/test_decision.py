import unittest

from ai_os.intelligence import (
    Decision,
    DecisionKind,
)


class DecisionTests(unittest.TestCase):

    def test_decision_can_be_created(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.USE_WORKFLOW,
        )

        self.assertEqual(
            decision.intent_id,
            "intent:test",
        )

        self.assertEqual(
            decision.kind,
            DecisionKind.USE_WORKFLOW,
        )

    def test_decision_accepts_string_kind(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind="answer",
        )

        self.assertEqual(
            decision.kind,
            DecisionKind.ANSWER,
        )

    def test_all_initial_decision_kinds_exist(self):
        self.assertEqual(
            set(DecisionKind),
            {
                DecisionKind.USE_WORKFLOW,
                DecisionKind.ANSWER,
                DecisionKind.REQUEST_CLARIFICATION,
                DecisionKind.DECLINE,
            },
        )

    def test_empty_intent_id_rejected(self):
        with self.assertRaises(ValueError):
            Decision(
                decision_id="decision:test",
                intent_id="",
                kind=DecisionKind.ANSWER,
            )

    def test_whitespace_intent_id_rejected(self):
        with self.assertRaises(ValueError):
            Decision(
                decision_id="decision:test",
                intent_id="   ",
                kind=DecisionKind.ANSWER,
            )

    def test_invalid_intent_id_type_rejected(self):
        with self.assertRaises(TypeError):
            Decision(
                decision_id="decision:test",
                intent_id=123,
                kind=DecisionKind.ANSWER,
            )

    def test_invalid_kind_rejected(self):
        with self.assertRaises(ValueError):
            Decision(
                decision_id="decision:test",
                intent_id="intent:test",
                kind="delete_everything",
            )

    def test_invalid_metadata_rejected(self):
        with self.assertRaises(TypeError):
            Decision(
                decision_id="decision:test",
                intent_id="intent:test",
                kind=DecisionKind.ANSWER,
                metadata=[],
            )

    def test_metadata_defaults_to_empty(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.ANSWER,
        )

        self.assertEqual(
            dict(decision.metadata),
            {},
        )

    def test_metadata_is_immutable(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.ANSWER,
            metadata={
                "source": "test",
            },
        )

        with self.assertRaises(TypeError):
            decision.metadata["source"] = "changed"

    def test_decision_is_immutable(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.ANSWER,
        )

        with self.assertRaises(AttributeError):
            decision.kind = DecisionKind.DECLINE

    def test_decision_does_not_contain_workflow_id(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.USE_WORKFLOW,
        )

        self.assertFalse(
            hasattr(decision, "workflow_id")
        )

    def test_decision_does_not_contain_parameters(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.USE_WORKFLOW,
        )

        self.assertFalse(
            hasattr(decision, "parameters")
        )

    def test_decision_does_not_contain_execution_plan(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.USE_WORKFLOW,
        )

        self.assertFalse(
            hasattr(decision, "plan_id")
        )

        self.assertFalse(
            hasattr(decision, "steps")
        )

    def test_decision_does_not_execute(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.USE_WORKFLOW,
        )

        self.assertFalse(
            hasattr(decision, "execute")
        )

        self.assertFalse(
            hasattr(decision, "run")
        )

    def test_decision_does_not_require_runtime(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.USE_WORKFLOW,
        )

        self.assertFalse(
            hasattr(decision, "runtime")
        )

        self.assertFalse(
            hasattr(decision, "scheduler")
        )

        self.assertFalse(
            hasattr(decision, "task_executor")
        )

        self.assertFalse(
            hasattr(decision, "task_registry")
        )

    def test_decision_does_not_require_agent(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.ANSWER,
        )

        self.assertFalse(
            hasattr(decision, "agent")
        )

        self.assertFalse(
            hasattr(decision, "handle")
        )

    def test_decision_does_not_require_model_provider(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.ANSWER,
        )

        self.assertFalse(
            hasattr(decision, "model")
        )

        self.assertFalse(
            hasattr(decision, "provider")
        )

    def test_decision_is_not_authorization(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.USE_WORKFLOW,
        )

        self.assertFalse(
            hasattr(decision, "authorized")
        )

        self.assertFalse(
            hasattr(decision, "permission")
        )

    def test_decision_does_not_contain_reasoning(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.ANSWER,
        )

        self.assertFalse(
            hasattr(decision, "reasoning")
        )

        self.assertFalse(
            hasattr(decision, "chain_of_thought")
        )

    def test_same_intent_can_have_different_decisions(self):
        first = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.ANSWER,
        )

        second = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.REQUEST_CLARIFICATION,
        )

        self.assertEqual(
            first.intent_id,
            second.intent_id,
        )

        self.assertNotEqual(
            first.kind,
            second.kind,
        )

    def test_empty_decision_id_rejected(self):
        with self.assertRaises(ValueError):
            Decision(
                # decision_id="decision:test",
                decision_id="",
                intent_id="intent:test",
                kind=DecisionKind.ANSWER,
            )


    def test_whitespace_decision_id_rejected(self):
        with self.assertRaises(ValueError):
            Decision(
                decision_id="   ",
                intent_id="intent:test",
                kind=DecisionKind.ANSWER,
            )


    def test_invalid_decision_id_type_rejected(self):
        with self.assertRaises(TypeError):
            Decision(
                decision_id=123,
                intent_id="intent:test",
                kind=DecisionKind.ANSWER,
            )


    def test_decision_id_is_immutable(self):
        decision = Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.ANSWER,
        )

        with self.assertRaises(AttributeError):
            decision.decision_id = "changed"


if __name__ == "__main__":
    unittest.main(verbosity=2)