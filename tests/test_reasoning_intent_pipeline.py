import unittest

from ai_os.intelligence import (
    IntelligenceContext,
    Intent,
    IntentCandidate,
    IntentExtractor,
    IntentSelector,
    Reasoner,
    ReasoningIntentPipeline,
    ReasoningIntentResult,
    ReasoningIntentStatus,
    ReasoningResolution,
    ReasoningResolutionStatus,
    ReasoningResult,
    ReasoningResolver,
)


class FakeReasoner:
    def __init__(self, result):
        self.result = result
        self.calls = 0
        self.received_contexts = []
        self.received_tokens = []

    def reason(self, context, cancellation_token=None):
        self.calls += 1
        self.received_contexts.append(context)
        self.received_tokens.append(cancellation_token)
        return self.result


class WrongResultReasoner:
    def reason(self, context, cancellation_token=None):
        return "invalid"


class RaisingReasoner:
    def reason(self, context, cancellation_token=None):
        raise RuntimeError("reasoning failed")


class TrackingResolver:
    def __init__(self, result):
        self.result = result
        self.calls = 0
        self.received_results = []
        self.received_indexes = []

    def resolve(self, result, candidate_index=None):
        self.calls += 1
        self.received_results.append(result)
        self.received_indexes.append(candidate_index)
        return self.result


class WrongResolver:
    def resolve(self, result, candidate_index=None):
        return "invalid"


class TrackingSelector:
    def __init__(self, candidate):
        self.candidate = candidate
        self.calls = 0
        self.received_results = []
        self.received_indexes = []

    def select(self, result, candidate_index=None):
        self.calls += 1
        self.received_results.append(result)
        self.received_indexes.append(candidate_index)
        return self.candidate


class WrongSelector:
    def select(self, result, candidate_index=None):
        return "invalid"


class TrackingExtractor:
    def __init__(self, intent):
        self.intent = intent
        self.calls = 0
        self.received_candidates = []
        self.received_ids = []

    def extract(self, candidate, intent_id):
        self.calls += 1
        self.received_candidates.append(candidate)
        self.received_ids.append(intent_id)
        return self.intent


class WrongExtractor:
    def extract(self, candidate, intent_id):
        return "invalid"


