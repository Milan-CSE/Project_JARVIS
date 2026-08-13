import unittest

from ai_os.engines import EngineResult, EngineStatus


class EngineResultTests(unittest.TestCase):

    def test_success_result(self):
        result = EngineResult(
            status=EngineStatus.SUCCESS,
            output={"plan": "created"},
        )

        self.assertEqual(
            result.status,
            EngineStatus.SUCCESS,
        )

        self.assertEqual(
            result.output["plan"],
            "created",
        )

        self.assertIsNone(result.error)

    def test_failed_result(self):
        result = EngineResult(
            status=EngineStatus.FAILED,
            error="planning failed",
        )

        self.assertEqual(
            result.status,
            EngineStatus.FAILED,
        )

        self.assertEqual(
            result.error,
            "planning failed",
        )

    def test_cancelled_result(self):
        result = EngineResult(
            status=EngineStatus.CANCELLED,
        )

        self.assertEqual(
            result.status,
            EngineStatus.CANCELLED,
        )

        self.assertIsNone(result.error)

    def test_failed_result_requires_error(self):
        with self.assertRaises(ValueError):
            EngineResult(
                status=EngineStatus.FAILED,
            )

    def test_failed_result_rejects_empty_error(self):
        with self.assertRaises(ValueError):
            EngineResult(
                status=EngineStatus.FAILED,
                error="",
            )

    def test_non_failed_result_rejects_error(self):
        with self.assertRaises(ValueError):
            EngineResult(
                status=EngineStatus.SUCCESS,
                output={"ok": True},
                error="unexpected",
            )

    def test_invalid_status_rejected(self):
        with self.assertRaises(TypeError):
            EngineResult(
                status="success",
                output={"ok": True},
            )

    def test_error_must_be_string(self):
        with self.assertRaises(TypeError):
            EngineResult(
                status=EngineStatus.FAILED,
                error=123,
            )

    def test_result_is_immutable(self):
        result = EngineResult(
            status=EngineStatus.SUCCESS,
            output={"ok": True},
        )

        with self.assertRaises(AttributeError):
            result.status = EngineStatus.FAILED

    def test_output_is_immutable(self):
        result = EngineResult(
            status=EngineStatus.SUCCESS,
            output={"plan": {"step": 1}},
        )

        with self.assertRaises(TypeError):
            result.output["plan"]["step"] = 2

    def test_metadata_is_immutable(self):
        result = EngineResult(
            status=EngineStatus.SUCCESS,
            output={"ok": True},
            metadata={"source": "planner"},
        )

        with self.assertRaises(TypeError):
            result.metadata["source"] = "other"

    def test_non_json_output_rejected(self):
        with self.assertRaises(TypeError):
            EngineResult(
                status=EngineStatus.SUCCESS,
                output={"bad": object()},
            )

    def test_non_json_metadata_rejected(self):
        with self.assertRaises(TypeError):
            EngineResult(
                status=EngineStatus.SUCCESS,
                metadata={"bad": object()},
            )

    def test_round_trip(self):
        result = EngineResult(
            status=EngineStatus.SUCCESS,
            output={
                "plan": {
                    "steps": ["one", "two"],
                }
            },
            metadata={
                "engine": "planner",
            },
        )

        restored = EngineResult.from_json(
            result.to_json()
        )

        self.assertEqual(
            restored.to_dict(),
            result.to_dict(),
        )

    def test_failed_result_round_trip(self):
        result = EngineResult(
            status=EngineStatus.FAILED,
            error="planning failed",
            metadata={
                "engine": "planner",
            },
        )

        restored = EngineResult.from_json(
            result.to_json()
        )

        self.assertEqual(
            restored.to_dict(),
            result.to_dict(),
        )

    def test_execution_result_is_not_engine_result(self):
        from ai_os.runtime.contracts import ExecutionResult

        self.assertIsNot(
            EngineResult,
            ExecutionResult,
        )

    def test_empty_success_output_allowed(self):
        result = EngineResult(
            status=EngineStatus.SUCCESS,
        )

        self.assertIsNone(result.output)

    def test_nested_output_is_immutable(self):
        result = EngineResult(
            status=EngineStatus.SUCCESS,
            output={
                "data": {
                    "items": ["a", "b"],
                }
            },
        )

        with self.assertRaises(TypeError):
            result.output["data"]["items"][0] = "changed"


if __name__ == "__main__":
    unittest.main(verbosity=2)