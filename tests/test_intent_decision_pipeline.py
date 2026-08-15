from __future__ import annotations

import unittest

from ai_os.intelligence import (
    Decision,
    DecisionGenerationCancelledError,
    DecisionGeneratorContract,
    DecisionKind,
    Intent,
    IntentDecisionPipeline,
    IntentDecisionResult,
    IntentDecisionStatus,
    RuleBasedDecisionGenerator,
)
from ai_os.runtime.cancellation import CancellationSource


class MatchingRule:
    def __init__(self, kind: DecisionKind):
        self.kind = kind
        self.calls = 0

    def evaluate(self, intent):
        self.calls += 1
        return self.kind


class NoMatchRule:
    def evaluate(self, intent):
        return None


class FailingGenerator:
    def generate(
        self,
        intent,
        decision_id,
        cancellation_token=None,
    ):
        raise RuntimeError("generator failed")


class WrongResultGenerator:
    def generate(
        self,
        intent,
        decision_id,
        cancellation_token=None,
    ):
        return "invalid"


class TrackingGenerator:
    def __init__(self, result):
        self.result = result
        self.calls = 0
        self.received_intents = []
        self.received_decision_ids = []
        self.received_tokens = []

    def generate(
        self,
        intent,
        decision_id,
        cancellation_token=None,
    ):
        self.calls += 1
        self.received_intents.append(intent)
        self.received_decision_ids.append(decision_id)
        self.received_tokens.append(cancellation_token)
        return self.result


