from __future__ import annotations

import unittest

from ai_os.tools import DefaultTool, DefaultToolAdapter, Tool, ToolAdapter
from ai_os.runtime.tasks.task import Task


class ValidTask:
    def __init__(self, capability):
        self._capability = capability
        self.executed = False

    @property
    def capability(self):
        return self._capability

    def execute(self, step):
        self.executed = True
        return {"ok": True}


class ConcreteAdapter(DefaultToolAdapter):
    def __init__(self, tool, task):
        super().__init__(tool)
        self._task = task
        self.build_calls = 0

    def _build_task(self):
        self.build_calls += 1
        return self._task


class WrongTask:
    @property
    def capability(self):
        return "wrong.capability"

    def execute(self, step):
        return None


class NotATask:
    pass


class MalformedTool:
    tool_id = "tool.test"
    name = "Test"
    version = "1.0"
    description = "Test"
    capability = "test.action"
    input_schema = {}
    required_permissions = ()
    metadata = {}


class ToolAdapterTests(unittest.TestCase):
    def create_tool(self, capability="test.action"):
        return DefaultTool(
            tool_id="tool.test",
            name="Test Tool",
            version="1.0",
            description="Test tool",
            capability=capability,
        )

    def test_valid_adapter_matches_protocol(self):
        tool = self.create_tool()
        task = ValidTask(tool.capability)
        adapter = ConcreteAdapter(tool, task)
        self.assertIsInstance(adapter, ToolAdapter)

    def test_valid_task_matches_runtime_contract(self):
        task = ValidTask("test.action")
        self.assertIsInstance(task, Task)

    def test_invalid_adapter_object_does_not_match_protocol(self):
        class MissingAdapter:
            pass
        self.assertFalse(isinstance(MissingAdapter(), ToolAdapter))

    def test_invalid_tool_rejected(self):
        with self.assertRaises(TypeError):
            DefaultToolAdapter(object())

    def test_tool_id_is_preserved(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertEqual(adapter.tool_id, tool.tool_id)

    def test_capability_is_preserved(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertEqual(adapter.capability, tool.capability)

    def test_exact_tool_is_preserved(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertIs(adapter.tool, tool)

    def test_adapt_returns_task(self):
        tool = self.create_tool()
        task = ValidTask(tool.capability)
        adapter = ConcreteAdapter(tool, task)
        result = adapter.adapt()
        self.assertIs(result, task)
        self.assertIsInstance(result, Task)

    def test_adapt_calls_builder_once_per_call(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        adapter.adapt()
        self.assertEqual(adapter.build_calls, 1)

    def test_adapt_is_reusable(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        first = adapter.adapt()
        second = adapter.adapt()
        self.assertIs(first, second)
        self.assertEqual(adapter.build_calls, 2)

    def test_non_task_result_rejected(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, NotATask())
        with self.assertRaises(TypeError):
            adapter.adapt()

    def test_wrong_capability_rejected(self):
        tool = self.create_tool("test.action")
        adapter = ConcreteAdapter(tool, ValidTask("wrong.action"))
        with self.assertRaises(ValueError):
            adapter.adapt()

    def test_adapter_does_not_execute_task(self):
        tool = self.create_tool()
        task = ValidTask(tool.capability)
        adapter = ConcreteAdapter(tool, task)
        adapter.adapt()
        self.assertFalse(task.executed)

    def test_adapter_does_not_have_execute_api(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertFalse(hasattr(adapter, "execute"))

    def test_adapter_does_not_have_runtime_executor(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertFalse(hasattr(adapter, "runtime_executor"))
        self.assertFalse(hasattr(adapter, "executor"))

    def test_adapter_does_not_have_scheduler(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertFalse(hasattr(adapter, "scheduler"))

    def test_adapter_does_not_have_workflow_runner(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertFalse(hasattr(adapter, "workflow_runner"))
        self.assertFalse(hasattr(adapter, "run_workflow"))

    def test_adapter_does_not_reason(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertFalse(hasattr(adapter, "reason"))
        self.assertFalse(hasattr(adapter, "plan"))
        self.assertFalse(hasattr(adapter, "decide"))
        self.assertFalse(hasattr(adapter, "replan"))

    def test_adapter_does_not_authorize(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertFalse(hasattr(adapter, "authorize"))
        self.assertFalse(hasattr(adapter, "authenticate"))

    def test_adapter_does_not_manage_plugin_lifecycle(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertFalse(hasattr(adapter, "load"))
        self.assertFalse(hasattr(adapter, "initialize"))
        self.assertFalse(hasattr(adapter, "pause"))
        self.assertFalse(hasattr(adapter, "unload"))

    def test_adapter_does_not_register_task(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertFalse(hasattr(adapter, "register"))
        self.assertFalse(hasattr(adapter, "task_registry"))

    def test_adapter_does_not_mutate_tool(self):
        tool = self.create_tool()
        original = (tool.tool_id, tool.capability, tool.version)
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        adapter.adapt()
        self.assertEqual((tool.tool_id, tool.capability, tool.version), original)

    def test_adapter_does_not_mutate_task_during_adaptation(self):
        tool = self.create_tool()
        task = ValidTask(tool.capability)
        adapter = ConcreteAdapter(tool, task)
        self.assertFalse(task.executed)
        adapter.adapt()
        self.assertFalse(task.executed)

    def test_base_adapter_is_contract_but_not_generic_execution(self):
        tool = self.create_tool()
        adapter = DefaultToolAdapter(tool)
        self.assertIsInstance(adapter, ToolAdapter)
        with self.assertRaises(NotImplementedError):
            adapter.adapt()

    def test_empty_tool_id_rejected(self):
        class BadTool:
            tool_id = ""
            name = "Bad"
            version = "1.0"
            description = "Bad"
            capability = "test.action"
            input_schema = {}
            required_permissions = ()
            metadata = {}
        with self.assertRaises(ValueError):
            DefaultToolAdapter(BadTool())

    def test_empty_capability_rejected(self):
        class BadTool:
            tool_id = "tool.bad"
            name = "Bad"
            version = "1.0"
            description = "Bad"
            capability = ""
            input_schema = {}
            required_permissions = ()
            metadata = {}
        with self.assertRaises(ValueError):
            DefaultToolAdapter(BadTool())

    def test_adapter_state_does_not_change_after_adapt(self):
        tool = self.create_tool()
        task = ValidTask(tool.capability)
        adapter = ConcreteAdapter(tool, task)
        before = (adapter.tool_id, adapter.capability, adapter.tool)
        adapter.adapt()
        after = (adapter.tool_id, adapter.capability, adapter.tool)
        self.assertEqual(before, after)

    def test_task_capability_must_match_tool_capability(self):
        tool = self.create_tool("email.send")
        task = ValidTask("email.read")
        adapter = ConcreteAdapter(tool, task)
        with self.assertRaises(ValueError):
            adapter.adapt()

    def test_adapter_can_wrap_same_capability_from_different_tool(self):
        first = self.create_tool()
        second = DefaultTool(
            tool_id="tool.second",
            name="Second",
            version="1.0",
            description="Second",
            capability=first.capability,
        )
        first_adapter = ConcreteAdapter(first, ValidTask(first.capability))
        second_adapter = ConcreteAdapter(second, ValidTask(second.capability))
        self.assertNotEqual(first_adapter.tool_id, second_adapter.tool_id)
        self.assertEqual(first_adapter.capability, second_adapter.capability)

    def test_adapter_does_not_select_between_tools(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertFalse(hasattr(adapter, "select"))
        self.assertFalse(hasattr(adapter, "resolve"))

    def test_adapter_does_not_access_identity(self):
        tool = self.create_tool()
        adapter = ConcreteAdapter(tool, ValidTask(tool.capability))
        self.assertFalse(hasattr(adapter, "identity"))
        self.assertFalse(hasattr(adapter, "principal"))
        self.assertFalse(hasattr(adapter, "current_user"))

    def test_adapter_does_not_persist_state_between_tool_calls(self):
        tool = self.create_tool()
        task = ValidTask(tool.capability)
        adapter = ConcreteAdapter(tool, task)
        first = adapter.adapt()
        second = adapter.adapt()
        self.assertIs(first, second)
        self.assertEqual(adapter.tool_id, tool.tool_id)
        self.assertEqual(adapter.capability, tool.capability)


if __name__ == "__main__":
    unittest.main(verbosity=2)