class ReasoningIntentPipelineTests(unittest.TestCase):

    def make_context(self, value="test request"):
        return IntelligenceContext(
            input=value,
        )

    def make_candidate(self, goal="generate_report"):
        return IntentCandidate(
            goal=goal,
        )

    def make_reasoning_result(self, *candidates):
        return ReasoningResult(
            intent_candidates=tuple(candidates),
        )

    def make_intent(self, intent_id="intent:test"):
        return Intent(
            intent_id=intent_id,
            goal="generate_report",
        )

    def make_pipeline(
        self,
        reasoning,
        resolver=None,
        selector=None,
        extractor=None,
    ):
        return ReasoningIntentPipeline(
            reasoner=FakeReasoner(reasoning),
            resolver=resolver,
            selector=selector,
            extractor=extractor,
        )

    def test_single_candidate_resolves_to_intent(self):
        candidate = self.make_candidate()

        pipeline = self.make_pipeline(
            self.make_reasoning_result(candidate)
        )

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertEqual(
            result.status,
            ReasoningIntentStatus.RESOLVED,
        )

        self.assertIsInstance(
            result.intent,
            Intent,
        )

        self.assertEqual(
            result.intent.goal,
            "generate_report",
        )

    def test_result_contains_context(self):
        context = self.make_context()

        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        result = pipeline.run(
            context,
            intent_id="intent:test",
        )

        self.assertIs(
            result.context,
            context,
        )

    def test_result_contains_reasoning(self):
        reasoning = self.make_reasoning_result(
            self.make_candidate()
        )

        pipeline = self.make_pipeline(reasoning)

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertIs(
            result.reasoning,
            reasoning,
        )

    def test_result_contains_resolution(self):
        reasoning = self.make_reasoning_result(
            self.make_candidate()
        )

        pipeline = self.make_pipeline(reasoning)

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertIsInstance(
            result.resolution,
            ReasoningResolution,
        )

        self.assertEqual(
            result.resolution.status,
            ReasoningResolutionStatus.READY,
        )

    def test_zero_candidates_produce_no_intent(self):
        pipeline = self.make_pipeline(
            ReasoningResult()
        )

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertEqual(
            result.status,
            ReasoningIntentStatus.NO_INTENT,
        )

        self.assertIsNone(
            result.intent,
        )

    def test_multiple_candidates_require_selection(self):
        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate("sales_report"),
                self.make_candidate("financial_report"),
            )
        )

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertEqual(
            result.status,
            ReasoningIntentStatus.AMBIGUOUS,
        )

        self.assertIsNone(
            result.intent,
        )

        self.assertEqual(
            result.resolution.status,
            ReasoningResolutionStatus.CLARIFICATION_REQUIRED,
        )

    def test_explicit_candidate_index_resolves_multiple_candidates(self):
        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate("sales_report"),
                self.make_candidate("financial_report"),
            )
        )

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
            candidate_index=1,
        )

        self.assertEqual(
            result.status,
            ReasoningIntentStatus.RESOLVED,
        )

        self.assertEqual(
            result.intent.goal,
            "financial_report",
        )

        self.assertEqual(
            result.resolution.candidate_index,
            1,
        )

    def test_reasoner_called_exactly_once(self):
        reasoner = FakeReasoner(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        pipeline = ReasoningIntentPipeline(
            reasoner=reasoner,
        )

        pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertEqual(
            reasoner.calls,
            1,
        )

    def test_reasoner_receives_exact_context(self):
        context = self.make_context()

        reasoner = FakeReasoner(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        pipeline = ReasoningIntentPipeline(
            reasoner=reasoner,
        )

        pipeline.run(
            context,
            intent_id="intent:test",
        )

        self.assertIs(
            reasoner.received_contexts[0],
            context,
        )

    def test_cancellation_token_is_forwarded_to_reasoner(self):
        token = object()

        reasoner = FakeReasoner(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        pipeline = ReasoningIntentPipeline(
            reasoner=reasoner,
        )

        pipeline.run(
            self.make_context(),
            intent_id="intent:test",
            cancellation_token=token,
        )

        self.assertIs(
            reasoner.received_tokens[0],
            token,
        )

    def test_resolver_receives_exact_reasoning_result(self):
        reasoning = self.make_reasoning_result(
            self.make_candidate()
        )

        resolution = ReasoningResolution(
            status=ReasoningResolutionStatus.READY,
            candidate_index=0,
        )

        resolver = TrackingResolver(
            resolution
        )

        pipeline = self.make_pipeline(
            reasoning,
            resolver=resolver,
        )

        pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertEqual(
            resolver.calls,
            1,
        )

        self.assertIs(
            resolver.received_results[0],
            reasoning,
        )

    def test_candidate_index_is_forwarded_to_resolver(self):
        reasoning = self.make_reasoning_result(
            self.make_candidate(),
            self.make_candidate("other_goal"),
        )

        resolution = ReasoningResolution(
            status=ReasoningResolutionStatus.READY,
            candidate_index=1,
        )

        resolver = TrackingResolver(
            resolution
        )

        pipeline = self.make_pipeline(
            reasoning,
            resolver=resolver,
        )

        pipeline.run(
            self.make_context(),
            intent_id="intent:test",
            candidate_index=1,
        )

        self.assertEqual(
            resolver.received_indexes,
            [1],
        )

    def test_selector_not_called_when_unresolved(self):
        candidate = self.make_candidate()

        selector = TrackingSelector(
            candidate
        )

        pipeline = self.make_pipeline(
            ReasoningResult(),
            selector=selector,
        )

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertEqual(
            result.status,
            ReasoningIntentStatus.NO_INTENT,
        )

        self.assertEqual(
            selector.calls,
            0,
        )

    def test_extractor_not_called_when_unresolved(self):
        extractor = TrackingExtractor(
            self.make_intent()
        )

        pipeline = self.make_pipeline(
            ReasoningResult(),
            extractor=extractor,
        )

        pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertEqual(
            extractor.calls,
            0,
        )

    def test_selector_not_called_when_ambiguous(self):
        selector = TrackingSelector(
            self.make_candidate()
        )

        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate("a"),
                self.make_candidate("b"),
            ),
            selector=selector,
        )

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertEqual(
            result.status,
            ReasoningIntentStatus.AMBIGUOUS,
        )

        self.assertEqual(
            selector.calls,
            0,
        )

    def test_extractor_not_called_when_ambiguous(self):
        extractor = TrackingExtractor(
            self.make_intent()
        )

        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate("a"),
                self.make_candidate("b"),
            ),
            extractor=extractor,
        )

        pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertEqual(
            extractor.calls,
            0,
        )

    def test_selector_receives_resolved_candidate_index(self):
        reasoning = self.make_reasoning_result(
            self.make_candidate("a"),
            self.make_candidate("b"),
        )

        resolution = ReasoningResolution(
            status=ReasoningResolutionStatus.READY,
            candidate_index=1,
        )

        resolver = TrackingResolver(
            resolution
        )

        selector = TrackingSelector(
            self.make_candidate("b")
        )

        pipeline = self.make_pipeline(
            reasoning,
            resolver=resolver,
            selector=selector,
        )

        pipeline.run(
            self.make_context(),
            intent_id="intent:test",
            candidate_index=1,
        )

        self.assertEqual(
            selector.received_indexes,
            [1],
        )

    def test_extractor_receives_selected_candidate(self):
        candidate = self.make_candidate()

        selector = TrackingSelector(
            candidate
        )

        extractor = TrackingExtractor(
            self.make_intent()
        )

        pipeline = self.make_pipeline(
            self.make_reasoning_result(candidate),
            selector=selector,
            extractor=extractor,
        )

        pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertIs(
            extractor.received_candidates[0],
            candidate,
        )

    def test_extractor_receives_supplied_intent_id(self):
        extractor = TrackingExtractor(
            self.make_intent()
        )

        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            ),
            extractor=extractor,
        )

        pipeline.run(
            self.make_context(),
            intent_id="intent:123",
        )

        self.assertEqual(
            extractor.received_ids,
            ["intent:123"],
        )

    def test_custom_selector_and_extractor_are_used(self):
        candidate = self.make_candidate()

        selector = TrackingSelector(
            candidate
        )

        intent = self.make_intent(
            "intent:custom"
        )

        extractor = TrackingExtractor(
            intent
        )

        pipeline = self.make_pipeline(
            self.make_reasoning_result(candidate),
            selector=selector,
            extractor=extractor,
        )

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:custom",
        )

        self.assertEqual(
            selector.calls,
            1,
        )

        self.assertEqual(
            extractor.calls,
            1,
        )

        self.assertIs(
            result.intent,
            intent,
        )

    def test_invalid_reasoner_rejected(self):
        with self.assertRaises(TypeError):
            ReasoningIntentPipeline(
                reasoner="invalid",
            )

    def test_invalid_resolver_rejected(self):
        reasoner = FakeReasoner(
            ReasoningResult()
        )

        with self.assertRaises(TypeError):
            ReasoningIntentPipeline(
                reasoner=reasoner,
                resolver="invalid",
            )

    def test_invalid_selector_rejected(self):
        reasoner = FakeReasoner(
            ReasoningResult()
        )

        with self.assertRaises(TypeError):
            ReasoningIntentPipeline(
                reasoner=reasoner,
                selector="invalid",
            )

    def test_invalid_extractor_rejected(self):
        reasoner = FakeReasoner(
            ReasoningResult()
        )

        with self.assertRaises(TypeError):
            ReasoningIntentPipeline(
                reasoner=reasoner,
                extractor="invalid",
            )

    def test_invalid_context_rejected(self):
        pipeline = self.make_pipeline(
            ReasoningResult()
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                "invalid",
                intent_id="intent:test",
            )

    def test_empty_intent_id_rejected(self):
        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        with self.assertRaises(ValueError):
            pipeline.run(
                self.make_context(),
                intent_id="",
            )

    def test_whitespace_intent_id_rejected(self):
        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        with self.assertRaises(ValueError):
            pipeline.run(
                self.make_context(),
                intent_id="   ",
            )

    def test_invalid_intent_id_type_rejected(self):
        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                self.make_context(),
                intent_id=123,
            )

    def test_invalid_candidate_index_type_rejected(self):
        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                self.make_context(),
                intent_id="intent:test",
                candidate_index="0",
            )

    def test_bool_candidate_index_rejected(self):
        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                self.make_context(),
                intent_id="intent:test",
                candidate_index=True,
            )

    def test_wrong_reasoner_result_rejected(self):
        pipeline = ReasoningIntentPipeline(
            reasoner=WrongResultReasoner(),
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                self.make_context(),
                intent_id="intent:test",
            )

    def test_wrong_resolver_result_rejected(self):
        pipeline = ReasoningIntentPipeline(
            reasoner=FakeReasoner(
                self.make_reasoning_result(
                    self.make_candidate()
                )
            ),
            resolver=WrongResolver(),
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                self.make_context(),
                intent_id="intent:test",
            )

    def test_wrong_selector_result_rejected(self):
        pipeline = ReasoningIntentPipeline(
            reasoner=FakeReasoner(
                self.make_reasoning_result(
                    self.make_candidate()
                )
            ),
            selector=WrongSelector(),
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                self.make_context(),
                intent_id="intent:test",
            )

    def test_wrong_extractor_result_rejected(self):
        pipeline = ReasoningIntentPipeline(
            reasoner=FakeReasoner(
                self.make_reasoning_result(
                    self.make_candidate()
                )
            ),
            extractor=WrongExtractor(),
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                self.make_context(),
                intent_id="intent:test",
            )

    def test_reasoner_exception_propagates(self):
        pipeline = ReasoningIntentPipeline(
            reasoner=RaisingReasoner(),
        )

        with self.assertRaises(RuntimeError):
            pipeline.run(
                self.make_context(),
                intent_id="intent:test",
            )

    def test_pipeline_does_not_create_decision(self):
        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertFalse(
            hasattr(result, "decision")
        )

    def test_pipeline_does_not_create_proposal(self):
        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertFalse(
            hasattr(result, "proposal")
        )

    def test_pipeline_does_not_create_agent_decision(self):
        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertFalse(
            hasattr(result, "agent_decision")
        )

    def test_pipeline_has_no_runtime_dependency(self):
        pipeline = self.make_pipeline(
            ReasoningResult()
        )

        self.assertFalse(
            hasattr(pipeline, "runtime")
        )

        self.assertFalse(
            hasattr(pipeline, "scheduler")
        )

        self.assertFalse(
            hasattr(pipeline, "task_executor")
        )

        self.assertFalse(
            hasattr(pipeline, "task_registry")
        )

    def test_pipeline_has_no_execution_api(self):
        pipeline = self.make_pipeline(
            ReasoningResult()
        )

        self.assertFalse(
            hasattr(pipeline, "execute")
        )

        self.assertFalse(
            hasattr(pipeline, "run_task")
        )

    def test_pipeline_has_no_decision_generator(self):
        pipeline = self.make_pipeline(
            ReasoningResult()
        )

        self.assertFalse(
            hasattr(pipeline, "_decision_generator")
        )

    def test_result_is_immutable(self):
        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        result = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        with self.assertRaises(AttributeError):
            result.status = ReasoningIntentStatus.NO_INTENT

    def test_context_is_not_mutated(self):
        context = self.make_context()

        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        pipeline.run(
            context,
            intent_id="intent:test",
        )

        self.assertEqual(
            context.input,
            "test request",
        )

    def test_pipeline_is_reusable(self):
        reasoner = FakeReasoner(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        pipeline = ReasoningIntentPipeline(
            reasoner=reasoner,
        )

        first = pipeline.run(
            self.make_context("first"),
            intent_id="intent:first",
        )

        second = pipeline.run(
            self.make_context("second"),
            intent_id="intent:second",
        )

        self.assertEqual(
            first.status,
            ReasoningIntentStatus.RESOLVED,
        )

        self.assertEqual(
            second.status,
            ReasoningIntentStatus.RESOLVED,
        )

        self.assertEqual(
            reasoner.calls,
            2,
        )

        self.assertEqual(
            first.intent.intent_id,
            "intent:first",
        )

        self.assertEqual(
            second.intent.intent_id,
            "intent:second",
        )

    def test_ambiguity_does_not_create_intent(self):
        result = self.make_reasoning_result(
            self.make_candidate("a"),
            self.make_candidate("b"),
        )

        pipeline = self.make_pipeline(result)

        output = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertEqual(
            output.status,
            ReasoningIntentStatus.AMBIGUOUS,
        )

        self.assertIsNone(
            output.intent,
        )

    def test_no_intent_does_not_create_intent(self):
        pipeline = self.make_pipeline(
            ReasoningResult()
        )

        output = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertEqual(
            output.status,
            ReasoningIntentStatus.NO_INTENT,
        )

        self.assertIsNone(
            output.intent,
        )

    def test_intent_is_immutable(self):
        pipeline = self.make_pipeline(
            self.make_reasoning_result(
                self.make_candidate()
            )
        )

        output = pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        with self.assertRaises(AttributeError):
            output.intent.goal = "changed"

    def test_pipeline_does_not_mutate_reasoning_result(self):
        reasoning = self.make_reasoning_result(
            self.make_candidate()
        )

        pipeline = self.make_pipeline(
            reasoning
        )

        pipeline.run(
            self.make_context(),
            intent_id="intent:test",
        )

        self.assertIs(
            pipeline._reasoner.result,
            reasoning,
        )

        self.assertEqual(
            len(reasoning.intent_candidates),
            1,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)