from __future__ import annotations

import unittest

from ai_os.tools import (
    DefaultTool,
    DefaultToolContributionValidator,
    DefaultToolRegistry,
    ToolContribution,
    ToolContributionValidator,
    ToolEcosystemManager,
    ToolEcosystemResult,
)


class TrackingValidator:
    def __init__(self, error=None):
        self.calls = 0
        self.received = []
        self.error = error

    def validate(self, contribution):
        self.calls += 1
        self.received.append(contribution)
        if self.error is not None:
            raise self.error


class WrongValidator:
    pass


class EcosystemTests(unittest.TestCase):

    def create_tool(
        self,
        tool_id="tool:test",
        capability="test.capability",
    ):
        return DefaultTool(
            tool_id=tool_id,
            name=tool_id,
            version="1.0",
            description="test tool",
            capability=capability,
        )

    def create_contribution(
        self,
        contribution_id="contribution:test",
        tools=None,
        dependencies=(),
        compatibility=None,
        metadata=None,
    ):
        if tools is None:
            tools = (
                self.create_tool(),
            )

        return ToolContribution(
            contribution_id=contribution_id,
            name="Test Contribution",
            version="1.0",
            tools=tools,
            dependencies=dependencies,
            compatibility=(
                compatibility
                if compatibility is not None
                else {}
            ),
            metadata=(
                metadata
                if metadata is not None
                else {}
            ),
        )

    def create_manager(self, validator=None):
        return ToolEcosystemManager(
            DefaultToolRegistry(),
            validator=validator,
        )

    # ----------------------------------------------------------
    # Contribution contract
    # ----------------------------------------------------------

    def test_valid_contribution_matches_expected_shape(self):
        contribution = self.create_contribution()

        self.assertIsInstance(
            contribution,
            ToolContribution,
        )

    def test_contribution_is_immutable(self):
        contribution = self.create_contribution()

        with self.assertRaises(AttributeError):
            contribution.name = "changed"

    def test_contribution_metadata_is_immutable(self):
        contribution = self.create_contribution(
            metadata={"x": 1},
        )

        with self.assertRaises(TypeError):
            contribution.metadata["x"] = 2

    def test_empty_tools_rejected(self):
        with self.assertRaises(ValueError):
            self.create_contribution(
                tools=(),
            )

    def test_invalid_tool_rejected(self):
        with self.assertRaises(TypeError):
            self.create_contribution(
                tools=("invalid",),
            )

    def test_duplicate_tool_ids_within_contribution_rejected(self):
        tool = self.create_tool()
        contribution = ToolContribution(
            contribution_id="contribution:test",
            name="Test",
            version="1.0",
            tools=(tool, tool),
        )

        with self.assertRaises(ValueError):
            ToolEcosystemManager(
                DefaultToolRegistry()
            ).admit(contribution)

    def test_duplicate_dependencies_rejected(self):
        with self.assertRaises(ValueError):
            self.create_contribution(
                dependencies=("dep.one", "dep.one"),
            )

    def test_invalid_dependency_rejected(self):
        with self.assertRaises(TypeError):
            self.create_contribution(
                dependencies=(123,),
            )

    # ----------------------------------------------------------
    # Validator contract
    # ----------------------------------------------------------

    def test_default_validator_matches_protocol(self):
        self.assertIsInstance(
            DefaultToolContributionValidator(),
            ToolContributionValidator,
        )

    def test_invalid_validator_rejected(self):
        with self.assertRaises(TypeError):
            ToolEcosystemManager(
                DefaultToolRegistry(),
                validator=WrongValidator(),
            )

    def test_custom_validator_called_once(self):
        validator = TrackingValidator()
        contribution = self.create_contribution()

        manager = self.create_manager(
            validator=validator,
        )

        result = manager.admit(contribution)

        self.assertTrue(result.accepted)
        self.assertEqual(validator.calls, 1)
        self.assertIs(
            validator.received[0],
            contribution,
        )

    def test_validator_exception_propagates(self):
        validator = TrackingValidator(
            error=RuntimeError("validator failed"),
        )

        with self.assertRaises(RuntimeError):
            self.create_manager(
                validator=validator,
            ).admit(
                self.create_contribution()
            )

    # ----------------------------------------------------------
    # Admission
    # ----------------------------------------------------------

    def test_valid_contribution_is_admitted(self):
        registry = DefaultToolRegistry()
        manager = ToolEcosystemManager(
            registry
        )

        contribution = self.create_contribution()

        result = manager.admit(contribution)

        self.assertTrue(result.accepted)
        self.assertEqual(
            result.contribution_id,
            contribution.contribution_id,
        )
        self.assertEqual(
            result.tool_ids,
            ("tool:test",),
        )

    def test_admission_does_not_mutate_registry(self):
        registry = DefaultToolRegistry()
        manager = ToolEcosystemManager(
            registry
        )

        contribution = self.create_contribution()

        result = manager.admit(contribution)

        self.assertTrue(result.accepted)
        self.assertIsNone(
            registry.resolve("tool:test")
        )

    def test_duplicate_tool_id_is_rejected(self):
        registry = DefaultToolRegistry()
        registry.register(
            self.create_tool()
        )

        manager = ToolEcosystemManager(
            registry
        )

        result = manager.admit(
            self.create_contribution()
        )

        self.assertFalse(result.accepted)
        self.assertIn(
            "duplicate tool_id",
            result.reason,
        )

    def test_duplicate_tool_id_across_contribution_is_rejected(self):
        registry = DefaultToolRegistry()
        registry.register(
            self.create_tool(
                tool_id="tool:existing"
            )
        )

        contribution = self.create_contribution(
            contribution_id="contribution:new",
            tools=(
                self.create_tool(
                    tool_id="tool:existing"
                ),
                self.create_tool(
                    tool_id="tool:other",
                    capability="test.other",
                ),
            ),
        )

        result = ToolEcosystemManager(
            registry
        ).admit(contribution)

        self.assertFalse(result.accepted)
        self.assertEqual(
            registry.list_tools(),
            (
                registry.resolve("tool:existing"),
            ),
        )

    def test_capability_collision_is_allowed(self):
        registry = DefaultToolRegistry()
        registry.register(
            self.create_tool(
                tool_id="tool:existing",
                capability="email.send",
            )
        )

        contribution = self.create_contribution(
            tools=(
                self.create_tool(
                    tool_id="tool:new",
                    capability="email.send",
                ),
            ),
        )

        result = ToolEcosystemManager(
            registry
        ).admit(contribution)

        self.assertTrue(result.accepted)

    def test_duplicate_contribution_id_is_rejected(self):
        manager = self.create_manager()
        contribution = self.create_contribution()

        first = manager.admit(contribution)
        second = manager.admit(contribution)

        self.assertTrue(first.accepted)
        self.assertFalse(second.accepted)
        self.assertIn(
            "duplicate contribution_id",
            second.reason,
        )

    def test_failed_admission_does_not_consume_contribution_id(self):
        registry = DefaultToolRegistry()
        registry.register(
            self.create_tool()
        )

        manager = ToolEcosystemManager(
            registry
        )

        rejected = manager.admit(
            self.create_contribution()
        )

        self.assertFalse(rejected.accepted)

        # Same ID remains available for a later corrected contribution.
        corrected = self.create_contribution(
            tools=(
                self.create_tool(
                    tool_id="tool:corrected",
                ),
            ),
        )

        accepted = manager.admit(corrected)

        self.assertTrue(accepted.accepted)

    # ----------------------------------------------------------
    # No hidden execution / lifecycle / security responsibilities
    # ----------------------------------------------------------

    def test_manager_has_no_execute_api(self):
        manager = self.create_manager()

        self.assertFalse(hasattr(manager, "execute"))
        self.assertFalse(hasattr(manager, "execute_task"))

    def test_manager_has_no_runtime_api(self):
        manager = self.create_manager()

        self.assertFalse(
            hasattr(manager, "runtime_executor")
        )
        self.assertFalse(
            hasattr(manager, "scheduler")
        )
        self.assertFalse(
            hasattr(manager, "task_executor")
        )

    def test_manager_has_no_workflow_api(self):
        manager = self.create_manager()

        self.assertFalse(
            hasattr(manager, "workflow_runner")
        )
        self.assertFalse(
            hasattr(manager, "build_steps")
        )

    def test_manager_has_no_security_api(self):
        manager = self.create_manager()

        self.assertFalse(
            hasattr(manager, "authorize")
        )
        self.assertFalse(
            hasattr(manager, "security")
        )

    def test_manager_has_no_intelligence_api(self):
        manager = self.create_manager()

        self.assertFalse(hasattr(manager, "reason"))
        self.assertFalse(hasattr(manager, "plan"))
        self.assertFalse(hasattr(manager, "decide"))

    def test_manager_has_no_plugin_lifecycle_api(self):
        manager = self.create_manager()

        self.assertFalse(hasattr(manager, "load"))
        self.assertFalse(hasattr(manager, "initialize"))
        self.assertFalse(hasattr(manager, "pause"))
        self.assertFalse(hasattr(manager, "unload"))

    def test_manager_has_no_automatic_enablement(self):
        manager = self.create_manager()
        result = manager.admit(
            self.create_contribution()
        )

        self.assertTrue(result.accepted)

    def test_manager_has_no_automatic_adapter_creation(self):
        manager = self.create_manager()
        result = manager.admit(
            self.create_contribution()
        )

        self.assertTrue(result.accepted)
        self.assertFalse(
            hasattr(manager, "adapt")
        )

    # ----------------------------------------------------------
    # Result model
    # ----------------------------------------------------------

    def test_result_is_immutable(self):
        result = ToolEcosystemResult(
            accepted=True,
            contribution_id="contribution:test",
            tool_ids=("tool:test",),
            reason="accepted",
        )

        with self.assertRaises(AttributeError):
            result.accepted = False

    def test_result_metadata_is_immutable(self):
        result = ToolEcosystemResult(
            accepted=True,
            contribution_id="contribution:test",
            tool_ids=("tool:test",),
            reason="accepted",
            metadata={"stage": "test"},
        )

        with self.assertRaises(TypeError):
            result.metadata["stage"] = "changed"

    def test_result_type_is_correct(self):
        result = self.create_manager().admit(
            self.create_contribution()
        )

        self.assertIsInstance(
            result,
            ToolEcosystemResult,
        )

    # ----------------------------------------------------------
    # Reusability / state isolation
    # ----------------------------------------------------------

    def test_manager_is_reusable(self):
        manager = self.create_manager()

        first = manager.admit(
            self.create_contribution(
                contribution_id="contribution:first",
                tools=(
                    self.create_tool(
                        tool_id="tool:first",
                    ),
                ),
            )
        )

        second = manager.admit(
            self.create_contribution(
                contribution_id="contribution:second",
                tools=(
                    self.create_tool(
                        tool_id="tool:second",
                    ),
                ),
            )
        )

        self.assertTrue(first.accepted)
        self.assertTrue(second.accepted)

    def test_failed_admission_does_not_leak_registry_state(self):
        registry = DefaultToolRegistry()
        registry.register(
            self.create_tool(
                tool_id="tool:existing"
            )
        )

        manager = ToolEcosystemManager(
            registry
        )

        result = manager.admit(
            self.create_contribution(
                tools=(
                    self.create_tool(
                        tool_id="tool:existing"
                    ),
                    self.create_tool(
                        tool_id="tool:new",
                        capability="test.new",
                    ),
                )
            )
        )

        self.assertFalse(result.accepted)
        self.assertIsNone(
            registry.resolve("tool:new")
        )

    # ----------------------------------------------------------
    # Compatibility/dependency metadata remains declarative
    # ----------------------------------------------------------

    def test_compatibility_metadata_is_preserved(self):
        contribution = self.create_contribution(
            compatibility={
                "tool_contract": "1.x",
            }
        )

        self.assertEqual(
            contribution.compatibility["tool_contract"],
            "1.x",
        )

    def test_dependencies_are_preserved(self):
        contribution = self.create_contribution(
            dependencies=(
                "network",
                "oauth",
            )
        )

        self.assertEqual(
            contribution.dependencies,
            (
                "network",
                "oauth",
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
