import unittest

from ai_os.runtime.tasks import (
    DefaultTaskRegistry,
    DuplicateCapabilityError,
    RegistryFrozenError,
    Task,
    TaskRegistry,
)


class ValidTask:

    @property
    def capability(self):
        return "test.capability"

    def execute(self, step):
        return {"ok": True}


class AnotherValidTask:

    @property
    def capability(self):
        return "another.capability"

    def execute(self, step):
        return {"ok": True}


class MissingExecuteTask:

    @property
    def capability(self):
        return "test.capability"


class MissingCapabilityTask:

    def execute(self, step):
        return {"ok": True}


class ValidRegistry:

    def __init__(self):
        self._tasks = {}
        self._frozen = False

    def register(self, task):
        self._tasks[task.capability] = task

    def resolve(self, capability):
        return self._tasks.get(capability)

    def freeze(self):
        self._frozen = True


class MissingRegisterRegistry:

    def resolve(self, capability):
        return None


class MissingResolveRegistry:

    def register(self, task):
        pass


class MissingFreezeRegistry:

    def register(self, task):
        pass

    def resolve(self, capability):
        return None

class TaskRegistryTests(unittest.TestCase):

    def test_valid_implementation_matches_protocol(self):
        registry = ValidRegistry()

        self.assertIsInstance(
            registry,
            TaskRegistry,
        )

    def test_invalid_registry_without_register_rejected(self):
        registry = MissingRegisterRegistry()

        self.assertFalse(
            isinstance(
                registry,
                TaskRegistry,
            )
        )

    def test_invalid_registry_without_resolve_rejected(self):
        registry = MissingResolveRegistry()

        self.assertFalse(
            isinstance(
                registry,
                TaskRegistry,
            )
        )

    def test_register_accepts_task(self):
        registry = ValidRegistry()
        task = ValidTask()

        registry.register(task)

        self.assertIs(
            registry.resolve("test.capability"),
            task,
        )

    def test_resolve_returns_none_for_unknown_capability(self):
        registry = ValidRegistry()

        self.assertIsNone(
            registry.resolve("unknown.capability")
        )

    def test_multiple_capabilities_resolve_independently(self):
        registry = ValidRegistry()

        first = ValidTask()
        second = AnotherValidTask()

        registry.register(first)
        registry.register(second)

        self.assertIs(
            registry.resolve("test.capability"),
            first,
        )

        self.assertIs(
            registry.resolve("another.capability"),
            second,
        )

    def test_registry_is_structural_contract(self):
        registry = ValidRegistry()

        self.assertIsInstance(
            registry,
            TaskRegistry,
        )

        self.assertNotIn(
            TaskRegistry,
            ValidRegistry.__bases__,
        )

    def test_registry_does_not_require_engine(self):
        registry = ValidRegistry()

        self.assertFalse(
            hasattr(registry, "engine")
        )

        self.assertFalse(
            hasattr(registry, "route")
        )

    def test_registry_does_not_require_intelligence(self):
        registry = ValidRegistry()

        self.assertFalse(
            hasattr(registry, "reason")
        )

        self.assertFalse(
            hasattr(registry, "think")
        )

        self.assertFalse(
            hasattr(registry, "plan")
        )

    def test_invalid_registry_without_freeze_rejected(self):
        registry = MissingFreezeRegistry()

        self.assertFalse(
            isinstance(
                registry,
                TaskRegistry,
            )
        )

    def test_freeze_prevents_registration(self):
        registry = DefaultTaskRegistry()

        registry.register(ValidTask())
        registry.freeze()

        with self.assertRaises(RegistryFrozenError):
            registry.register(AnotherValidTask())


    def test_resolve_still_works_after_freeze(self):
        registry = DefaultTaskRegistry()

        task = ValidTask()
        registry.register(task)
        registry.freeze()

        self.assertIs(
            registry.resolve("test.capability"),
            task,
        )


    def test_unknown_capability_still_returns_none_after_freeze(self):
        registry = DefaultTaskRegistry()

        registry.freeze()

        self.assertIsNone(
            registry.resolve("unknown.capability")
        )


    def test_freeze_is_idempotent(self):
        registry = DefaultTaskRegistry()

        registry.freeze()
        registry.freeze()
        registry.freeze()

        self.assertIsNone(
            registry.resolve("unknown.capability")
        )


    def test_frozen_registry_rejects_registration_before_validation(self):
        registry = DefaultTaskRegistry()

        registry.freeze()

        with self.assertRaises(RegistryFrozenError):
            registry.register(MissingExecuteTask())


    def test_frozen_registry_preserves_existing_task(self):
        registry = DefaultTaskRegistry()

        task = ValidTask()

        registry.register(task)
        registry.freeze()

        self.assertIs(
            registry.resolve("test.capability"),
            task,
        )

    def test_resolve_does_not_execute_task(self):
        executed = []

        class NonExecutingTask:

            @property
            def capability(self):
                return "test.capability"

            def execute(self, step):
                executed.append(True)
                return {}

        registry = ValidRegistry()
        task = NonExecutingTask()

        registry.register(task)

        resolved = registry.resolve("test.capability")

        self.assertIs(
            resolved,
            task,
        )

        self.assertEqual(
            executed,
            [],
        )

    def test_freeze_does_not_execute_tasks(self):
        executed = []

        class NonExecutingTask:

            @property
            def capability(self):
                return "test.capability"

            def execute(self, step):
                executed.append(True)
                return {}

        registry = DefaultTaskRegistry()
        registry.register(NonExecutingTask())

        registry.freeze()

        self.assertEqual(
            executed,
            [],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)