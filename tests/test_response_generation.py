from __future__ import annotations

import unittest

from ai_os.intelligence import (
    IntelligenceContext,
    IntelligenceOrchestrationResult,
    IntelligenceOrchestrationStatus,
)
from ai_os.intelligence.response import (
    DefaultResponseGenerator,
    Response,
    ResponseGenerationPipeline,
    ResponseGenerationResult,
    ResponseGeneratorContract,
    ResponseStatus,
)


class TrackingGenerator:
    def __init__(self, response):
        self.response = response
        self.calls = 0
        self.received = []

    def generate(self, result):
        self.calls += 1
        self.received.append(result)
        return self.response


class WrongGenerator:
    def generate(self, result):
        return "invalid"


class RaisingGenerator:
    def generate(self, result):
        raise RuntimeError("response generation failed")


class MissingGenerate:
    pass


class ResponseGenerationTests(unittest.TestCase):

    def context(self):
        return IntelligenceContext(
            input="test"
        )

    def orchestration_result(
        self,
        status=IntelligenceOrchestrationStatus.COMPLETED,
    ):
        return IntelligenceOrchestrationResult(
            status=status,
            context=self.context(),
        )

    def response_for(self, result):
        status_map = {
            IntelligenceOrchestrationStatus.COMPLETED:
                ResponseStatus.COMPLETED,
            IntelligenceOrchestrationStatus.BLOCKED:
                ResponseStatus.BLOCKED,
            IntelligenceOrchestrationStatus.FAILED:
                ResponseStatus.FAILED,
            IntelligenceOrchestrationStatus.CANCELLED:
                ResponseStatus.CANCELLED,
        }

        return Response(
            status=status_map[result.status],
            content="test response",
            source_status=result.status,
        )

    def test_default_generator_matches_contract(self):
        self.assertIsInstance(
            DefaultResponseGenerator(),
            ResponseGeneratorContract,
        )

    def test_missing_generator_method_not_accepted(self):
        self.assertFalse(
            isinstance(
                MissingGenerate(),
                ResponseGeneratorContract,
            )
        )

    def test_invalid_generator_rejected(self):
        with self.assertRaises(TypeError):
            ResponseGenerationPipeline(
                generator=object()
            )

    def test_completed_response(self):
        result = ResponseGenerationPipeline().run(
            self.orchestration_result(
                IntelligenceOrchestrationStatus.COMPLETED
            )
        )

        self.assertEqual(
            result.response.status,
            ResponseStatus.COMPLETED,
        )

        self.assertEqual(
            result.response.source_status,
            IntelligenceOrchestrationStatus.COMPLETED,
        )

        self.assertIn(
            "prepared",
            result.response.content,
        )

    def test_blocked_response(self):
        result = ResponseGenerationPipeline().run(
            self.orchestration_result(
                IntelligenceOrchestrationStatus.BLOCKED
            )
        )

        self.assertEqual(
            result.response.status,
            ResponseStatus.BLOCKED,
        )

    def test_failed_response(self):
        result = ResponseGenerationPipeline().run(
            self.orchestration_result(
                IntelligenceOrchestrationStatus.FAILED
            )
        )

        self.assertEqual(
            result.response.status,
            ResponseStatus.FAILED,
        )

    def test_cancelled_response(self):
        result = ResponseGenerationPipeline().run(
            self.orchestration_result(
                IntelligenceOrchestrationStatus.CANCELLED
            )
        )

        self.assertEqual(
            result.response.status,
            ResponseStatus.CANCELLED,
        )

    def test_source_result_is_preserved(self):
        source = self.orchestration_result()

        result = ResponseGenerationPipeline().run(
            source
        )

        self.assertIs(
            result.source,
            source,
        )

    def test_generator_receives_exact_result(self):
        source = self.orchestration_result()

        response = self.response_for(source)

        generator = TrackingGenerator(
            response
        )

        ResponseGenerationPipeline(
            generator
        ).run(source)

        self.assertEqual(
            generator.calls,
            1,
        )

        self.assertIs(
            generator.received[0],
            source,
        )

    def test_custom_generator_is_used(self):
        source = self.orchestration_result()

        response = self.response_for(source)

        generator = TrackingGenerator(
            response
        )

        result = ResponseGenerationPipeline(
            generator
        ).run(source)

        self.assertIs(
            result.response,
            response,
        )

    def test_wrong_generator_result_rejected(self):
        with self.assertRaises(TypeError):
            ResponseGenerationPipeline(
                WrongGenerator()
            ).run(
                self.orchestration_result()
            )

    def test_generator_failure_propagates(self):
        with self.assertRaises(RuntimeError):
            ResponseGenerationPipeline(
                RaisingGenerator()
            ).run(
                self.orchestration_result()
            )

    def test_invalid_source_result_rejected(self):
        with self.assertRaises(TypeError):
            ResponseGenerationPipeline().run(
                "invalid"
            )

    def test_response_source_status_must_match(self):
        source = self.orchestration_result(
            IntelligenceOrchestrationStatus.COMPLETED
        )

        wrong_response = Response(
            status=ResponseStatus.FAILED,
            content="wrong",
            source_status=(
                IntelligenceOrchestrationStatus.FAILED
            ),
        )

        generator = TrackingGenerator(
            wrong_response
        )

        with self.assertRaises(ValueError):
            ResponseGenerationPipeline(
                generator
            ).run(source)

    def test_response_is_immutable(self):
        response = Response(
            status=ResponseStatus.COMPLETED,
            content="test",
            source_status=(
                IntelligenceOrchestrationStatus.COMPLETED
            ),
        )

        with self.assertRaises(AttributeError):
            response.content = "changed"

    def test_response_metadata_is_immutable(self):
        response = Response(
            status=ResponseStatus.COMPLETED,
            content="test",
            source_status=(
                IntelligenceOrchestrationStatus.COMPLETED
            ),
            metadata={"x": 1},
        )

        with self.assertRaises(TypeError):
            response.metadata["x"] = 2

    def test_pipeline_result_is_immutable(self):
        result = ResponseGenerationPipeline().run(
            self.orchestration_result()
        )

        with self.assertRaises(AttributeError):
            result.response = None

    def test_empty_response_rejected(self):
        with self.assertRaises(ValueError):
            Response(
                status=ResponseStatus.COMPLETED,
                content="   ",
                source_status=(
                    IntelligenceOrchestrationStatus.COMPLETED
                ),
            )

    def test_no_execution_api(self):
        pipeline = ResponseGenerationPipeline()

        self.assertFalse(
            hasattr(pipeline, "execute")
        )

        self.assertFalse(
            hasattr(pipeline, "run_task")
        )

    def test_no_runtime_dependency(self):
        pipeline = ResponseGenerationPipeline()

        self.assertFalse(
            hasattr(pipeline, "runtime")
        )

        self.assertFalse(
            hasattr(pipeline, "scheduler")
        )

        self.assertFalse(
            hasattr(pipeline, "task_executor")
        )

    def test_no_agent_execution(self):
        result = ResponseGenerationPipeline().run(
            self.orchestration_result()
        )

        self.assertFalse(
            hasattr(
                result.response,
                "execution_result",
            )
        )

    def test_completed_does_not_claim_execution(self):
        result = ResponseGenerationPipeline().run(
            self.orchestration_result(
                IntelligenceOrchestrationStatus.COMPLETED
            )
        )

        content = result.response.content.lower()

        self.assertNotIn(
            "executed successfully",
            content,
        )

        self.assertNotIn(
            "workflow completed",
            content,
        )

    def test_pipeline_is_reusable(self):
        pipeline = ResponseGenerationPipeline()

        first = pipeline.run(
            self.orchestration_result(
                IntelligenceOrchestrationStatus.COMPLETED
            )
        )

        second = pipeline.run(
            self.orchestration_result(
                IntelligenceOrchestrationStatus.BLOCKED
            )
        )

        self.assertEqual(
            first.response.status,
            ResponseStatus.COMPLETED,
        )

        self.assertEqual(
            second.response.status,
            ResponseStatus.BLOCKED,
        )

    def test_result_is_correct_type(self):
        result = ResponseGenerationPipeline().run(
            self.orchestration_result()
        )

        self.assertIsInstance(
            result,
            ResponseGenerationResult,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)