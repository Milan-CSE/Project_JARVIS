from __future__ import annotations

import json
import unittest
from collections.abc import Mapping

from ai_os.tools import DefaultTool, Tool


class ValidStructuralTool:
    @property
    def tool_id(self):
        return "tool.test"

    @property
    def name(self):
        return "Test Tool"

    @property
    def version(self):
        return "1.0"

    @property
    def description(self):
        return "A test tool."

    @property
    def capability(self):
        return "test.capability"

    @property
    def input_schema(self):
        return {"type": "object"}

    @property
    def required_permissions(self):
        return ("test.read",)

    @property
    def metadata(self):
        return {}


class ExecutingTool:
    tool_id = "tool.bad"
    name = "Bad"
    version = "1.0"
    description = "Bad"
    capability = "bad"

    @property
    def input_schema(self):
        return {}

    @property
    def required_permissions(self):
        return ()

    @property
    def metadata(self):
        return {}

    def execute(self, *args, **kwargs):
        return None


class WorkflowLikeTool:
    tool_id = "tool.workflow"
    name = "Workflow"
    version = "1.0"
    description = "Workflow-like"
    capability = "workflow"

    input_schema = {}
    required_permissions = ()
    metadata = {}

    def build_steps(self, parameters):
        return ()


class PluginLikeTool:
    tool_id = "tool.plugin"
    name = "Plugin"
    version = "1.0"
    description = "Plugin-like"
    capability = "plugin"

    input_schema = {}
    required_permissions = ()
    metadata = {}

    def load(self):
        pass

    def initialize(self):
        pass

    def pause(self):
        pass

    def unload(self):
        pass


