import unittest

from ai_os.intelligence import (
    IntelligenceContext,
    IntelligenceOrchestrationResult,
    IntelligenceOrchestrationStatus,
    IntelligenceOrchestrator,
)


class ValidOrchestrator:

    def orchestrate(
        self,
        context,
        cancellation_token=None,
    ):
        return IntelligenceOrchestrationResult(
            status=IntelligenceOrchestrationStatus.BLOCKED,
            context=context,
        )


class InvalidOrchestrator:
    pass


class IntelligenceOrchestrationTests(unittest.TestCase):

    def test_valid_implementation_matches_protocol(self):
        orchestrator = ValidOrchestrator()

        self.assertIsInstance(
            orchestrator,
            IntelligenceOrchestrator,
        )

    def test_invalid_implementation_rejected(self):
        self.assertFalse(
            isinstance(
                InvalidOrchestrator(),
                IntelligenceOrchestrator,
            )
        )

    def test_result_can_be_created(self):
        context = IntelligenceContext(
            input="test",
        )

        result = IntelligenceOrchestrationResult(
            status=IntelligenceOrchestrationStatus.BLOCKED,
            context=context,
        )

        self.assertEqual(
            result.status,
            IntelligenceOrchestrationStatus.BLOCKED,
        )

    def test_result_is_immutable(self):
        context = IntelligenceContext(
            input="test",
        )

        result = IntelligenceOrchestrationResult(
            status=IntelligenceOrchestrationStatus.BLOCKED,
            context=context,
        )

        with self.assertRaises(AttributeError):
            result.status = (
                IntelligenceOrchestrationStatus.FAILED
            )

    def test_context_is_preserved(self):
        context = IntelligenceContext(
            input="test",
        )

        result = IntelligenceOrchestrationResult(
            status=IntelligenceOrchestrationStatus.BLOCKED,
            context=context,
        )

        self.assertIs(
            result.context,
            context,
        )

    def test_partial_progress_is_allowed(self):
        context = IntelligenceContext(
            input="test",
        )

        result = IntelligenceOrchestrationResult(
            status=IntelligenceOrchestrationStatus.FAILED,
            context=context,
        )

        self.assertIsNone(result.intent)
        self.assertIsNone(result.decision)
        self.assertIsNone(result.proposal)
        self.assertIsNone(result.agent_decision)

    def test_statuses_exist(self):
        self.assertEqual(
            set(IntelligenceOrchestrationStatus),
            {
                IntelligenceOrchestrationStatus.COMPLETED,
                IntelligenceOrchestrationStatus.BLOCKED,
                IntelligenceOrchestrationStatus.FAILED,
                IntelligenceOrchestrationStatus.CANCELLED,
            },
        )

    def test_orchestrator_has_no_runtime_method(self):
        orchestrator = ValidOrchestrator()

        self.assertFalse(
            hasattr(orchestrator, "execute")
        )

        self.assertFalse(
            hasattr(orchestrator, "run_task")
        )

    def test_result_does_not_contain_execution_plan(self):
        context = IntelligenceContext(
            input="test",
        )

        result = IntelligenceOrchestrationResult(
            status=IntelligenceOrchestrationStatus.BLOCKED,
            context=context,
        )

        self.assertFalse(
            hasattr(result, "execution_plan")
        )

    def test_invalid_context_rejected(self):
        with self.assertRaises(TypeError):
            IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.BLOCKED,
                context="invalid",
            )

    def test_invalid_intent_rejected(self):
        context = IntelligenceContext(
            input="test",
        )

        with self.assertRaises(TypeError):
            IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.BLOCKED,
                context=context,
                intent="invalid",
            )

    def test_invalid_decision_rejected(self):
        context = IntelligenceContext(
            input="test",
        )

        with self.assertRaises(TypeError):
            IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.BLOCKED,
                context=context,
                decision="invalid",
            )

    def test_invalid_proposal_rejected(self):
        context = IntelligenceContext(
            input="test",
        )

        with self.assertRaises(TypeError):
            IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.BLOCKED,
                context=context,
                proposal="invalid",
            )

    def test_invalid_agent_decision_rejected(self):
        context = IntelligenceContext(
            input="test",
        )

        with self.assertRaises(TypeError):
            IntelligenceOrchestrationResult(
                status=IntelligenceOrchestrationStatus.BLOCKED,
                context=context,
                agent_decision="invalid",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)