from __future__ import annotations

import unittest

from ai_os.intelligence import (
    IntelligenceFailure,
    IntelligenceFailureBoundary,
    IntelligenceOperationResult,
    IntelligenceOperationStatus,
)
from ai_os.runtime.cancellation import CancellationSource


class IntelligenceFailureBoundaryTests(unittest.TestCase):

    def setUp(self):
        self.boundary = IntelligenceFailureBoundary()

    def test_success_is_completed(self):
        result = self.boundary.run(
            lambda: "success"
        )

        self.assertEqual(
            result.status,
            IntelligenceOperationStatus.COMPLETED,
        )

        self.assertEqual(
            result.value,
            "success",
        )

        self.assertIsNone(
            result.failure,
        )

    def test_success_preserves_exact_object(self):
        value = object()

        result = self.boundary.run(
            lambda: value
        )

        self.assertIs(
            result.value,
            value,
        )

    def test_failure_is_normalized(self):
        result = self.boundary.run(
            lambda: (_ for _ in ()).throw(
                RuntimeError("boom")
            )
        )

        self.assertEqual(
            result.status,
            IntelligenceOperationStatus.FAILED,
        )

        self.assertIsInstance(
            result.failure,
            IntelligenceFailure,
        )

        self.assertEqual(
            result.failure.exception_type,
            "RuntimeError",
        )

        self.assertEqual(
            result.failure.message,
            "boom",
        )

    def test_failure_does_not_return_value(self):
        result = self.boundary.run(
            lambda: (_ for _ in ()).throw(
                RuntimeError("boom")
            )
        )

        self.assertIsNone(
            result.value,
        )

    def test_already_cancelled_does_not_start_operation(self):
        source = CancellationSource()
        source.cancel()

        called = []

        result = self.boundary.run(
            lambda: called.append(True),
            source.token,
        )

        self.assertEqual(
            result.status,
            IntelligenceOperationStatus.CANCELLED,
        )

        self.assertEqual(
            called,
            [],
        )

    def test_cancelled_operation_returns_cancelled(self):
        source = CancellationSource()

        def operation():
            source.cancel()
            raise RuntimeError("cancelled")

        result = self.boundary.run(
            operation,
            source.token,
        )

        self.assertEqual(
            result.status,
            IntelligenceOperationStatus.CANCELLED,
        )

        self.assertIsNone(
            result.failure,
        )

    def test_non_cancelled_exception_is_failed(self):
        source = CancellationSource()

        result = self.boundary.run(
            lambda: (_ for _ in ()).throw(
                ValueError("bad input")
            ),
            source.token,
        )

        self.assertEqual(
            result.status,
            IntelligenceOperationStatus.FAILED,
        )

        self.assertEqual(
            result.failure.exception_type,
            "ValueError",
        )

    def test_success_wins_over_late_cancellation(self):
        source = CancellationSource()

        result = self.boundary.run(
            lambda: "done",
            source.token,
        )

        source.cancel()

        self.assertEqual(
            result.status,
            IntelligenceOperationStatus.COMPLETED,
        )

        self.assertEqual(
            result.value,
            "done",
        )

    def test_same_token_is_visible_to_operation_via_closure(self):
        source = CancellationSource()

        observed = []

        def operation():
            observed.append(
                source.token
            )
            return "ok"

        result = self.boundary.run(
            operation,
            source.token,
        )

        self.assertIs(
            observed[0],
            source.token,
        )

        self.assertEqual(
            result.status,
            IntelligenceOperationStatus.COMPLETED,
        )

    def test_invalid_operation_rejected(self):
        with self.assertRaises(TypeError):
            self.boundary.run("invalid")

    def test_none_operation_rejected(self):
        with self.assertRaises(TypeError):
            self.boundary.run(None)

    def test_invalid_token_rejected(self):
        with self.assertRaises(TypeError):
            self.boundary.run(
                lambda: "ok",
                object(),
            )

    def test_result_is_immutable(self):
        result = self.boundary.run(
            lambda: "ok"
        )

        with self.assertRaises(AttributeError):
            result.status = IntelligenceOperationStatus.FAILED

    def test_failure_is_immutable(self):
        result = self.boundary.run(
            lambda: (_ for _ in ()).throw(
                RuntimeError("boom")
            )
        )

        with self.assertRaises(AttributeError):
            result.failure.message = "changed"

    def test_metadata_is_immutable(self):
        result = IntelligenceOperationResult(
            status=IntelligenceOperationStatus.COMPLETED,
            value="ok",
            metadata={
                "stage": "test",
            },
        )

        with self.assertRaises(TypeError):
            result.metadata["changed"] = True

    def test_completed_cannot_contain_failure(self):
        with self.assertRaises(ValueError):
            IntelligenceOperationResult(
                status=IntelligenceOperationStatus.COMPLETED,
                failure=IntelligenceFailure(
                    "RuntimeError",
                    "bad",
                ),
            )

    def test_failed_requires_failure(self):
        with self.assertRaises(ValueError):
            IntelligenceOperationResult(
                status=IntelligenceOperationStatus.FAILED,
            )

    def test_cancelled_cannot_contain_failure(self):
        with self.assertRaises(ValueError):
            IntelligenceOperationResult(
                status=IntelligenceOperationStatus.CANCELLED,
                failure=IntelligenceFailure(
                    "RuntimeError",
                    "bad",
                ),
            )

    def test_semantic_result_is_not_interpreted_as_failure(self):
        semantic_result = {
            "status": "rejected",
        }

        result = self.boundary.run(
            lambda: semantic_result
        )

        self.assertEqual(
            result.status,
            IntelligenceOperationStatus.COMPLETED,
        )

        self.assertIs(
            result.value,
            semantic_result,
        )

    def test_boundary_is_reusable(self):
        first = self.boundary.run(
            lambda: "first"
        )

        second = self.boundary.run(
            lambda: "second"
        )

        self.assertEqual(
            first.value,
            "first",
        )

        self.assertEqual(
            second.value,
            "second",
        )

    def test_no_execution_api(self):
        self.assertFalse(
            hasattr(
                self.boundary,
                "execute",
            )
        )

        self.assertFalse(
            hasattr(
                self.boundary,
                "run_task",
            )
        )

    def test_no_runtime_dependency_state(self):
        self.assertFalse(
            hasattr(
                self.boundary,
                "runtime",
            )
        )

        self.assertFalse(
            hasattr(
                self.boundary,
                "scheduler",
            )
        )

        self.assertFalse(
            hasattr(
                self.boundary,
                "task_executor",
            )
        )

    def test_failure_message_is_preserved(self):
        result = self.boundary.run(
            lambda: (_ for _ in ()).throw(
                RuntimeError("specific failure")
            )
        )

        self.assertEqual(
            result.failure.message,
            "specific failure",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)