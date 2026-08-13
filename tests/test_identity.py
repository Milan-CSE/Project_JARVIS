import unittest

from ai_os.identity import (
    Identity,
    IdentityResolver,
    IdentityType,
)


class TestIdentityResolver:
    def __init__(self):
        self.identities = {
            "identity:user:123": Identity(
                identity_id="identity:user:123",
                principal="user:123",
                identity_type=IdentityType.USER,
            )
        }

    def resolve(self, identity_id):
        return self.identities.get(identity_id)


class IdentityTests(unittest.TestCase):

    def test_identity_types(self):
        self.assertEqual(
            [item.value for item in IdentityType],
            [
                "user",
                "service",
                "agent",
                "system",
            ],
        )

    def test_create_user_identity(self):
        identity = Identity(
            identity_id="identity:user:123",
            principal="user:123",
            identity_type=IdentityType.USER,
        )

        self.assertEqual(
            identity.identity_id,
            "identity:user:123",
        )

        self.assertEqual(
            identity.principal,
            "user:123",
        )

        self.assertEqual(
            identity.identity_type,
            IdentityType.USER,
        )

    def test_non_user_identity_types(self):
        for identity_type in (
            IdentityType.SERVICE,
            IdentityType.AGENT,
            IdentityType.SYSTEM,
        ):
            identity = Identity(
                identity_id=f"identity:{identity_type.value}:1",
                principal=f"{identity_type.value}:1",
                identity_type=identity_type,
            )

            self.assertEqual(
                identity.identity_type,
                identity_type,
            )

    def test_identity_is_immutable(self):
        identity = Identity(
            "identity:user:123",
            "user:123",
            IdentityType.USER,
        )

        with self.assertRaises(AttributeError):
            identity.principal = "user:456"

    def test_metadata_is_immutable(self):
        identity = Identity(
            "identity:user:123",
            "user:123",
            IdentityType.USER,
            metadata={"locale": "en-IN"},
        )

        with self.assertRaises(TypeError):
            identity.metadata["locale"] = "en-US"

    def test_invalid_identity_id_rejected(self):
        with self.assertRaises(ValueError):
            Identity(
                "",
                "user:123",
                IdentityType.USER,
            )

    def test_invalid_principal_rejected(self):
        with self.assertRaises(ValueError):
            Identity(
                "identity:user:123",
                "",
                IdentityType.USER,
            )

    def test_invalid_identity_type_rejected(self):
        with self.assertRaises(TypeError):
            Identity(
                "identity:user:123",
                "user:123",
                "user",
            )

    def test_metadata_must_be_json_compatible(self):
        with self.assertRaises(TypeError):
            Identity(
                "identity:user:123",
                "user:123",
                IdentityType.USER,
                metadata={"bad": object()},
            )

    def test_identity_round_trip(self):
        identity = Identity(
            "identity:user:123",
            "user:123",
            IdentityType.USER,
            metadata={
                "display_name": "Milan",
                "locale": "en-IN",
            },
        )

        restored = Identity.from_json(identity.to_json())

        self.assertEqual(
            restored.to_dict(),
            identity.to_dict(),
        )

    def test_valid_resolver_matches_protocol(self):
        resolver = TestIdentityResolver()

        self.assertIsInstance(
            resolver,
            IdentityResolver,
        )

    def test_resolver_returns_identity(self):
        resolver = TestIdentityResolver()

        identity = resolver.resolve(
            "identity:user:123"
        )

        self.assertIsInstance(
            identity,
            Identity,
        )

    def test_unknown_identity_returns_none(self):
        resolver = TestIdentityResolver()

        result = resolver.resolve(
            "identity:user:999"
        )

        self.assertIsNone(result)

    def test_identity_contains_no_credential_fields(self):
        identity = Identity(
            "identity:user:123",
            "user:123",
            IdentityType.USER,
        )

        self.assertFalse(hasattr(identity, "password"))
        self.assertFalse(hasattr(identity, "token"))
        self.assertFalse(hasattr(identity, "credential"))
        self.assertFalse(hasattr(identity, "session"))

    def test_resolver_does_not_authenticate(self):
        resolver = TestIdentityResolver()

        identity = resolver.resolve(
            "identity:user:123"
        )

        # Resolving an identity is not authentication.
        self.assertFalse(
            hasattr(identity, "authenticated")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)