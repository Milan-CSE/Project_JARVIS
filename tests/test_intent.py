import unittest

from ai_os.intelligence import Intent


class ValidIntent:

    pass


class IntentTests(unittest.TestCase):

    def test_intent_can_be_created(self):
        intent = Intent(
            intent_id="intent:test",
            goal="generate_sales_report",
        )

        self.assertEqual(
            intent.intent_id,
            "intent:test",
        )

        self.assertEqual(
            intent.goal,
            "generate_sales_report",
        )

    def test_intent_accepts_parameters(self):
        intent = Intent(
            intent_id="intent:test",
            goal="generate_sales_report",
            parameters={
                "date": "2026-08-14",
            },
        )

        self.assertEqual(
            intent.parameters["date"],
            "2026-08-14",
        )

    def test_intent_accepts_constraints(self):
        intent = Intent(
            intent_id="intent:test",
            goal="generate_sales_report",
            constraints={
                "format": "pdf",
            },
        )

        self.assertEqual(
            intent.constraints["format"],
            "pdf",
        )

    def test_optional_mappings_default_to_empty(self):
        intent = Intent(
            intent_id="intent:test",
            goal="test",
        )

        self.assertEqual(
            dict(intent.parameters),
            {},
        )

        self.assertEqual(
            dict(intent.constraints),
            {},
        )

        self.assertEqual(
            dict(intent.metadata),
            {},
        )

    def test_empty_intent_id_rejected(self):
        with self.assertRaises(ValueError):
            Intent(
                intent_id="",
                goal="test",
            )

    def test_whitespace_intent_id_rejected(self):
        with self.assertRaises(ValueError):
            Intent(
                intent_id="   ",
                goal="test",
            )

    def test_empty_goal_rejected(self):
        with self.assertRaises(ValueError):
            Intent(
                intent_id="intent:test",
                goal="",
            )

    def test_whitespace_goal_rejected(self):
        with self.assertRaises(ValueError):
            Intent(
                intent_id="intent:test",
                goal="   ",
            )

    def test_invalid_intent_id_type_rejected(self):
        with self.assertRaises(TypeError):
            Intent(
                intent_id=123,
                goal="test",
            )

    def test_invalid_goal_type_rejected(self):
        with self.assertRaises(TypeError):
            Intent(
                intent_id="intent:test",
                goal=123,
            )

    def test_invalid_parameters_rejected(self):
        with self.assertRaises(TypeError):
            Intent(
                intent_id="intent:test",
                goal="test",
                parameters=[],
            )

    def test_invalid_constraints_rejected(self):
        with self.assertRaises(TypeError):
            Intent(
                intent_id="intent:test",
                goal="test",
                constraints=[],
            )

    def test_invalid_metadata_rejected(self):
        with self.assertRaises(TypeError):
            Intent(
                intent_id="intent:test",
                goal="test",
                metadata=[],
            )

    def test_intent_is_immutable(self):
        intent = Intent(
            intent_id="intent:test",
            goal="test",
        )

        with self.assertRaises(AttributeError):
            intent.goal = "changed"

    def test_parameters_are_immutable(self):
        intent = Intent(
            intent_id="intent:test",
            goal="test",
            parameters={
                "value": 1,
            },
        )

        with self.assertRaises(TypeError):
            intent.parameters["value"] = 2

    def test_constraints_are_immutable(self):
        intent = Intent(
            intent_id="intent:test",
            goal="test",
            constraints={
                "limit": 5,
            },
        )

        with self.assertRaises(TypeError):
            intent.constraints["limit"] = 10

    def test_metadata_is_immutable(self):
        intent = Intent(
            intent_id="intent:test",
            goal="test",
            metadata={
                "source": "test",
            },
        )

        with self.assertRaises(TypeError):
            intent.metadata["source"] = "other"

    def test_intent_does_not_require_runtime(self):
        intent = Intent(
            intent_id="intent:test",
            goal="test",
        )

        self.assertFalse(
            hasattr(intent, "runtime")
        )

        self.assertFalse(
            hasattr(intent, "scheduler")
        )

        self.assertFalse(
            hasattr(intent, "task_executor")
        )

    def test_intent_does_not_require_agent(self):
        intent = Intent(
            intent_id="intent:test",
            goal="test",
        )

        self.assertFalse(
            hasattr(intent, "agent")
        )

        self.assertFalse(
            hasattr(intent, "handle")
        )

    def test_intent_does_not_require_model_provider(self):
        intent = Intent(
            intent_id="intent:test",
            goal="test",
        )

        self.assertFalse(
            hasattr(intent, "model")
        )

        self.assertFalse(
            hasattr(intent, "provider")
        )

    def test_ambiguous_intent_is_allowed(self):
        intent = Intent(
            intent_id="intent:test",
            goal="send_item",
            parameters={
                "recipient": "John",
            },
        )

        self.assertEqual(
            intent.goal,
            "send_item",
        )

        self.assertEqual(
            intent.parameters["recipient"],
            "John",
        )

    def test_intent_is_not_execution_plan(self):
        intent = Intent(
            intent_id="intent:test",
            goal="generate_report",
        )

        self.assertFalse(
            hasattr(intent, "steps")
        )

        self.assertFalse(
            hasattr(intent, "plan_id")
        )

    def test_intent_does_not_authorize_action(self):
        intent = Intent(
            intent_id="intent:test",
            goal="delete_data",
            metadata={
                "requested": True,
            },
        )

        self.assertFalse(
            hasattr(intent, "authorized")
        )

        self.assertFalse(
            hasattr(intent, "permission")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)