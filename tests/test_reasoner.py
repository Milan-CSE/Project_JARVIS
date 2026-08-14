import unittest

from ai_os.intelligence import (
    IntelligenceContext,
    Reasoner,
)


class ValidReasoner:

    def reason(
        self,
        context,
        cancellation_token=None,
    ):
        return {
            "kind": "test",
        }


class MissingReasonReasoner:
    pass


class WrongReasoner:

    def reason(self):
        return None


class ReasonerTests(unittest.TestCase):

    def test_valid_implementation_matches_protocol(self):
        reasoner = ValidReasoner()

        self.assertIsInstance(
            reasoner,
            Reasoner,
        )

    def test_invalid_reasoner_rejected(self):
        reasoner = MissingReasonReasoner()

        self.assertFalse(
            isinstance(
                reasoner,
                Reasoner,
            )
        )

    def test_reasoner_is_structural_contract(self):
        reasoner = ValidReasoner()

        self.assertIsInstance(
            reasoner,
            Reasoner,
        )

        self.assertNotIn(
            Reasoner,
            ValidReasoner.__bases__,
        )

    def test_reason_accepts_intelligence_context(self):
        reasoner = ValidReasoner()

        context = IntelligenceContext(
            input="test request",
        )

        result = reasoner.reason(
            context,
        )

        self.assertEqual(
            result,
            {"kind": "test"},
        )

    def test_cancellation_is_optional(self):
        reasoner = ValidReasoner()

        context = IntelligenceContext(
            input="test request",
        )

        result = reasoner.reason(
            context,
            None,
        )

        self.assertEqual(
            result,
            {"kind": "test"},
        )

    def test_reasoner_does_not_require_runtime(self):
        reasoner = ValidReasoner()

        self.assertFalse(
            hasattr(reasoner, "runtime")
        )

        self.assertFalse(
            hasattr(reasoner, "execute")
        )

    def test_reasoner_does_not_require_scheduler(self):
        reasoner = ValidReasoner()

        self.assertFalse(
            hasattr(reasoner, "scheduler")
        )

        self.assertFalse(
            hasattr(reasoner, "schedule")
        )

    def test_reasoner_does_not_require_task_executor(self):
        reasoner = ValidReasoner()

        self.assertFalse(
            hasattr(reasoner, "task_executor")
        )

        self.assertFalse(
            hasattr(reasoner, "execute_task")
        )

    def test_reasoner_does_not_require_task_registry(self):
        reasoner = ValidReasoner()

        self.assertFalse(
            hasattr(reasoner, "task_registry")
        )

        self.assertFalse(
            hasattr(reasoner, "registry")
        )

    def test_reasoner_does_not_require_engine(self):
        reasoner = ValidReasoner()

        self.assertFalse(
            hasattr(reasoner, "engine")
        )

    def test_reasoner_does_not_require_agent(self):
        reasoner = ValidReasoner()

        self.assertFalse(
            hasattr(reasoner, "agent")
        )

        self.assertFalse(
            hasattr(reasoner, "handle")
        )

    def test_reasoner_does_not_require_model_provider(self):
        reasoner = ValidReasoner()

        self.assertFalse(
            hasattr(reasoner, "model")
        )

        self.assertFalse(
            hasattr(reasoner, "provider")
        )

    def test_reasoner_does_not_create_execution_plan(self):
        reasoner = ValidReasoner()

        self.assertFalse(
            hasattr(reasoner, "plan")
        )

        self.assertFalse(
            hasattr(reasoner, "execution_plan")
        )

    def test_reasoner_does_not_execute(self):
        reasoner = ValidReasoner()

        self.assertFalse(
            hasattr(reasoner, "execute")
        )

        self.assertFalse(
            hasattr(reasoner, "run")
        )

    def test_reasoner_does_not_store_global_request_state(self):
        reasoner = ValidReasoner()

        self.assertFalse(
            hasattr(reasoner, "current_request")
        )

        self.assertFalse(
            hasattr(reasoner, "current_user")
        )

        self.assertFalse(
            hasattr(reasoner, "current_context")
        )

    def test_reasoner_can_receive_different_contexts(self):
        reasoner = ValidReasoner()

        first = IntelligenceContext(
            input="first",
        )

        second = IntelligenceContext(
            input="second",
        )

        first_result = reasoner.reason(first)
        second_result = reasoner.reason(second)

        self.assertEqual(
            first_result,
            {"kind": "test"},
        )

        self.assertEqual(
            second_result,
            {"kind": "test"},
        )

    def test_context_remains_immutable(self):
        reasoner = ValidReasoner()

        context = IntelligenceContext(
            input={
                "value": "original",
            },
        )

        reasoner.reason(context)

        self.assertEqual(
            context.input["value"],
            "original",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)