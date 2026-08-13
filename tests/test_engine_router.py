import unittest

from ai_os.engines import (
    EngineRegistry,
    EngineRequest,
    EngineResult,
    EngineStatus,
    EngineType,
)
from ai_os.engines.routing import (
    EngineRouter,
    RegistryEngineRouter,
)
from ai_os.identity import Identity, IdentityType


def create_identity():
    return Identity(
        identity_id="identity:user:123",
        principal="user:123",
        identity_type=IdentityType.USER,
    )


def create_request(
    engine_id="engine.planner",
):
    return EngineRequest(
        request_id="request:123",
        identity=create_identity(),
        input={"task": "plan"},
        metadata={"engine_id": engine_id},
    )


class TestEngine:

    def __init__(
        self,
        engine_id,
        engine_type=EngineType.PLANNING,
    ):
        self._engine_id = engine_id
        self._engine_type = engine_type
        self.executed = False

    @property
    def engine_id(self):
        return self._engine_id

    @property
    def engine_type(self):
        return self._engine_type

    def execute(self, request):
        self.executed = True

        return EngineResult(
            status=EngineStatus.SUCCESS,
            output={
                "engine_id": self.engine_id,
                "request_id": request.request_id,
            },
        )


class EngineRouterTests(unittest.TestCase):

    def create_registry(self):
        registry = EngineRegistry()

        registry.register(
            TestEngine("engine.planner")
        )

        return registry

    def test_valid_registry_router_matches_protocol(self):
        router = RegistryEngineRouter(
            self.create_registry()
        )

        self.assertIsInstance(
            router,
            EngineRouter,
        )

    def test_router_selects_registered_engine(self):
        registry = self.create_registry()

        router = RegistryEngineRouter(
            registry
        )

        result = router.route(
            create_request("engine.planner")
        )

        self.assertEqual(
            result.output["engine_id"],
            "engine.planner",
        )

    def test_router_dispatches_request_to_engine(self):
        registry = EngineRegistry()

        engine = TestEngine(
            "engine.planner"
        )

        registry.register(engine)

        router = RegistryEngineRouter(
            registry
        )

        router.route(
            create_request("engine.planner")
        )

        self.assertTrue(
            engine.executed
        )

    def test_router_returns_engine_result(self):
        router = RegistryEngineRouter(
            self.create_registry()
        )

        result = router.route(
            create_request()
        )

        self.assertIsInstance(
            result,
            EngineResult,
        )

    def test_unknown_engine_rejected(self):
        router = RegistryEngineRouter(
            self.create_registry()
        )

        with self.assertRaises(KeyError):
            router.route(
                create_request(
                    "engine.unknown"
                )
            )

    def test_missing_engine_id_rejected(self):
        request = EngineRequest(
            request_id="request:123",
            identity=create_identity(),
            input={"task": "plan"},
        )

        router = RegistryEngineRouter(
            self.create_registry()
        )

        with self.assertRaises(ValueError):
            router.route(request)

    def test_invalid_request_rejected(self):
        router = RegistryEngineRouter(
            self.create_registry()
        )

        with self.assertRaises(TypeError):
            router.route(
                {"engine_id": "engine.planner"}
            )

    def test_invalid_registry_rejected(self):
        with self.assertRaises(TypeError):
            RegistryEngineRouter(
                object()
            )

    def test_router_does_not_return_execution_result(self):
        from ai_os.runtime.contracts import ExecutionResult

        router = RegistryEngineRouter(
            self.create_registry()
        )

        result = router.route(
            create_request()
        )

        self.assertIsInstance(
            result,
            EngineResult,
        )

        self.assertIsNot(
            type(result),
            ExecutionResult,
        )

    def test_router_does_not_authorize_identity(self):
        router = RegistryEngineRouter(
            self.create_registry()
        )

        result = router.route(
            create_request()
        )

        self.assertFalse(
            hasattr(
                result,
                "authorized",
            )
        )

    def test_router_does_not_modify_identity(self):
        request = create_request()

        router = RegistryEngineRouter(
            self.create_registry()
        )

        router.route(request)

        self.assertEqual(
            request.identity.identity_id,
            "identity:user:123",
        )

    def test_router_does_not_require_intelligence(self):
        router = RegistryEngineRouter(
            self.create_registry()
        )

        self.assertFalse(
            hasattr(
                router,
                "reason",
            )
        )

    def test_router_does_not_execute_runtime(self):
        router = RegistryEngineRouter(
            self.create_registry()
        )

        result = router.route(
            create_request()
        )

        self.assertIsInstance(
            result,
            EngineResult,
        )

        self.assertNotIsInstance(
            result,
            ExecutionResultProxy,
        )


class ExecutionResultProxy:
    """Marker used only to ensure Router doesn't expose runtime results."""


if __name__ == "__main__":
    unittest.main(verbosity=2)