import unittest

from ai_os.intelligence import (
    DecisionGenerationRule,
    DecisionKind,
    DecisionGenerationCancelledError,
    DecisionUndeterminedError,
    Intent,
    RuleBasedDecisionGenerator,
)
from ai_os.runtime.cancellation import CancellationSource


class NoMatchRule:

    def evaluate(self, intent):
        return None


class MatchingRule:

    def __init__(self, kind):
        self.kind = kind
        self.calls = 0

    def evaluate(self, intent):
        self.calls += 1
        return self.kind


class FailingRule:

    def evaluate(self, intent):
        raise RuntimeError("rule failed")


class InvalidRule:

    def evaluate(self, intent):
        return "not_a_decision"


class StringDecisionRule:

    def evaluate(self, intent):
        return "answer"


class DecisionGeneratorTests(unittest.TestCase):

    def create_intent(self):
        return Intent(
            intent_id="intent:test",
            goal="generate_report",
        )

    def test_valid_rule_matches_protocol(self):
        rule = NoMatchRule()

        self.assertIsInstance(
            rule,
            DecisionGenerationRule,
        )

    def test_invalid_rule_rejected(self):
        with self.assertRaises(TypeError):
            RuleBasedDecisionGenerator(
                rules=("invalid",),
            )

    def test_first_matching_rule_wins(self):
        first = MatchingRule(
            DecisionKind.ANSWER,
        )

        second = MatchingRule(
            DecisionKind.DECLINE,
        )

        generator = RuleBasedDecisionGenerator(
            rules=(
                first,
                second,
            )
        )

        result = generator.generate(
            self.create_intent(),
            "decision:test",
        )

        self.assertEqual(
            result.kind,
            DecisionKind.ANSWER,
        )

        self.assertEqual(
            first.calls,
            1,
        )

        self.assertEqual(
            second.calls,
            0,
        )

    def test_nonmatching_rule_is_skipped(self):
        first = NoMatchRule()

        second = MatchingRule(
            DecisionKind.USE_WORKFLOW,
        )

        result = RuleBasedDecisionGenerator(
            rules=(
                first,
                second,
            )
        ).generate(
            self.create_intent(),
            "decision:test",
        )

        self.assertEqual(
            result.kind,
            DecisionKind.USE_WORKFLOW,
        )

    def test_no_matching_rule_raises(self):
        generator = RuleBasedDecisionGenerator(
            rules=(NoMatchRule(),)
        )

        with self.assertRaises(
            DecisionUndeterminedError
        ):
            generator.generate(
                self.create_intent(),
                "decision:test",
            )

    def test_empty_rules_raise(self):
        generator = RuleBasedDecisionGenerator()

        with self.assertRaises(
            DecisionUndeterminedError
        ):
            generator.generate(
                self.create_intent(),
                "decision:test",
            )

    def test_string_decision_kind_is_normalized(self):
        result = RuleBasedDecisionGenerator(
            rules=(StringDecisionRule(),)
        ).generate(
            self.create_intent(),
            "decision:test",
        )

        self.assertEqual(
            result.kind,
            DecisionKind.ANSWER,
        )

    def test_invalid_rule_output_rejected(self):
        generator = RuleBasedDecisionGenerator(
            rules=(InvalidRule(),)
        )

        with self.assertRaises(TypeError):
            generator.generate(
                self.create_intent(),
                "decision:test",
            )

    def test_rule_exception_propagates(self):
        generator = RuleBasedDecisionGenerator(
            rules=(FailingRule(),)
        )

        with self.assertRaises(RuntimeError):
            generator.generate(
                self.create_intent(),
                "decision:test",
            )

    def test_invalid_intent_rejected(self):
        generator = RuleBasedDecisionGenerator()

        with self.assertRaises(TypeError):
            generator.generate(
                "invalid",
                "decision:test",
            )

    def test_empty_decision_id_rejected(self):
        generator = RuleBasedDecisionGenerator()

        with self.assertRaises(ValueError):
            generator.generate(
                self.create_intent(),
                "",
            )

    def test_invalid_decision_id_type_rejected(self):
        generator = RuleBasedDecisionGenerator()

        with self.assertRaises(TypeError):
            generator.generate(
                self.create_intent(),
                123,
            )

    def test_decision_references_input_intent(self):
        intent = self.create_intent()

        result = RuleBasedDecisionGenerator(
            rules=(
                MatchingRule(
                    DecisionKind.ANSWER,
                ),
            )
        ).generate(
            intent,
            "decision:test",
        )

        self.assertEqual(
            result.intent_id,
            intent.intent_id,
        )

    def test_decision_id_is_preserved(self):
        result = RuleBasedDecisionGenerator(
            rules=(
                MatchingRule(
                    DecisionKind.ANSWER,
                ),
            )
        ).generate(
            self.create_intent(),
            "decision:123",
        )

        self.assertEqual(
            result.decision_id,
            "decision:123",
        )

    def test_generator_does_not_create_proposal(self):
        result = RuleBasedDecisionGenerator(
            rules=(
                MatchingRule(
                    DecisionKind.USE_WORKFLOW,
                ),
            )
        ).generate(
            self.create_intent(),
            "decision:test",
        )

        self.assertFalse(
            hasattr(result, "proposal")
        )

        self.assertFalse(
            hasattr(result, "workflow_id")
        )

    def test_generator_does_not_create_execution_plan(self):
        result = RuleBasedDecisionGenerator(
            rules=(
                MatchingRule(
                    DecisionKind.USE_WORKFLOW,
                ),
            )
        ).generate(
            self.create_intent(),
            "decision:test",
        )

        self.assertFalse(
            hasattr(result, "execution_plan")
        )

        self.assertFalse(
            hasattr(result, "steps")
        )

    def test_generator_has_no_runtime_dependency(self):
        generator = RuleBasedDecisionGenerator()

        self.assertFalse(
            hasattr(generator, "runtime")
        )

        self.assertFalse(
            hasattr(generator, "scheduler")
        )

        self.assertFalse(
            hasattr(generator, "task_executor")
        )

        self.assertFalse(
            hasattr(generator, "task_registry")
        )

    def test_generator_has_no_engine_dependency(self):
        generator = RuleBasedDecisionGenerator()

        self.assertFalse(
            hasattr(generator, "engine")
        )

    def test_generator_has_no_agent_dependency(self):
        generator = RuleBasedDecisionGenerator()

        self.assertFalse(
            hasattr(generator, "agent")
        )

        self.assertFalse(
            hasattr(generator, "handle")
        )

    def test_generator_is_reusable(self):
        rule = MatchingRule(
            DecisionKind.ANSWER,
        )

        generator = RuleBasedDecisionGenerator(
            rules=(rule,)
        )

        first = generator.generate(
            Intent(
                intent_id="intent:one",
                goal="one",
            ),
            "decision:one",
        )

        second = generator.generate(
            Intent(
                intent_id="intent:two",
                goal="two",
            ),
            "decision:two",
        )

        self.assertEqual(
            first.intent_id,
            "intent:one",
        )

        self.assertEqual(
            second.intent_id,
            "intent:two",
        )

        self.assertEqual(
            rule.calls,
            2,
        )

    def test_cancellation_before_generation(self):
        source = CancellationSource()
        source.cancel()

        generator = RuleBasedDecisionGenerator(
            rules=(
                MatchingRule(
                    DecisionKind.ANSWER,
                ),
            )
        )

        with self.assertRaises(
            DecisionGenerationCancelledError
        ):
            generator.generate(
                self.create_intent(),
                "decision:test",
                source.token,
            )

    def test_cancellation_between_rules(self):
        source = CancellationSource()

        class CancelRule:

            def evaluate(self, intent):
                source.cancel()
                return None

        generator = RuleBasedDecisionGenerator(
            rules=(
                CancelRule(),
                MatchingRule(
                    DecisionKind.ANSWER,
                ),
            )
        )

        with self.assertRaises(
            DecisionGenerationCancelledError
        ):
            generator.generate(
                self.create_intent(),
                "decision:test",
                source.token,
            )

    def test_success_returns_before_late_cancellation(self):
        source = CancellationSource()

        class SuccessRule:

            def evaluate(self, intent):
                return DecisionKind.ANSWER

        result = RuleBasedDecisionGenerator(
            rules=(SuccessRule(),)
        ).generate(
            self.create_intent(),
            "decision:test",
            source.token,
        )

        self.assertEqual(
            result.kind,
            DecisionKind.ANSWER,
        )

    def test_generator_does_not_mutate_intent(self):
        intent = self.create_intent()

        RuleBasedDecisionGenerator(
            rules=(
                MatchingRule(
                    DecisionKind.ANSWER,
                ),
            )
        ).generate(
            intent,
            "decision:test",
        )

        self.assertEqual(
            intent.goal,
            "generate_report",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)