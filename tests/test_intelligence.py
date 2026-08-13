import unittest

from ai_os.intelligence import Intelligence


class ValidIntelligence:

    def decide(
        self,
        input,
        cancellation_token=None,
    ):
        return {
            "kind": "test",
        }


class MissingDecideIntelligence:

    pass


class WrongIntelligence:

    def decide(self):
        return None


class IntelligenceTests(unittest.TestCase):

    def test_valid_implementation_matches_protocol(self):
        intelligence = ValidIntelligence()

        self.assertIsInstance(
            intelligence,
            Intelligence,
        )

    def test_invalid_intelligence_rejected(self):
        intelligence = MissingDecideIntelligence()

        self.assertFalse(
            isinstance(
                intelligence,
                Intelligence,
            )
        )

    def test_structural_contract(self):
        intelligence = ValidIntelligence()

        self.assertIsInstance(
            intelligence,
            Intelligence,
        )

        self.assertNotIn(
            Intelligence,
            ValidIntelligence.__bases__,
        )

    def test_intelligence_does_not_require_engine(self):
        intelligence = ValidIntelligence()

        self.assertFalse(
            hasattr(intelligence, "engine")
        )

        self.assertFalse(
            hasattr(intelligence, "route")
        )

    def test_intelligence_does_not_require_scheduler(self):
        intelligence = ValidIntelligence()

        self.assertFalse(
            hasattr(intelligence, "scheduler")
        )

        self.assertFalse(
            hasattr(intelligence, "schedule")
        )

    def test_intelligence_does_not_require_task_executor(self):
        intelligence = ValidIntelligence()

        self.assertFalse(
            hasattr(intelligence, "task_executor")
        )

        self.assertFalse(
            hasattr(intelligence, "execute_task")
        )

    def test_intelligence_does_not_require_task_registry(self):
        intelligence = ValidIntelligence()

        self.assertFalse(
            hasattr(intelligence, "registry")
        )

        self.assertFalse(
            hasattr(intelligence, "task_registry")
        )

    def test_intelligence_does_not_require_runtime(self):
        intelligence = ValidIntelligence()

        self.assertFalse(
            hasattr(intelligence, "runtime")
        )

        self.assertFalse(
            hasattr(intelligence, "execute")
        )

    def test_intelligence_does_not_require_agent(self):
        intelligence = ValidIntelligence()

        self.assertFalse(
            hasattr(intelligence, "agent")
        )

        self.assertFalse(
            hasattr(intelligence, "handle")
        )

    def test_decide_is_not_execution(self):
        intelligence = ValidIntelligence()

        result = intelligence.decide(
            "test input"
        )

        self.assertEqual(
            result,
            {"kind": "test"},
        )

    def test_cancellation_is_optional(self):
        intelligence = ValidIntelligence()

        result = intelligence.decide(
            "test input",
            None,
        )

        self.assertEqual(
            result,
            {"kind": "test"},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)