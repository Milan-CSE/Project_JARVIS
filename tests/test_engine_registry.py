import unittest

from ai_os.engines import (
    Engine,
    EngineRegistry,
    EngineResult,
    EngineStatus,
    EngineType,
)


class TestEngine:
    def __init__(self, engine_id, engine_type=EngineType.PLANNING):
        self._engine_id = engine_id
        self._engine_type = engine_type

    @property
    def engine_id(self):
        return self._engine_id

    @property
    def engine_type(self):
        return self._engine_type

    def execute(self, request):
        return EngineResult(
            status=EngineStatus.SUCCESS,
            output={"engine": self.engine_id},
        )


class InvalidEngine:
    @property
    def engine_id(self):
        return "invalid"

    @property
    def engine_type(self):
        return EngineType.PLANNING


class EngineRegistryTests(unittest.TestCase):

    def test_registry_starts_empty(self):
        registry = EngineRegistry()

        self.assertEqual(
            len(registry),
            0,
        )

    def test_register_valid_engine(self):
        registry = EngineRegistry()
        engine = TestEngine("engine.planner")

        registry.register(engine)

        self.assertEqual(
            len(registry),
            1,
        )

    def test_registered_engine_can_be_retrieved(self):
        registry = EngineRegistry()
        engine = TestEngine("engine.planner")

        registry.register(engine)

        retrieved = registry.get(
            "engine.planner"
        )

        self.assertIs(
            retrieved,
            engine,
        )

    def test_registered_engine_satisfies_protocol(self):
        registry = EngineRegistry()
        engine = TestEngine("engine.planner")

        registry.register(engine)

        retrieved = registry.get(
            "engine.planner"
        )

        self.assertIsInstance(
            retrieved,
            Engine,
        )

    def test_duplicate_engine_id_rejected(self):
        registry = EngineRegistry()

        registry.register(
            TestEngine("engine.planner")
        )

        with self.assertRaises(ValueError):
            registry.register(
                TestEngine("engine.planner")
            )

    def test_unknown_engine_rejected(self):
        registry = EngineRegistry()

        with self.assertRaises(KeyError):
            registry.get("engine.unknown")

    def test_remove_engine(self):
        registry = EngineRegistry()
        engine = TestEngine("engine.planner")

        registry.register(engine)
        registry.remove("engine.planner")

        self.assertEqual(
            len(registry),
            0,
        )

    def test_removed_engine_is_unavailable(self):
        registry = EngineRegistry()

        registry.register(
            TestEngine("engine.planner")
        )

        registry.remove("engine.planner")

        with self.assertRaises(KeyError):
            registry.get("engine.planner")

    def test_contains_registered_engine(self):
        registry = EngineRegistry()

        registry.register(
            TestEngine("engine.planner")
        )

        self.assertTrue(
            registry.contains("engine.planner")
        )

    def test_contains_unknown_engine(self):
        registry = EngineRegistry()

        self.assertFalse(
            registry.contains("engine.unknown")
        )

    def test_invalid_engine_rejected(self):
        registry = EngineRegistry()

        with self.assertRaises(TypeError):
            registry.register(
                InvalidEngine()
            )

    def test_empty_engine_id_rejected(self):
        registry = EngineRegistry()

        with self.assertRaises(ValueError):
            registry.register(
                TestEngine("")
            )

    def test_non_string_engine_id_rejected(self):
        registry = EngineRegistry()

        with self.assertRaises(TypeError):
            registry.get(123)

    def test_registry_does_not_execute_engine(self):
        registry = EngineRegistry()
        engine = TestEngine("engine.planner")

        registry.register(engine)

        retrieved = registry.get(
            "engine.planner"
        )

        self.assertIs(
            retrieved,
            engine,
        )

        # Registry only returns the engine.
        # It does not call execute().
        self.assertEqual(
            len(registry),
            1,
        )

    def test_remove_unknown_engine_rejected(self):
        registry = EngineRegistry()

        with self.assertRaises(KeyError):
            registry.remove("engine.unknown")


if __name__ == "__main__":
    unittest.main(verbosity=2)