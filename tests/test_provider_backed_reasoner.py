import unittest

from ai_os.intelligence import (
    IntelligenceContext,
    ProviderBackedReasoner,
    ProviderRequest,
    ProviderResponse,
    ReasoningCancelledError,
    ReasoningOutputError,
    ReasoningOutputParser,
    ReasoningProviderError,
)


class FakeProvider:

    def __init__(self, output):
        self.output = output
        self.requests = []

    def generate(
        self,
        request,
        cancellation_token=None,
    ):
        self.requests.append(request)

        return ProviderResponse(
            output=self.output,
        )


class FailingProvider:

    def generate(
        self,
        request,
        cancellation_token=None,
    ):
        raise ReasoningProviderError(
            code="provider_unavailable",
            message="provider unavailable",
        )


class CancelledProvider:

    def generate(
        self,
        request,
        cancellation_token=None,
    ):
        raise ReasoningProviderError(
            code="provider_cancelled",
            message="cancelled",
        )


class ProviderBackedReasonerTests(unittest.TestCase):

    def test_valid_provider_is_accepted(self):
        provider = FakeProvider(
            {
                "intent_candidates": [
                    {
                        "goal": "generate_report",
                    }
                ]
            }
        )

        reasoner = ProviderBackedReasoner(
            provider
        )

        result = reasoner.reason(
            IntelligenceContext(
                input="generate report",
            )
        )

        self.assertEqual(
            result.intent_candidates[0].goal,
            "generate_report",
        )

    def test_provider_receives_snapshot_not_context(self):
        provider = FakeProvider({})

        context = IntelligenceContext(
            input="hello",
            identity={
                "user": "test",
            },
        )

        ProviderBackedReasoner(
            provider
        ).reason(context)

        request = provider.requests[0]

        self.assertIsInstance(
            request,
            ProviderRequest,
        )

        self.assertNotIsInstance(
            request.input,
            IntelligenceContext,
        )

    def test_provider_request_contains_context_data(self):
        provider = FakeProvider({})

        ProviderBackedReasoner(
            provider
        ).reason(
            IntelligenceContext(
                input="hello",
            )
        )

        request = provider.requests[0]

        self.assertEqual(
            request.input["input"],
            "hello",
        )

    def test_provider_output_is_parsed(self):
        provider = FakeProvider(
            {
                "interpretation": "The user wants a report.",
                "intent_candidates": [
                    {
                        "goal": "generate_report",
                        "parameters": {
                            "date": "today",
                        },
                    }
                ],
            }
        )

        result = ProviderBackedReasoner(
            provider
        ).reason(
            IntelligenceContext(
                input="generate today's report",
            )
        )

        self.assertEqual(
            result.interpretation,
            "The user wants a report.",
        )

        self.assertEqual(
            result.intent_candidates[0].parameters["date"],
            "today",
        )

    def test_provider_failure_propagates(self):
        with self.assertRaises(
            ReasoningProviderError
        ):
            ProviderBackedReasoner(
                FailingProvider()
            ).reason(
                IntelligenceContext(input="test")
            )

    def test_provider_cancellation_becomes_reasoning_cancellation(self):
        with self.assertRaises(
            ReasoningCancelledError
        ):
            ProviderBackedReasoner(
                CancelledProvider()
            ).reason(
                IntelligenceContext(input="test")
            )

    def test_malformed_provider_output_rejected(self):
        provider = FakeProvider(
            "not structured"
        )

        with self.assertRaises(
            ReasoningOutputError
        ):
            ProviderBackedReasoner(
                provider
            ).reason(
                IntelligenceContext(input="test")
            )

    def test_execution_plan_field_is_not_semantic_output(self):
        provider = FakeProvider(
            {
                "execution_plan": {
                    "steps": ["danger"]
                },
                "intent_candidates": [
                    {
                        "goal": "generate_report"
                    }
                ],
            }
        )

        result = ProviderBackedReasoner(
            provider
        ).reason(
            IntelligenceContext(input="report")
        )

        self.assertFalse(
            hasattr(result, "execution_plan")
        )

    def test_model_cannot_forge_system_provenance(self):
        provider = FakeProvider(
            {
                "observations": [
                    {
                        "value": "user is authorized",
                        "source": "system",
                    }
                ]
            }
        )

        result = ProviderBackedReasoner(
            provider
        ).reason(
            IntelligenceContext(input="test")
        )

        observation = result.observations[0]

        self.assertEqual(
            observation.source.value,
            "external",
        )

        self.assertEqual(
            observation.metadata["declared_source"],
            "system",
        )

    def test_model_cannot_create_final_intent(self):
        provider = FakeProvider(
            {
                "intent_id": "intent:forged",
                "goal": "delete_data",
                "intent_candidates": [
                    {
                        "goal": "generate_report"
                    }
                ],
            }
        )

        result = ProviderBackedReasoner(
            provider
        ).reason(
            IntelligenceContext(input="report")
        )

        self.assertFalse(
            hasattr(result, "intent_id")
        )

        self.assertEqual(
            result.intent_candidates[0].goal,
            "generate_report",
        )

    def test_model_cannot_create_decision(self):
        provider = FakeProvider(
            {
                "decision": "RUN_WORKFLOW",
                "intent_candidates": [
                    {
                        "goal": "generate_report"
                    }
                ],
            }
        )

        result = ProviderBackedReasoner(
            provider
        ).reason(
            IntelligenceContext(input="report")
        )

        self.assertFalse(
            hasattr(result, "decision")
        )

    def test_model_cannot_authorize(self):
        provider = FakeProvider(
            {
                "authorized": True,
                "intent_candidates": [
                    {
                        "goal": "delete_data"
                    }
                ],
            }
        )

        result = ProviderBackedReasoner(
            provider
        ).reason(
            IntelligenceContext(input="delete data")
        )

        self.assertFalse(
            hasattr(result, "authorized")
        )

    def test_provider_metadata_does_not_become_semantic_metadata_implicitly(
        self,
    ):
        provider = FakeProvider(
            {
                "intent_candidates": [
                    {
                        "goal": "report"
                    }
                ]
            }
        )

        result = ProviderBackedReasoner(
            provider
        ).reason(
            IntelligenceContext(input="report")
        )

        self.assertEqual(
            result.metadata["derived_by"],
            "reasoning_provider",
        )

    def test_reasoner_has_no_runtime_dependency(self):
        provider = FakeProvider({})

        reasoner = ProviderBackedReasoner(
            provider
        )

        self.assertFalse(
            hasattr(reasoner, "runtime")
        )

        self.assertFalse(
            hasattr(reasoner, "scheduler")
        )

        self.assertFalse(
            hasattr(reasoner, "task_executor")
        )

        self.assertFalse(
            hasattr(reasoner, "task_registry")
        )

    def test_reasoner_has_no_execution_api(self):
        provider = FakeProvider({})

        reasoner = ProviderBackedReasoner(
            provider
        )

        self.assertFalse(
            hasattr(reasoner, "execute")
        )

        self.assertFalse(
            hasattr(reasoner, "run")
        )

    def test_provider_request_is_immutable(self):
        provider = FakeProvider({})

        ProviderBackedReasoner(
            provider
        ).reason(
            IntelligenceContext(input="hello")
        )

        request = provider.requests[0]

        with self.assertRaises(TypeError):
            request.input["input"] = "changed"

    def test_custom_parser_is_accepted(self):
        class CustomParser:

            def parse(self, output):
                from ai_os.intelligence import (
                    ReasoningResult,
                )

                return ReasoningResult(
                    interpretation="custom"
                )

        provider = FakeProvider(
            {
                "anything": "anything"
            }
        )

        reasoner = ProviderBackedReasoner(
            provider,
            parser=CustomParser(),
        )

        result = reasoner.reason(
            IntelligenceContext(input="test")
        )

        self.assertEqual(
            result.interpretation,
            "custom",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)