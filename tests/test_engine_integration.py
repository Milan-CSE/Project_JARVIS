import unittest

from ai_os.engines import (
    Engine,
    EngineRegistry,
    EngineRequest,
    EngineResult,
    EngineStatus,
    EngineType,
)
from ai_os.engines.adapters import EngineAdapter
from ai_os.engines.routing import (
    EngineRouter,
    RegistryEngineRouter,
)
from ai_os.identity import Identity, IdentityType
from ai_os.runtime.contracts import ExecutionResult


class TestAdapter:
    """Fake external adapter used only for integration testing."""

    def adapt_request(self, request):
        return {
            "external_task": request.input["task"],
            "request_id": request.request_id,
        }

    def adapt_result(self, result):
        return EngineResult(
            status=EngineStatus.SUCCESS,
            output=result,
        )


class IntegratedTestEngine:
    """Fake Engine proving Engine + Adapter integration."""

    def __init__(self):
        self.adapter = TestAdapter()
        self.executed_request = None

    @property
    def engine_id(self):
        return "engine.integrated"

    @property
    def engine_type(self):
        return EngineType.PLANNING

    def execute(self, request):
        self.executed_request = request

        external_request = self.adapter.adapt_request(
            request
        )

        external_result = {
            "processed_task":
                external_request["external_task"],
            "request_id":
                external_request["request_id"],
        }

        return self.adapter.adapt_result(
            external_result
        )


def create_identity():
    return Identity(
        identity_id="identity:user:123",
        principal="user:123",
        identity_type=IdentityType.USER,
    )


def create_request():
    return EngineRequest(
        request_id="request:integration:001",
        identity=create_identity(),
        input={
            "task": "create a plan",
        },
        metadata={
            "engine_id": "engine.integrated",
        },
    )


class EngineIntegrationTests(unittest.TestCase):

    def create_system(self):
        engine = IntegratedTestEngine()

        registry = EngineRegistry()
        registry.register(engine)

        router = RegistryEngineRouter(
            registry
        )

        return engine, registry, router

    # --------------------------------------------------
    # Structural integration
    # --------------------------------------------------

    def test_engine_satisfies_engine_protocol(self):
        engine, _, _ = self.create_system()

        self.assertIsInstance(
            engine,
            Engine,
        )

    def test_adapter_satisfies_adapter_protocol(self):
        engine, _, _ = self.create_system()

        self.assertIsInstance(
            engine.adapter,
            EngineAdapter,
        )

    def test_router_satisfies_router_protocol(self):
        _, _, router = self.create_system()

        self.assertIsInstance(
            router,
            EngineRouter,
        )

    # --------------------------------------------------
    # Complete flow
    # --------------------------------------------------

    def test_request_flows_router_registry_engine_adapter_result(self):
        engine, _, router = self.create_system()

        request = create_request()

        result = router.route(request)

        self.assertIsInstance(
            result,
            EngineResult,
        )

        self.assertEqual(
            result.status,
            EngineStatus.SUCCESS,
        )

        self.assertEqual(
            result.output["processed_task"],
            "create a plan",
        )

        self.assertIs(
            engine.executed_request,
            request,
        )

    # --------------------------------------------------
    # Identity boundary
    # --------------------------------------------------

    def test_identity_survives_engine_flow(self):
        engine, _, router = self.create_system()

        request = create_request()

        router.route(request)

        self.assertEqual(
            engine.executed_request.identity.identity_id,
            "identity:user:123",
        )

        self.assertEqual(
            engine.executed_request.identity.principal,
            "user:123",
        )

    def test_engine_does_not_modify_identity(self):
        engine, _, router = self.create_system()

        request = create_request()

        original_identity = request.identity

        router.route(request)

        self.assertIs(
            request.identity,
            original_identity,
        )

    # --------------------------------------------------
    # Runtime boundary
    # --------------------------------------------------

    def test_engine_result_is_not_execution_result(self):
        _, _, router = self.create_system()

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

    def test_router_does_not_execute_runtime(self):
        _, _, router = self.create_system()

        result = router.route(
            create_request()
        )

        self.assertIsInstance(
            result,
            EngineResult,
        )

        self.assertFalse(
            hasattr(
                router,
                "execute_plan",
            )
        )

    # --------------------------------------------------
    # Intelligence boundary
    # --------------------------------------------------

    def test_engine_does_not_require_intelligence(self):
        engine, _, _ = self.create_system()

        self.assertFalse(
            hasattr(
                engine,
                "reason",
            )
        )

        self.assertFalse(
            hasattr(
                engine,
                "think",
            )
        )

        self.assertFalse(
            hasattr(
                engine,
                "generate_strategy",
            )
        )

    def test_router_does_not_require_intelligence(self):
        _, _, router = self.create_system()

        self.assertFalse(
            hasattr(
                router,
                "reason",
            )
        )

        self.assertFalse(
            hasattr(
                router,
                "think",
            )
        )

    # --------------------------------------------------
    # Adapter boundary
    # --------------------------------------------------

    def test_adapter_receives_engine_request_not_runtime_result(self):
        engine, _, router = self.create_system()

        request = create_request()

        router.route(request)

        self.assertIsInstance(
            engine.executed_request,
            EngineRequest,
        )

    def test_adapter_returns_engine_result(self):
        engine, _, router = self.create_system()

        result = router.route(
            create_request()
        )

        self.assertIsInstance(
            result,
            EngineResult,
        )

    # --------------------------------------------------
    # Registry boundary
    # --------------------------------------------------

    def test_registry_only_selects_registered_engine(self):
        engine, registry, _ = self.create_system()

        retrieved = registry.get(
            "engine.integrated"
        )

        self.assertIs(
            retrieved,
            engine,
        )

    def test_unknown_engine_never_reaches_engine(self):
        engine, _, router = self.create_system()

        request = EngineRequest(
            request_id="request:unknown",
            identity=create_identity(),
            input={
                "task": "test",
            },
            metadata={
                "engine_id": "engine.unknown",
            },
        )

        with self.assertRaises(KeyError):
            router.route(request)

        self.assertIsNone(
            engine.executed_request
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)