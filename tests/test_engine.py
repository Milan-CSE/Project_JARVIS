import unittest

from ai_os.engines import (
    Engine,
    EngineRequest,
    EngineResult,
    EngineStatus,
    EngineType,
)
from ai_os.identity import Identity, IdentityType


def create_identity():
    return Identity(
        identity_id="identity:user:123",
        principal="user:123",
        identity_type=IdentityType.USER,
    )


def create_request():
    return EngineRequest(
        request_id="request:123",
        identity=create_identity(),
        input={"task": "plan"},
    )


class ValidEngine:
    @property
    def engine_id(self):
        return "engine.test"

    @property
    def engine_type(self):
        return EngineType.PLANNING

    def execute(self, request):
        return EngineResult(
            status=EngineStatus.SUCCESS,
            output={"received": request.input},
        )


class MissingExecuteEngine:
    @property
    def engine_id(self):
        return "engine.bad"

    @property
    def engine_type(self):
        return EngineType.PLANNING


class MissingTypeEngine:
    @property
    def engine_id(self):
        return "engine.bad"

    def execute(self, request):
        return EngineResult(
            status=EngineStatus.SUCCESS,
        )


class MissingIdEngine:
    @property
    def engine_type(self):
        return EngineType.PLANNING

    def execute(self, request):
        return EngineResult(
            status=EngineStatus.SUCCESS,
        )


class EngineTests(unittest.TestCase):

    def test_valid_implementation_matches_protocol(self):
        engine = ValidEngine()

        self.assertIsInstance(
            engine,
            Engine,
        )

    def test_engine_id_is_available(self):
        engine = ValidEngine()

        self.assertEqual(
            engine.engine_id,
            "engine.test",
        )

    def test_engine_type_is_available(self):
        engine = ValidEngine()

        self.assertEqual(
            engine.engine_type,
            EngineType.PLANNING,
        )

    def test_execute_returns_engine_result(self):
        engine = ValidEngine()

        result = engine.execute(
            create_request()
        )

        self.assertIsInstance(
            result,
            EngineResult,
        )

    def test_execute_receives_engine_request(self):
        engine = ValidEngine()
        request = create_request()

        result = engine.execute(request)

        self.assertEqual(
            result.output["received"],
            request.input,
        )

    def test_invalid_engine_without_execute_rejected(self):
        engine = MissingExecuteEngine()

        self.assertFalse(
            isinstance(engine, Engine)
        )

    def test_invalid_engine_without_type_rejected(self):
        engine = MissingTypeEngine()

        self.assertFalse(
            isinstance(engine, Engine)
        )

    def test_invalid_engine_without_id_rejected(self):
        engine = MissingIdEngine()

        self.assertFalse(
            isinstance(engine, Engine)
        )

    def test_engine_contract_does_not_require_inheritance(self):
        engine = ValidEngine()

        self.assertIsInstance(
            engine,
            Engine,
        )

        self.assertNotIn(
            Engine,
            ValidEngine.__bases__,
        )

        self.assertIsInstance(
            engine,
            Engine,
        )

    def test_engine_does_not_execute_runtime(self):
        engine = ValidEngine()

        result = engine.execute(
            create_request()
        )

        self.assertIsInstance(
            result,
            EngineResult,
        )

        self.assertNotIsInstance(
            result,
            dict,
        )

    def test_engine_type_is_not_identity_type(self):
        engine = ValidEngine()

        self.assertIsInstance(
            engine.engine_type,
            EngineType,
        )

        self.assertNotIsInstance(
            engine.engine_type,
            IdentityType,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)