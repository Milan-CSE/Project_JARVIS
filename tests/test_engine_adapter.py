import unittest

from ai_os.engines import (
    EngineRequest,
    EngineResult,
    EngineStatus,
)
from ai_os.engines.adapters import EngineAdapter
from ai_os.identity import Identity, IdentityType


def create_identity():
    return Identity(
        identity_id="identity:user:123",
        principal="user:123",
        identity_type=IdentityType.USER,
    )


def create_request():
    return EngineRequest(
        request_id="request:123",
        identity=create_identity(),
        input={
            "task": "plan",
        },
    )


class ValidAdapter:

    def adapt_request(self, request):
        return {
            "request_id": request.request_id,
            "task": request.input["task"],
        }

    def adapt_result(self, result):
        return EngineResult(
            status=EngineStatus.SUCCESS,
            output=result,
        )


class MissingRequestAdapter:

    def adapt_result(self, result):
        return EngineResult(
            status=EngineStatus.SUCCESS,
            output=result,
        )


class MissingResultAdapter:

    def adapt_request(self, request):
        return request.input


class EngineAdapterTests(unittest.TestCase):

    def test_valid_adapter_matches_protocol(self):
        adapter = ValidAdapter()

        self.assertIsInstance(
            adapter,
            EngineAdapter,
        )

    def test_request_is_adapted(self):
        adapter = ValidAdapter()

        external_request = adapter.adapt_request(
            create_request()
        )

        self.assertEqual(
            external_request["request_id"],
            "request:123",
        )

        self.assertEqual(
            external_request["task"],
            "plan",
        )

    def test_result_is_adapted(self):
        adapter = ValidAdapter()

        result = adapter.adapt_result(
            {
                "output": "planned",
            }
        )

        self.assertIsInstance(
            result,
            EngineResult,
        )

        self.assertEqual(
            result.status,
            EngineStatus.SUCCESS,
        )

    def test_invalid_adapter_without_request_adapter_rejected(self):
        adapter = MissingRequestAdapter()

        self.assertFalse(
            isinstance(
                adapter,
                EngineAdapter,
            )
        )

    def test_invalid_adapter_without_result_adapter_rejected(self):
        adapter = MissingResultAdapter()

        self.assertFalse(
            isinstance(
                adapter,
                EngineAdapter,
            )
        )

    def test_adapter_does_not_become_engine(self):
        from ai_os.engines import Engine

        adapter = ValidAdapter()

        self.assertFalse(
            isinstance(
                adapter,
                Engine,
            )
        )

    def test_adapter_does_not_execute_runtime(self):
        adapter = ValidAdapter()

        external_request = adapter.adapt_request(
            create_request()
        )

        self.assertIsInstance(
            external_request,
            dict,
        )

        self.assertNotIn(
            "execute",
            external_request,
        )

    def test_adapter_preserves_request_identity_when_needed(self):
        class IdentityAdapter:

            def adapt_request(self, request):
                return {
                    "identity_id":
                        request.identity.identity_id,
                    "principal":
                        request.identity.principal,
                }

            def adapt_result(self, result):
                return EngineResult(
                    status=EngineStatus.SUCCESS,
                    output=result,
                )

        adapter = IdentityAdapter()

        external_request = adapter.adapt_request(
            create_request()
        )

        self.assertEqual(
            external_request["identity_id"],
            "identity:user:123",
        )

        self.assertEqual(
            external_request["principal"],
            "user:123",
        )

    def test_adapter_does_not_authorize_identity(self):
        adapter = ValidAdapter()

        external_request = adapter.adapt_request(
            create_request()
        )

        self.assertNotIn(
            "authorized",
            external_request,
        )

    def test_adapter_does_not_route(self):
        adapter = ValidAdapter()

        self.assertFalse(
            hasattr(adapter, "route")
        )

    def test_adapter_does_not_require_engine_inheritance(self):
        adapter = ValidAdapter()

        self.assertIsInstance(
            adapter,
            EngineAdapter,
        )

        self.assertNotIn(
            EngineAdapter,
            ValidAdapter.__bases__,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)