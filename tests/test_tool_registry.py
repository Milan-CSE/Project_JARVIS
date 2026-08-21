from __future__ import annotations

import unittest

from ai_os.tools import (
    DefaultTool,
    DefaultToolRegistry,
    DuplicateToolError,
    Tool,
    ToolRegistry,
    ToolRegistryFrozenError,
)


class ValidTool:
    def __init__(self, tool_id: str, capability: str):
        self._tool_id = tool_id
        self._capability = capability

    @property
    def tool_id(self) -> str:
        return self._tool_id

    @property
    def name(self) -> str:
        return self._tool_id

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def description(self) -> str:
        return "test tool"

    @property
    def capability(self) -> str:
        return self._capability

    @property
    def input_schema(self):
        return {}

    @property
    def required_permissions(self):
        return ()

    @property
    def metadata(self):
        return {}


class InvalidTool:
    pass


class ToolRegistryTests(unittest.TestCase):
    def make_tool(self, tool_id="tool.test", capability="test.action"):
        return DefaultTool(
            tool_id=tool_id,
            name="Test Tool",
            version="1.0",
            description="Test",
            capability=capability,
        )

    def test_valid_registry_matches_protocol(self):
        self.assertIsInstance(
            DefaultToolRegistry(),
            ToolRegistry,
        )

    def test_invalid_registration_rejected(self):
        registry = DefaultToolRegistry()
        with self.assertRaises(TypeError):
            registry.register(InvalidTool())

    def test_register_and_resolve_by_id(self):
        registry = DefaultToolRegistry()
        tool = self.make_tool()
        registry.register(tool)
        self.assertIs(registry.resolve(tool.tool_id), tool)

    def test_unknown_id_returns_none(self):
        registry = DefaultToolRegistry()
        self.assertIsNone(registry.resolve("tool.missing"))

    def test_contains(self):
        registry = DefaultToolRegistry()
        tool = self.make_tool()
        self.assertFalse(registry.contains(tool.tool_id))
        registry.register(tool)
        self.assertTrue(registry.contains(tool.tool_id))

    def test_duplicate_tool_id_rejected(self):
        registry = DefaultToolRegistry()
        registry.register(self.make_tool())
        with self.assertRaises(DuplicateToolError):
            registry.register(self.make_tool())

    def test_capability_lookup_returns_matching_tools(self):
        registry = DefaultToolRegistry()
        first = self.make_tool("tool.one", "email.send")
        second = self.make_tool("tool.two", "email.send")
        registry.register(first)
        registry.register(second)
        result = registry.resolve_capability("email.send")
        self.assertEqual(result, (first, second))

    def test_capability_lookup_returns_empty_tuple_when_unknown(self):
        registry = DefaultToolRegistry()
        self.assertEqual(
            registry.resolve_capability("email.send"),
            (),
        )

    def test_same_tool_is_not_registered_twice(self):
        registry = DefaultToolRegistry()
        tool = self.make_tool()
        registry.register(tool)
        with self.assertRaises(DuplicateToolError):
            registry.register(tool)

    def test_list_tools_preserves_registration_order(self):
        registry = DefaultToolRegistry()
        first = self.make_tool("tool.one", "a.action")
        second = self.make_tool("tool.two", "b.action")
        registry.register(first)
        registry.register(second)
        self.assertEqual(registry.list_tools(), (first, second))

    def test_list_tools_is_immutable_snapshot(self):
        registry = DefaultToolRegistry()
        first = self.make_tool("tool.one", "a.action")
        registry.register(first)
        snapshot = registry.list_tools()
        self.assertIsInstance(snapshot, tuple)
        with self.assertRaises(AttributeError):
            snapshot.append(first)

    def test_capability_results_are_immutable_snapshot(self):
        registry = DefaultToolRegistry()
        tool = self.make_tool()
        registry.register(tool)
        result = registry.resolve_capability("test.action")
        self.assertIsInstance(result, tuple)
        with self.assertRaises(AttributeError):
            result.append(tool)

    def test_freeze_prevents_registration(self):
        registry = DefaultToolRegistry()
        registry.freeze()
        with self.assertRaises(ToolRegistryFrozenError):
            registry.register(self.make_tool())

    def test_freeze_is_idempotent(self):
        registry = DefaultToolRegistry()
        registry.freeze()
        registry.freeze()

    def test_freeze_does_not_remove_existing_tools(self):
        registry = DefaultToolRegistry()
        tool = self.make_tool()
        registry.register(tool)
        registry.freeze()
        self.assertIs(registry.resolve(tool.tool_id), tool)
        self.assertEqual(registry.resolve_capability(tool.capability), (tool,))

    def test_empty_tool_id_rejected(self):
        registry = DefaultToolRegistry()
        with self.assertRaises(ValueError):
            registry.resolve("   ")

    def test_invalid_tool_id_type_rejected(self):
        registry = DefaultToolRegistry()
        with self.assertRaises(ValueError):
            registry.resolve(123)  # type: ignore[arg-type]

    def test_empty_capability_rejected(self):
        registry = DefaultToolRegistry()
        with self.assertRaises(ValueError):
            registry.resolve_capability("   ")

    def test_invalid_capability_type_rejected(self):
        registry = DefaultToolRegistry()
        with self.assertRaises(ValueError):
            registry.resolve_capability(123)  # type: ignore[arg-type]

    def test_registry_does_not_execute_tools(self):
        registry = DefaultToolRegistry()
        self.assertFalse(hasattr(registry, "execute"))
        self.assertFalse(hasattr(registry, "invoke"))
        self.assertFalse(hasattr(registry, "run"))

    def test_registry_does_not_select_best_tool(self):
        registry = DefaultToolRegistry()
        self.assertFalse(hasattr(registry, "select"))
        self.assertFalse(hasattr(registry, "choose"))
        self.assertFalse(hasattr(registry, "best"))

    def test_registry_does_not_build_workflows(self):
        registry = DefaultToolRegistry()
        self.assertFalse(hasattr(registry, "build_steps"))
        self.assertFalse(hasattr(registry, "workflow"))

    def test_registry_does_not_execute_runtime(self):
        registry = DefaultToolRegistry()
        self.assertFalse(hasattr(registry, "runtime_executor"))
        self.assertFalse(hasattr(registry, "task_executor"))
        self.assertFalse(hasattr(registry, "scheduler"))

    def test_registry_does_not_manage_plugin_lifecycle(self):
        registry = DefaultToolRegistry()
        self.assertFalse(hasattr(registry, "load"))
        self.assertFalse(hasattr(registry, "initialize"))
        self.assertFalse(hasattr(registry, "pause"))
        self.assertFalse(hasattr(registry, "unload"))

    def test_registry_does_not_authorize(self):
        registry = DefaultToolRegistry()
        self.assertFalse(hasattr(registry, "authorize"))
        self.assertFalse(hasattr(registry, "authenticate"))
        self.assertFalse(hasattr(registry, "check_permission"))

    def test_registry_does_not_reason_or_plan(self):
        registry = DefaultToolRegistry()
        self.assertFalse(hasattr(registry, "reason"))
        self.assertFalse(hasattr(registry, "plan"))
        self.assertFalse(hasattr(registry, "decide"))
        self.assertFalse(hasattr(registry, "replan"))

    def test_registry_does_not_expose_internal_dicts(self):
        registry = DefaultToolRegistry()
        self.assertFalse(hasattr(registry, "tools_by_id"))
        self.assertFalse(hasattr(registry, "tools_by_capability"))

    def test_multiple_versions_are_not_ranked(self):
        registry = DefaultToolRegistry()
        old = self.make_tool("tool.browser.v1", "browser.search")
        new = self.make_tool("tool.browser.v2", "browser.search")
        registry.register(old)
        registry.register(new)
        self.assertEqual(
            registry.resolve_capability("browser.search"),
            (old, new),
        )

    def test_capability_lookup_does_not_mutate_after_external_tuple_use(self):
        registry = DefaultToolRegistry()
        first = self.make_tool("tool.one", "email.send")
        second = self.make_tool("tool.two", "email.send")
        registry.register(first)
        result = registry.resolve_capability("email.send")
        registry.register(second)
        self.assertEqual(result, (first,))
        self.assertEqual(
            registry.resolve_capability("email.send"),
            (first, second),
        )

    def test_registry_is_reusable(self):
        registry = DefaultToolRegistry()
        first = self.make_tool("tool.one", "first.action")
        second = self.make_tool("tool.two", "second.action")
        registry.register(first)
        self.assertEqual(registry.resolve_capability("first.action"), (first,))
        registry.register(second)
        self.assertEqual(registry.resolve_capability("second.action"), (second,))

    def test_registered_tool_identity_is_preserved(self):
        registry = DefaultToolRegistry()
        tool = self.make_tool()
        registry.register(tool)
        self.assertIs(registry.resolve(tool.tool_id), tool)
        self.assertIs(registry.resolve_capability(tool.capability)[0], tool)

    def test_registry_has_no_task_registry_api(self):
        registry = DefaultToolRegistry()
        self.assertFalse(hasattr(registry, "resolve_task"))
        self.assertFalse(hasattr(registry, "register_task"))

    def test_registry_has_no_workflow_registry_api(self):
        registry = DefaultToolRegistry()
        self.assertFalse(hasattr(registry, "resolve_workflow"))
        self.assertFalse(hasattr(registry, "register_workflow"))

    def test_registry_does_not_depend_on_identity(self):
        registry = DefaultToolRegistry()
        self.assertFalse(hasattr(registry, "identity"))
        self.assertFalse(hasattr(registry, "principal"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
