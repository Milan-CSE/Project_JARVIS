from __future__ import annotations

import unittest

from ai_os.foundation.config import (
    Configuration,
    ConfigurationManager,
    ConfigurationMissingError,
    ConfigurationSnapshot,
    ConfigurationSource,
    ConfigurationValidationError,
    ConfigurationValidator,
)
from ai_os.foundation.config.configuration import (
    MappingConfigurationSource,
)


class TrackingSource:
    def __init__(self, values):
        self.values = values
        self.calls = 0

    def load(self):
        self.calls += 1
        return self.values


class ValidatingConfiguration:
    def __init__(self):
        self.calls = 0
        self.snapshots = []

    def validate(self, snapshot):
        self.calls += 1
        self.snapshots.append(snapshot)
        if snapshot.contains("runtime.timeout"):
            value = snapshot.require("runtime.timeout")
            if not isinstance(value, int):
                raise ValueError("runtime.timeout must be int")
            if value <= 0:
                raise ValueError("runtime.timeout must be positive")


class ExplodingValidator:
    def validate(self, snapshot):
        raise RuntimeError("validator exploded")


class ConfigurationTests(unittest.TestCase):

    def create_manager(self, initial=None, validator=None):
        return ConfigurationManager(
            initial or {
                "runtime.timeout": 30,
                "providers.default": "local",
            },
            validator=validator,
        )

    # ------------------------------------------------------------
    # Contracts
    # ------------------------------------------------------------

    def test_manager_matches_configuration_protocol(self):
        manager = self.create_manager()
        self.assertIsInstance(manager, Configuration)

    def test_source_matches_protocol(self):
        source = MappingConfigurationSource({"a.b": 1})
        self.assertIsInstance(source, ConfigurationSource)

    def test_validator_matches_protocol(self):
        validator = ValidatingConfiguration()
        self.assertIsInstance(
            validator,
            ConfigurationValidator,
        )

    # ------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------

    def test_snapshot_is_immutable(self):
        snapshot = ConfigurationSnapshot(
            version="config:1",
            values={"runtime.timeout": 30},
        )

        with self.assertRaises(AttributeError):
            snapshot.version = "config:2"

    def test_snapshot_values_are_immutable(self):
        snapshot = ConfigurationSnapshot(
            version="config:1",
            values={"runtime.timeout": 30},
        )

        with self.assertRaises(TypeError):
            snapshot.values["runtime.timeout"] = 60

    def test_nested_mapping_is_immutable(self):
        snapshot = ConfigurationSnapshot(
            version="config:1",
            values={
                "provider.options": {
                    "region": "in",
                }
            },
        )

        nested = snapshot.require(
            "provider.options"
        )

        with self.assertRaises(TypeError):
            nested["region"] = "us"

    def test_nested_list_is_immutable(self):
        snapshot = ConfigurationSnapshot(
            version="config:1",
            values={
                "tools.enabled": ["browser", "email"],
            },
        )

        value = snapshot.require(
            "tools.enabled"
        )

        self.assertIsInstance(value, tuple)

        with self.assertRaises(AttributeError):
            value.append("shell")

    def test_nested_set_is_immutable(self):
        snapshot = ConfigurationSnapshot(
            version="config:1",
            values={
                "tools.capabilities": {"read", "write"},
            },
        )

        value = snapshot.require(
            "tools.capabilities"
        )

        self.assertIsInstance(
            value,
            frozenset,
        )

    # ------------------------------------------------------------
    # Key access
    # ------------------------------------------------------------

    def test_get_existing_key(self):
        manager = self.create_manager()

        self.assertEqual(
            manager.get("runtime.timeout"),
            30,
        )

    def test_get_missing_key_returns_default(self):
        manager = self.create_manager()

        self.assertEqual(
            manager.get(
                "missing.key",
                "fallback",
            ),
            "fallback",
        )

    def test_require_existing_key(self):
        manager = self.create_manager()

        self.assertEqual(
            manager.require("runtime.timeout"),
            30,
        )

    def test_require_missing_key_raises(self):
        manager = self.create_manager()

        with self.assertRaises(
            ConfigurationMissingError
        ):
            manager.require("missing.key")

    def test_contains(self):
        manager = self.create_manager()

        self.assertTrue(
            manager.contains(
                "runtime.timeout"
            )
        )

        self.assertFalse(
            manager.contains(
                "missing.key"
            )
        )

    def test_namespace_isolation(self):
        manager = self.create_manager(
            {
                "runtime.timeout": 30,
                "runtime.workers": 2,
                "providers.default": "local",
            }
        )

        runtime = manager.namespace(
            "runtime"
        )

        self.assertEqual(
            runtime["runtime.timeout"],
            30,
        )
        self.assertEqual(
            runtime["runtime.workers"],
            2,
        )
        self.assertNotIn(
            "providers.default",
            runtime,
        )

    # ------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------

    def test_invalid_key_rejected(self):
        with self.assertRaises(ValueError):
            ConfigurationSnapshot(
                "config:1",
                {"runtime..timeout": 30},
            )

    def test_non_string_key_rejected(self):
        with self.assertRaises(TypeError):
            ConfigurationSnapshot(
                "config:1",
                {1: "bad"},
            )

    def test_validator_called(self):
        validator = ValidatingConfiguration()

        manager = self.create_manager(
            validator=validator
        )

        self.assertEqual(
            validator.calls,
            1,
        )

        manager.update(
            {"runtime.timeout": 40}
        )

        self.assertEqual(
            validator.calls,
            2,
        )

    def test_invalid_candidate_does_not_replace_current(self):
        validator = ValidatingConfiguration()
        manager = self.create_manager(
            validator=validator
        )

        before = manager.snapshot()

        with self.assertRaises(
            ConfigurationValidationError
        ):
            manager.update(
                {"runtime.timeout": 0}
            )

        after = manager.snapshot()

        self.assertIs(
            before,
            after,
        )
        self.assertEqual(
            manager.require("runtime.timeout"),
            30,
        )

    def test_validator_unexpected_error_is_wrapped(self):
        with self.assertRaises(
            ConfigurationValidationError
        ):
            self.create_manager(
                validator=ExplodingValidator()
            )

    # ------------------------------------------------------------
    # Source loading
    # ------------------------------------------------------------

    def test_source_is_loaded(self):
        source = TrackingSource(
            {
                "providers.default": "remote",
            }
        )

        manager = ConfigurationManager(
            sources=(source,)
        )

        self.assertEqual(
            source.calls,
            1,
        )
        self.assertEqual(
            manager.get(
                "providers.default"
            ),
            "remote",
        )

    def test_initial_values_override_sources(self):
        source = MappingConfigurationSource(
            {
                "runtime.timeout": 10,
            }
        )

        manager = ConfigurationManager(
            initial={
                "runtime.timeout": 30,
            },
            sources=(source,),
        )

        self.assertEqual(
            manager.get("runtime.timeout"),
            30,
        )

    def test_multiple_sources_are_deterministic(self):
        first = MappingConfigurationSource(
            {"provider": "first"}
        )
        second = MappingConfigurationSource(
            {"provider": "second"}
        )

        manager = ConfigurationManager(
            sources=(first, second)
        )

        self.assertEqual(
            manager.get("provider"),
            "second",
        )

    def test_invalid_source_return_rejected(self):
        class BadSource:
            def load(self):
                return "invalid"

        with self.assertRaises(TypeError):
            ConfigurationManager(
                sources=(BadSource(),)
            )

    # ------------------------------------------------------------
    # Atomic updates / versions
    # ------------------------------------------------------------

    def test_update_is_atomic(self):
        manager = self.create_manager()

        before = manager.snapshot()

        after = manager.update(
            {
                "runtime.timeout": 45,
                "runtime.workers": 4,
            }
        )

        self.assertIsNot(
            before,
            after,
        )

        self.assertEqual(
            after.get("runtime.timeout"),
            45,
        )

        self.assertEqual(
            after.get("runtime.workers"),
            4,
        )

    def test_version_advances(self):
        manager = self.create_manager()

        first = manager.snapshot()
        second = manager.update(
            {"runtime.timeout": 40}
        )
        third = manager.update(
            {"runtime.timeout": 50}
        )

        self.assertEqual(first.version, "config:0")
        self.assertEqual(second.version, "config:1")
        self.assertEqual(third.version, "config:2")

    def test_remove_is_atomic(self):
        manager = self.create_manager()

        before = manager.snapshot()

        after = manager.remove(
            "runtime.timeout"
        )

        self.assertIsNot(
            before,
            after,
        )

        self.assertFalse(
            after.contains("runtime.timeout")
        )

    def test_remove_multiple_keys(self):
        manager = self.create_manager()

        after = manager.remove(
            (
                "runtime.timeout",
                "providers.default",
            )
        )

        self.assertFalse(
            after.contains("runtime.timeout")
        )
        self.assertFalse(
            after.contains("providers.default")
        )

    # ------------------------------------------------------------
    # Boundary safety
    # ------------------------------------------------------------

    def test_manager_has_no_execute_api(self):
        manager = self.create_manager()

        self.assertFalse(
            hasattr(manager, "execute")
        )
        self.assertFalse(
            hasattr(manager, "execute_tool")
        )

    def test_manager_has_no_runtime_api(self):
        manager = self.create_manager()

        self.assertFalse(
            hasattr(manager, "runtime_executor")
        )
        self.assertFalse(
            hasattr(manager, "scheduler")
        )

    def test_manager_has_no_security_api(self):
        manager = self.create_manager()

        self.assertFalse(
            hasattr(manager, "authorize")
        )
        self.assertFalse(
            hasattr(manager, "security")
        )

    def test_manager_has_no_identity_api(self):
        manager = self.create_manager()

        self.assertFalse(
            hasattr(manager, "create_identity")
        )

    def test_manager_has_no_plugin_lifecycle_api(self):
        manager = self.create_manager()

        self.assertFalse(
            hasattr(manager, "load_plugin")
        )
        self.assertFalse(
            hasattr(manager, "initialize_plugin")
        )

    def test_manager_has_no_persistence_api(self):
        manager = self.create_manager()

        self.assertFalse(
            hasattr(manager, "save_to_disk")
        )
        self.assertFalse(
            hasattr(manager, "database")
        )

    def test_configuration_reusable(self):
        manager = self.create_manager()

        first = manager.update(
            {"runtime.timeout": 40}
        )

        second = manager.update(
            {"runtime.timeout": 50}
        )

        self.assertEqual(
            first.get("runtime.timeout"),
            40,
        )
        self.assertEqual(
            second.get("runtime.timeout"),
            50,
        )

        self.assertEqual(
            manager.get("runtime.timeout"),
            50,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