class IntentDecisionPipelineTests(unittest.TestCase):

    def create_intent(
        self,
        intent_id="intent:test",
        goal="generate_report",
    ):
        return Intent(
            intent_id=intent_id,
            goal=goal,
        )

    def create_generator(
        self,
        kind=DecisionKind.ANSWER,
    ):
        return RuleBasedDecisionGenerator(
            rules=(
                MatchingRule(kind),
            )
        )

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def test_valid_generator_matches_structural_contract(self):
        generator = self.create_generator()

        self.assertIsInstance(
            generator,
            DecisionGeneratorContract,
        )

    def test_invalid_generator_does_not_match_contract(self):
        self.assertFalse(
            isinstance(
                object(),
                DecisionGeneratorContract,
            )
        )

    def test_pipeline_rejects_invalid_generator(self):
        with self.assertRaises(TypeError):
            IntentDecisionPipeline(
                decision_generator=object(),
            )

    # ------------------------------------------------------------------
    # Basic successful pipeline
    # ------------------------------------------------------------------

    def test_single_intent_produces_decision(self):
        intent = self.create_intent()

        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator(
                DecisionKind.ANSWER
            )
        )

        result = pipeline.run(
            intent,
            "decision:test",
        )

        self.assertIsInstance(
            result,
            IntentDecisionResult,
        )

        self.assertEqual(
            result.status,
            IntentDecisionStatus.RESOLVED,
        )

        self.assertIs(
            result.intent,
            intent,
        )

        self.assertIsInstance(
            result.decision,
            Decision,
        )

    def test_decision_kind_is_preserved(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator(
                DecisionKind.USE_WORKFLOW
            )
        )

        result = pipeline.run(
            self.create_intent(),
            "decision:test",
        )

        self.assertEqual(
            result.decision.kind,
            DecisionKind.USE_WORKFLOW,
        )

    def test_intent_is_preserved_exactly(self):
        intent = self.create_intent()

        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        result = pipeline.run(
            intent,
            "decision:test",
        )

        self.assertIs(
            result.intent,
            intent,
        )

        self.assertEqual(
            result.decision.intent_id,
            intent.intent_id,
        )

    def test_decision_id_is_preserved(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        result = pipeline.run(
            self.create_intent(),
            "decision:123",
        )

        self.assertEqual(
            result.decision.decision_id,
            "decision:123",
        )

    # ------------------------------------------------------------------
    # Generator interaction
    # ------------------------------------------------------------------

    def test_generator_is_called_exactly_once(self):
        real_generator = self.create_generator()

        pipeline = IntentDecisionPipeline(
            decision_generator=real_generator
        )

        pipeline.run(
            self.create_intent(),
            "decision:test",
        )

        # RuleBasedDecisionGenerator itself is reusable and its
        # injected rule is called once.
        rule = MatchingRule(DecisionKind.ANSWER)

        generator = RuleBasedDecisionGenerator(
            rules=(rule,)
        )

        IntentDecisionPipeline(
            decision_generator=generator
        ).run(
            self.create_intent(),
            "decision:test",
        )

        self.assertEqual(
            rule.calls,
            1,
        )

    def test_generator_receives_exact_intent(self):
        intent = self.create_intent()

        generated_decision = self.create_generator().generate(
            intent,
            "decision:test",
        )

        tracking = TrackingGenerator(
            generated_decision
        )

        pipeline = IntentDecisionPipeline(
            decision_generator=tracking
        )

        pipeline.run(
            intent,
            "decision:test",
        )

        self.assertEqual(
            tracking.calls,
            1,
        )

        self.assertIs(
            tracking.received_intents[0],
            intent,
        )

    def test_generator_receives_exact_decision_id(self):
        generated_decision = self.create_generator().generate(
            self.create_intent(),
            "decision:test",
        )

        tracking = TrackingGenerator(
            generated_decision
        )

        IntentDecisionPipeline(
            decision_generator=tracking
        ).run(
            self.create_intent(),
            "decision:123",
        )

        self.assertEqual(
            tracking.received_decision_ids,
            ["decision:123"],
        )

    def test_cancellation_token_is_forwarded(self):
        source = CancellationSource()

        generated_decision = self.create_generator().generate(
            self.create_intent(),
            "decision:test",
        )

        tracking = TrackingGenerator(
            generated_decision
        )

        pipeline = IntentDecisionPipeline(
            decision_generator=tracking
        )

        pipeline.run(
            self.create_intent(),
            "decision:test",
            source.token,
        )

        self.assertIs(
            tracking.received_tokens[0],
            source.token,
        )

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------

    def test_invalid_intent_rejected(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                "invalid",
                "decision:test",
            )

    def test_none_intent_rejected(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                None,
                "decision:test",
            )

    def test_empty_decision_id_rejected(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        with self.assertRaises(ValueError):
            pipeline.run(
                self.create_intent(),
                "",
            )

    def test_whitespace_decision_id_rejected(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        with self.assertRaises(ValueError):
            pipeline.run(
                self.create_intent(),
                "   ",
            )

    def test_invalid_decision_id_type_rejected(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                self.create_intent(),
                123,
            )

    # ------------------------------------------------------------------
    # Output validation
    # ------------------------------------------------------------------

    def test_invalid_generator_result_rejected(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=WrongResultGenerator()
        )

        with self.assertRaises(TypeError):
            pipeline.run(
                self.create_intent(),
                "decision:test",
            )

    def test_generator_failure_propagates(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=FailingGenerator()
        )

        with self.assertRaises(RuntimeError):
            pipeline.run(
                self.create_intent(),
                "decision:test",
            )

    def test_no_matching_rule_propagates(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=RuleBasedDecisionGenerator(
                rules=(NoMatchRule(),)
            )
        )

        with self.assertRaises(Exception) as caught:
            pipeline.run(
                self.create_intent(),
                "decision:test",
            )

        self.assertEqual(
            type(caught.exception).__name__,
            "DecisionUndeterminedError",
        )

    def test_cancellation_propagates(self):
        source = CancellationSource()
        source.cancel()

        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        with self.assertRaises(
            DecisionGenerationCancelledError
        ):
            pipeline.run(
                self.create_intent(),
                "decision:test",
                source.token,
            )

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------

    def test_result_is_immutable(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        result = pipeline.run(
            self.create_intent(),
            "decision:test",
        )

        with self.assertRaises(AttributeError):
            result.status = IntentDecisionStatus.RESOLVED

    def test_result_metadata_is_immutable(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        result = pipeline.run(
            self.create_intent(),
            "decision:test",
        )

        with self.assertRaises(TypeError):
            result.metadata["changed"] = True

    def test_pipeline_does_not_mutate_intent(self):
        intent = self.create_intent()

        original_goal = intent.goal
        original_parameters = intent.parameters
        original_constraints = intent.constraints

        IntentDecisionPipeline(
            decision_generator=self.create_generator()
        ).run(
            intent,
            "decision:test",
        )

        self.assertEqual(
            intent.goal,
            original_goal,
        )

        self.assertEqual(
            intent.parameters,
            original_parameters,
        )

        self.assertEqual(
            intent.constraints,
            original_constraints,
        )

    # ------------------------------------------------------------------
    # Boundary enforcement
    # ------------------------------------------------------------------

    def test_pipeline_has_no_proposal_attribute(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "proposal",
            )
        )

    def test_pipeline_has_no_agent_attribute(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "agent",
            )
        )

    def test_pipeline_has_no_runtime_attribute(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "runtime",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "scheduler",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "task_executor",
            )
        )

    def test_pipeline_has_no_execution_api(self):
        pipeline = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "execute",
            )
        )

        self.assertFalse(
            hasattr(
                pipeline,
                "run_task",
            )
        )

    def test_pipeline_does_not_create_proposal(self):
        result = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        ).run(
            self.create_intent(),
            "decision:test",
        )

        self.assertFalse(
            hasattr(
                result,
                "proposal",
            )
        )

    def test_pipeline_does_not_create_execution_plan(self):
        result = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        ).run(
            self.create_intent(),
            "decision:test",
        )

        self.assertFalse(
            hasattr(
                result,
                "execution_plan",
            )
        )

        self.assertFalse(
            hasattr(
                result,
                "steps",
            )
        )

    # ------------------------------------------------------------------
    # Reusability / isolation
    # ------------------------------------------------------------------

    def test_pipeline_is_reusable(self):
        rule = MatchingRule(
            DecisionKind.ANSWER
        )

        generator = RuleBasedDecisionGenerator(
            rules=(rule,)
        )

        pipeline = IntentDecisionPipeline(
            decision_generator=generator
        )

        first_intent = self.create_intent(
            "intent:first",
            "first_goal",
        )

        second_intent = self.create_intent(
            "intent:second",
            "second_goal",
        )

        first = pipeline.run(
            first_intent,
            "decision:first",
        )

        second = pipeline.run(
            second_intent,
            "decision:second",
        )

        self.assertIs(
            first.intent,
            first_intent,
        )

        self.assertIs(
            second.intent,
            second_intent,
        )

        self.assertEqual(
            first.decision.intent_id,
            "intent:first",
        )

        self.assertEqual(
            second.decision.intent_id,
            "intent:second",
        )

        self.assertEqual(
            first.decision.decision_id,
            "decision:first",
        )

        self.assertEqual(
            second.decision.decision_id,
            "decision:second",
        )

        self.assertEqual(
            rule.calls,
            2,
        )

    # ------------------------------------------------------------------
    # Semantic boundary
    # ------------------------------------------------------------------

    def test_result_contains_only_intent_and_decision_semantics(self):
        result = IntentDecisionPipeline(
            decision_generator=self.create_generator()
        ).run(
            self.create_intent(),
            "decision:test",
        )

        self.assertIsInstance(
            result.intent,
            Intent,
        )

        self.assertIsInstance(
            result.decision,
            Decision,
        )

        self.assertFalse(
            hasattr(result, "reasoning")
        )

        self.assertFalse(
            hasattr(result, "resolution")
        )

        self.assertFalse(
            hasattr(result, "proposal")
        )

        self.assertFalse(
            hasattr(result, "agent_decision")
        )

        self.assertFalse(
            hasattr(result, "execution_plan")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)