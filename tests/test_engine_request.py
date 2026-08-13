import unittest

from ai_os.engines import EngineRequest, EngineType
from ai_os.identity import Identity, IdentityType


def create_identity():
    return Identity(
        identity_id="identity:user:123",
        principal="user:123",
        identity_type=IdentityType.USER,
    )


class EngineRequestTests(unittest.TestCase):

    def test_valid_request(self):
        request = EngineRequest(
            request_id="request:123",
            identity=create_identity(),
            input={"task": "plan"},
        )

        self.assertEqual(
            request.request_id,
            "request:123",
        )

        self.assertEqual(
            request.identity.identity_id,
            "identity:user:123",
        )

        self.assertEqual(
            request.input["task"],
            "plan",
        )

    def test_request_is_immutable(self):
        request = EngineRequest(
            "request:123",
            create_identity(),
            {"task": "plan"},
        )

        with self.assertRaises(AttributeError):
            request.request_id = "request:456"

    def test_input_is_immutable(self):
        request = EngineRequest(
            "request:123",
            create_identity(),
            {"task": "plan"},
        )

        with self.assertRaises(TypeError):
            request.input["task"] = "changed"

    def test_metadata_is_immutable(self):
        request = EngineRequest(
            "request:123",
            create_identity(),
            {"task": "plan"},
            metadata={"source": "test"},
        )

        with self.assertRaises(TypeError):
            request.metadata["source"] = "changed"

    def test_empty_request_id_rejected(self):
        with self.assertRaises(ValueError):
            EngineRequest(
                "",
                create_identity(),
                {"task": "plan"},
            )

    def test_invalid_request_id_rejected(self):
        with self.assertRaises(TypeError):
            EngineRequest(
                123,
                create_identity(),
                {"task": "plan"},
            )

    def test_invalid_identity_rejected(self):
        with self.assertRaises(TypeError):
            EngineRequest(
                "request:123",
                "identity:user:123",
                {"task": "plan"},
            )

    def test_non_json_input_rejected(self):
        with self.assertRaises(TypeError):
            EngineRequest(
                "request:123",
                create_identity(),
                {"bad": object()},
            )

    def test_non_json_metadata_rejected(self):
        with self.assertRaises(TypeError):
            EngineRequest(
                "request:123",
                create_identity(),
                {"task": "plan"},
                metadata={"bad": object()},
            )

    def test_round_trip(self):
        request = EngineRequest(
            "request:123",
            create_identity(),
            {
                "task": "plan",
                "steps": ["one", "two"],
            },
            metadata={
                "source": "test",
            },
        )

        restored = EngineRequest.from_json(
            request.to_json()
        )

        self.assertEqual(
            restored.to_dict(),
            request.to_dict(),
        )

    def test_identity_is_preserved(self):
        request = EngineRequest(
            "request:123",
            create_identity(),
            {"task": "plan"},
        )

        restored = EngineRequest.from_json(
            request.to_json()
        )

        self.assertEqual(
            restored.identity.identity_id,
            "identity:user:123",
        )

        self.assertEqual(
            restored.identity.identity_type,
            IdentityType.USER,
        )

    def test_identity_is_not_authorization(self):
        request = EngineRequest(
            "request:123",
            create_identity(),
            {"task": "plan"},
        )

        self.assertFalse(
            hasattr(request.identity, "authorized")
        )

    def test_no_credentials_in_request_contract(self):
        request = EngineRequest(
            "request:123",
            create_identity(),
            {"task": "plan"},
        )

        self.assertFalse(hasattr(request, "password"))
        self.assertFalse(hasattr(request, "token"))
        self.assertFalse(hasattr(request, "credential"))

    def test_nested_input_is_immutable(self):
        request = EngineRequest(
            "request:123",
            create_identity(),
            {
                "config": {
                    "mode": "safe",
                    "items": ["a", "b"],
                }
            },
        )

        with self.assertRaises(TypeError):
            request.input["config"]["mode"] = "unsafe"

        with self.assertRaises(TypeError):
            request.input["config"]["items"][0] = "changed"

    def test_empty_metadata_is_allowed(self):
        request = EngineRequest(
            "request:123",
            create_identity(),
            {"task": "plan"},
        )

        self.assertEqual(
            dict(request.metadata),
            {},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)