class ToolContractTests(unittest.TestCase):
    def test_valid_implementation_matches_protocol(self):
        self.assertIsInstance(
            ValidStructuralTool(),
            Tool,
        )

    def test_default_tool_matches_protocol(self):
        tool = self.make_tool()
        self.assertIsInstance(tool, Tool)

    def make_tool(self, **overrides):
        values = {
            "tool_id": "tool.test",
            "name": "Test Tool",
            "version": "1.0",
            "description": "Test external capability.",
            "capability": "test.capability",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
            },
            "required_permissions": (
                "test.read",
                "test.network",
            ),
            "metadata": {
                "provider": "test",
                "nested": {"enabled": True},
            },
        }
        values.update(overrides)
        return DefaultTool(**values)

    def test_tool_is_immutable(self):
        tool = self.make_tool()

        with self.assertRaises(AttributeError):
            tool.name = "Changed"

    def test_input_schema_is_immutable(self):
        tool = self.make_tool()

        with self.assertRaises(TypeError):
            tool.input_schema["x"] = 1

    def test_nested_input_schema_is_immutable(self):
        tool = self.make_tool()

        with self.assertRaises(TypeError):
            tool.input_schema["properties"]["query"]["type"] = "integer"

    def test_metadata_is_immutable(self):
        tool = self.make_tool()

        with self.assertRaises(TypeError):
            tool.metadata["x"] = 1

    def test_nested_metadata_is_immutable(self):
        tool = self.make_tool()

        with self.assertRaises(TypeError):
            tool.metadata["nested"]["enabled"] = False

    def test_permissions_are_immutable(self):
        tool = self.make_tool()

        self.assertIsInstance(
            tool.required_permissions,
            tuple,
        )

    def test_empty_tool_id_rejected(self):
        with self.assertRaises(ValueError):
            self.make_tool(tool_id=" ")

    def test_empty_name_rejected(self):
        with self.assertRaises(ValueError):
            self.make_tool(name=" ")

    def test_empty_version_rejected(self):
        with self.assertRaises(ValueError):
            self.make_tool(version=" ")

    def test_empty_description_rejected(self):
        with self.assertRaises(ValueError):
            self.make_tool(description=" ")

    def test_empty_capability_rejected(self):
        with self.assertRaises(ValueError):
            self.make_tool(capability=" ")

    def test_non_string_identity_fields_rejected(self):
        for field_name in (
            "tool_id",
            "name",
            "version",
            "description",
            "capability",
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(TypeError):
                    self.make_tool(
                        **{field_name: 123}
                    )

    def test_input_schema_must_be_mapping(self):
        with self.assertRaises(TypeError):
            self.make_tool(
                input_schema=("invalid",)
            )

    def test_permissions_must_be_sequence(self):
        with self.assertRaises(TypeError):
            self.make_tool(
                required_permissions="test.read"
            )

    def test_permissions_must_contain_strings(self):
        with self.assertRaises(TypeError):
            self.make_tool(
                required_permissions=("test.read", 1)
            )

    def test_empty_permission_rejected(self):
        with self.assertRaises(ValueError):
            self.make_tool(
                required_permissions=("test.read", " ")
            )

    def test_duplicate_permissions_rejected(self):
        with self.assertRaises(ValueError):
            self.make_tool(
                required_permissions=(
                    "test.read",
                    "test.read",
                )
            )

    def test_metadata_must_be_mapping(self):
        with self.assertRaises(TypeError):
            self.make_tool(
                metadata=("invalid",)
            )

    def test_non_json_input_schema_rejected(self):
        with self.assertRaises(TypeError):
            self.make_tool(
                input_schema={
                    "bad": object(),
                }
            )

    def test_non_json_metadata_rejected(self):
        with self.assertRaises(TypeError):
            self.make_tool(
                metadata={
                    "bad": object(),
                }
            )

    def test_non_finite_input_schema_rejected(self):
        with self.assertRaises(ValueError):
            self.make_tool(
                input_schema={
                    "value": float("nan"),
                }
            )

    def test_non_finite_metadata_rejected(self):
        with self.assertRaises(ValueError):
            self.make_tool(
                metadata={
                    "value": float("inf"),
                }
            )

    def test_to_dict_contains_contract_fields(self):
        tool = self.make_tool()

        data = tool.to_dict()

        self.assertEqual(
            data["tool_id"],
            "tool.test",
        )
        self.assertEqual(
            data["capability"],
            "test.capability",
        )
        self.assertEqual(
            data["required_permissions"],
            ["test.read", "test.network"],
        )

    def test_to_json_is_valid_json(self):
        tool = self.make_tool()

        payload = json.loads(tool.to_json())

        self.assertEqual(
            payload["tool_id"],
            tool.tool_id,
        )

    def test_tool_has_no_execute_api(self):
        tool = self.make_tool()

        self.assertFalse(hasattr(tool, "execute"))
        self.assertFalse(hasattr(tool, "run"))
        self.assertFalse(hasattr(tool, "invoke"))

    def test_tool_has_no_workflow_api(self):
        tool = self.make_tool()

        self.assertFalse(hasattr(tool, "build_steps"))

    def test_tool_has_no_reasoning_api(self):
        tool = self.make_tool()

        self.assertFalse(hasattr(tool, "reason"))
        self.assertFalse(hasattr(tool, "plan"))
        self.assertFalse(hasattr(tool, "decide"))
        self.assertFalse(hasattr(tool, "replan"))

    def test_tool_has_no_lifecycle_api(self):
        tool = self.make_tool()

        self.assertFalse(hasattr(tool, "load"))
        self.assertFalse(hasattr(tool, "initialize"))
        self.assertFalse(hasattr(tool, "pause"))
        self.assertFalse(hasattr(tool, "unload"))

    def test_tool_has_no_security_authorization_api(self):
        tool = self.make_tool()

        self.assertFalse(hasattr(tool, "authorize"))
        self.assertFalse(hasattr(tool, "authenticate"))
        self.assertFalse(hasattr(tool, "elevate"))

    def test_tool_has_no_runtime_api(self):
        tool = self.make_tool()

        self.assertFalse(hasattr(tool, "execute_plan"))
        self.assertFalse(hasattr(tool, "schedule"))
        self.assertFalse(hasattr(tool, "task_registry"))
        self.assertFalse(hasattr(tool, "runtime_executor"))

    def test_tool_has_no_identity_ownership_api(self):
        tool = self.make_tool()

        self.assertFalse(hasattr(tool, "principal"))
        self.assertFalse(hasattr(tool, "identity"))

    def test_tool_has_no_intelligence_dependency(self):
        tool = self.make_tool()

        self.assertFalse(hasattr(tool, "intelligence"))

    def test_tool_does_not_contain_plugin_lifecycle(self):
        tool = self.make_tool()

        for name in (
            "load",
            "initialize",
            "pause",
            "unload",
        ):
            self.assertFalse(hasattr(tool, name))

    def test_reusable(self):
        first = self.make_tool(
            tool_id="tool.first",
            capability="first.capability",
        )
        second = self.make_tool(
            tool_id="tool.second",
            capability="second.capability",
        )

        self.assertEqual(
            first.tool_id,
            "tool.first",
        )
        self.assertEqual(
            second.tool_id,
            "tool.second",
        )

    def test_same_capability_is_allowed_for_different_tools(self):
        first = self.make_tool(
            tool_id="tool.first",
        )
        second = self.make_tool(
            tool_id="tool.second",
        )

        self.assertEqual(
            first.capability,
            second.capability,
        )

    def test_tool_protocol_is_not_execution_protocol(self):
        self.assertFalse(
            hasattr(Tool, "execute")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
