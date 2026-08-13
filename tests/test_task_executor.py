import unittest

from ai_os.runtime.contracts import (
    ExecutionStep,
)
from ai_os.runtime.tasks import (
    DefaultTaskExecutor,
    DefaultTaskRegistry,
    Task,
    TaskExecutor,
    UnknownCapabilityError,
)


class ValidTask:

    @property
    def capability(self):
        return "test.capability"

    def execute(self, step):
        return {
            "step_id": step.step_id,
            "value": "executed",
        }


class FailingTask:

    @property
    def capability(self):
        return "failing.capability"

    def execute(self, step):
        raise RuntimeError("task failed")


class InvalidTask:
    pass


class InvalidRegistry:

    def register(self, task):
        pass

    def resolve(self, capability):
        return InvalidTask()

    def freeze(self):
        pass


class TaskExecutorTests(unittest.TestCase):

    def create_registry(self):
        registry = DefaultTaskRegistry()
        registry.register(ValidTask())
        registry.freeze()
        return registry

    def create_step(
        self,
        capability="test.capability",
    ):
        return ExecutionStep(
            step_id="step:test",
            capability=capability,
        )

    # ---------------------------------------------
    # Protocol
    # ---------------------------------------------

    def test_valid_implementation_matches_protocol(self):
        executor = DefaultTaskExecutor(
            self.create_registry()
        )

        self.assertIsInstance(
            executor,
            TaskExecutor,
        )

    # ---------------------------------------------
    # Construction
    # ---------------------------------------------

    def test_invalid_registry_rejected(self):
        with self.assertRaises(TypeError):
            DefaultTaskExecutor(object())

    # ---------------------------------------------
    # Normal execution
    # ---------------------------------------------

    def test_registered_task_is_executed(self):
        registry = DefaultTaskRegistry()
        task = ValidTask()
        registry.register(task)
        registry.freeze()

        executor = DefaultTaskExecutor(
            registry
        )

        step = self.create_step()

        result = executor.execute_step(step)

        self.assertEqual(
            result["step_id"],
            "step:test",
        )

        self.assertEqual(
            result["value"],
            "executed",
        )

    def test_exact_execution_step_is_passed_to_task(self):
        received = []

        class CapturingTask:

            @property
            def capability(self):
                return "capture.capability"

            def execute(self, step):
                received.append(step)
                return "ok"

        registry = DefaultTaskRegistry()
        registry.register(CapturingTask())
        registry.freeze()

        executor = DefaultTaskExecutor(
            registry
        )

        step = self.create_step(
            "capture.capability"
        )

        result = executor.execute_step(step)

        self.assertEqual(
            result,
            "ok",
        )

        self.assertIs(
            received[0],
            step,
        )

    def test_task_output_is_returned_unchanged(self):
        output = {
            "result": 123,
            "nested": {
                "value": True,
            },
        }

        class OutputTask:

            @property
            def capability(self):
                return "output.capability"

            def execute(self, step):
                return output

        registry = DefaultTaskRegistry()
        registry.register(OutputTask())
        registry.freeze()

        executor = DefaultTaskExecutor(
            registry
        )

        result = executor.execute_step(
            self.create_step(
                "output.capability"
            )
        )

        self.assertIs(
            result,
            output,
        )

    # ---------------------------------------------
    # Errors
    # ---------------------------------------------

    def test_unknown_capability_rejected(self):
        executor = DefaultTaskExecutor(
            self.create_registry()
        )

        with self.assertRaises(
            UnknownCapabilityError
        ):
            executor.execute_step(
                self.create_step(
                    "unknown.capability"
                )
            )

    def test_invalid_step_rejected(self):
        executor = DefaultTaskExecutor(
            self.create_registry()
        )

        with self.assertRaises(TypeError):
            executor.execute_step(
                object()
            )

    def test_invalid_task_returned_by_registry_rejected(self):
        executor = DefaultTaskExecutor(
            InvalidRegistry()
        )

        with self.assertRaises(TypeError):
            executor.execute_step(
                self.create_step()
            )

    def test_task_exception_propagates(self):
        registry = DefaultTaskRegistry()
        registry.register(FailingTask())
        registry.freeze()

        executor = DefaultTaskExecutor(
            registry
        )

        with self.assertRaises(RuntimeError):
            executor.execute_step(
                self.create_step(
                    "failing.capability"
                )
            )

    # ---------------------------------------------
    # Registry boundary
    # ---------------------------------------------

    def test_executor_does_not_register_tasks(self):
        executor = DefaultTaskExecutor(
            self.create_registry()
        )

        self.assertFalse(
            hasattr(
                executor,
                "register",
            )
        )

        self.assertFalse(
            hasattr(
                executor,
                "freeze",
            )
        )

    # ---------------------------------------------
    # Architecture boundaries
    # ---------------------------------------------

    def test_executor_does_not_require_scheduler(self):
        executor = DefaultTaskExecutor(
            self.create_registry()
        )

        self.assertFalse(
            hasattr(
                executor,
                "scheduler",
            )
        )

        self.assertFalse(
            hasattr(
                executor,
                "get_ready_steps",
            )
        )

    def test_executor_does_not_require_engine(self):
        executor = DefaultTaskExecutor(
            self.create_registry()
        )

        self.assertFalse(
            hasattr(
                executor,
                "engine",
            )
        )

    def test_executor_does_not_require_intelligence(self):
        executor = DefaultTaskExecutor(
            self.create_registry()
        )

        self.assertFalse(
            hasattr(
                executor,
                "reason",
            )
        )

        self.assertFalse(
            hasattr(
                executor,
                "think",
            )
        )

    def test_executor_does_not_return_execution_result(self):
        from ai_os.runtime.contracts import ExecutionResult

        executor = DefaultTaskExecutor(
            self.create_registry()
        )

        result = executor.execute_step(
            self.create_step()
        )

        self.assertNotIsInstance(
            result,
            ExecutionResult,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)