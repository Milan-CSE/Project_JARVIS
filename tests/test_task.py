import unittest

from ai_os.runtime.contracts import ExecutionStep
from ai_os.runtime.tasks import Task


class ValidTask:

    @property
    def capability(self):
        return "test.capability"

    def execute(self, step):
        return {
            "processed": True,
            "step_id": step.step_id,
        }


class MissingExecuteTask:

    @property
    def capability(self):
        return "test.capability"


class MissingCapabilityTask:

    def execute(self, step):
        return {
            "processed": True,
        }


def create_step():
    return ExecutionStep(
        step_id="step:test",
        capability="test.capability",
    )


class TaskTests(unittest.TestCase):

    def test_valid_implementation_matches_protocol(self):
        task = ValidTask()

        self.assertIsInstance(
            task,
            Task,
        )

    def test_invalid_task_without_execute_rejected(self):
        task = MissingExecuteTask()

        self.assertFalse(
            isinstance(
                task,
                Task,
            )
        )

    def test_invalid_task_without_capability_rejected(self):
        task = MissingCapabilityTask()

        self.assertFalse(
            isinstance(
                task,
                Task,
            )
        )

    def test_capability_is_available(self):
        task = ValidTask()

        self.assertEqual(
            task.capability,
            "test.capability",
        )

    def test_execute_receives_execution_step(self):
        task = ValidTask()
        step = create_step()

        result = task.execute(step)

        self.assertEqual(
            result["step_id"],
            "step:test",
        )

    def test_execute_returns_operation_output(self):
        task = ValidTask()
        step = create_step()

        result = task.execute(step)

        self.assertEqual(
            result["processed"],
            True,
        )

    def test_task_does_not_require_executor(self):
        task = ValidTask()

        self.assertFalse(
            hasattr(task, "executor")
        )

        self.assertFalse(
            hasattr(task, "runtime_executor")
        )

    def test_task_does_not_require_engine_or_intelligence(self):
        task = ValidTask()

        self.assertFalse(
            hasattr(task, "engine")
        )

        self.assertFalse(
            hasattr(task, "reason")
        )

        self.assertFalse(
            hasattr(task, "think")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)