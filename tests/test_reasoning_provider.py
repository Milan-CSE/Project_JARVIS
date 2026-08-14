import unittest

from ai_os.intelligence import (
    ProviderRequest,
    ProviderResponse,
    ReasoningProvider,
    ReasoningProviderError,
)
from ai_os.runtime.cancellation import CancellationSource


class ValidProvider:

    def generate(
        self,
        request,
        cancellation_token=None,
    ):
        return ProviderResponse(
            output={
                "text": "test",
            }
        )


class MissingProvider:
    pass


class ReasoningProviderTests(unittest.TestCase):

    def test_valid_provider_matches_protocol(self):
        provider = ValidProvider()

        self.assertIsInstance(
            provider,
            ReasoningProvider,
        )

    def test_invalid_provider_rejected_by_protocol(self):
        provider = MissingProvider()

        self.assertFalse(
            isinstance(
                provider,
                ReasoningProvider,
            )
        )

    def test_provider_request_can_be_created(self):
        request = ProviderRequest(
            input={
                "text": "hello",
            },
            requested_output={
                "type": "structured",
            },
        )

        self.assertEqual(
            request.input["text"],
            "hello",
        )

    def test_provider_request_is_immutable(self):
        request = ProviderRequest(
            input="hello",
        )

        with self.assertRaises(AttributeError):
            request.input = "changed"

    def test_nested_request_input_is_immutable(self):
        request = ProviderRequest(
            input={
                "options": {
                    "language": "English",
                },
            },
        )

        with self.assertRaises(TypeError):
            request.input["options"]["language"] = "Hindi"

    def test_provider_request_metadata_is_immutable(self):
        request = ProviderRequest(
            input="hello",
            metadata={
                "source": "reasoner",
            },
        )

        with self.assertRaises(TypeError):
            request.metadata["source"] = "other"

    def test_provider_response_can_be_created(self):
        response = ProviderResponse(
            output={
                "result": "hello",
            }
        )

        self.assertEqual(
            response.output["result"],
            "hello",
        )

    def test_provider_response_is_immutable(self):
        response = ProviderResponse(
            output="hello",
        )

        with self.assertRaises(AttributeError):
            response.output = "changed"

    def test_nested_response_output_is_immutable(self):
        response = ProviderResponse(
            output={
                "result": {
                    "value": "hello",
                },
            },
        )

        with self.assertRaises(TypeError):
            response.output["result"]["value"] = "changed"

    def test_usage_is_immutable(self):
        response = ProviderResponse(
            output="hello",
            usage={
                "tokens": 10,
            },
        )

        with self.assertRaises(TypeError):
            response.usage["tokens"] = 20

    def test_provider_request_does_not_require_model_id(self):
        request = ProviderRequest(
            input="hello",
        )

        self.assertFalse(
            hasattr(request, "model_id")
        )

    def test_provider_request_does_not_contain_credentials(self):
        request = ProviderRequest(
            input="hello",
        )

        self.assertFalse(
            hasattr(request, "api_key")
        )

        self.assertFalse(
            hasattr(request, "token")
        )

        self.assertFalse(
            hasattr(request, "password")
        )

    def test_provider_response_is_not_reasoning_result(self):
        response = ProviderResponse(
            output="raw provider result",
        )

        self.assertFalse(
            hasattr(response, "intent_candidates")
        )

        self.assertFalse(
            hasattr(response, "ambiguities")
        )

    def test_provider_does_not_execute(self):
        provider = ValidProvider()

        self.assertFalse(
            hasattr(provider, "execute")
        )

        self.assertFalse(
            hasattr(provider, "run")
        )

    def test_provider_does_not_require_runtime(self):
        provider = ValidProvider()

        self.assertFalse(
            hasattr(provider, "runtime")
        )

        self.assertFalse(
            hasattr(provider, "scheduler")
        )

        self.assertFalse(
            hasattr(provider, "task_executor")
        )

        self.assertFalse(
            hasattr(provider, "task_registry")
        )

    def test_provider_does_not_require_agent(self):
        provider = ValidProvider()

        self.assertFalse(
            hasattr(provider, "agent")
        )

    def test_provider_does_not_require_engine(self):
        provider = ValidProvider()

        self.assertFalse(
            hasattr(provider, "engine")
        )

    def test_provider_response_can_carry_usage(self):
        response = ProviderResponse(
            output="result",
            usage={
                "input_tokens": 10,
                "output_tokens": 20,
            },
        )

        self.assertEqual(
            response.usage["input_tokens"],
            10,
        )

    def test_provider_error_has_normalized_boundary(self):
        error = ReasoningProviderError(
            code="provider_unavailable",
            message="provider unavailable",
            details={
                "retryable": True,
            },
        )

        self.assertEqual(
            error.code,
            "provider_unavailable",
        )

        self.assertEqual(
            error.message,
            "provider unavailable",
        )

        self.assertTrue(
            error.details["retryable"],
        )

    def test_provider_error_details_are_immutable(self):
        error = ReasoningProviderError(
            code="provider_error",
            message="failed",
            details={
                "attempt": 1,
            },
        )

        with self.assertRaises(TypeError):
            error.details["attempt"] = 2

    def test_provider_error_rejects_empty_code(self):
        with self.assertRaises(ValueError):
            ReasoningProviderError(
                code="",
                message="failed",
            )

    def test_provider_error_rejects_empty_message(self):
        with self.assertRaises(ValueError):
            ReasoningProviderError(
                code="provider_error",
                message="",
            )

    def test_provider_can_receive_cancellation_token(self):
        source = CancellationSource()

        provider = ValidProvider()

        result = provider.generate(
            ProviderRequest(
                input="hello",
            ),
            source.token,
        )

        self.assertEqual(
            result.output["text"],
            "test",
        )

    def test_provider_response_can_be_empty(self):
        response = ProviderResponse(
            output=None,
        )

        self.assertIsNone(
            response.output,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)