import unittest

from ai_os.intelligence import (
    Ambiguity,
    IntelligenceContext,
    IntentCandidate,
    ReasoningCancelledError,
    ReasoningResult,
    ReasoningRule,
    RuleBasedReasoner,
)
from ai_os.runtime.cancellation import CancellationSource


class NoMatchRule:

    def evaluate(self, context):
        return None


class MatchingRule:

    def __init__(self, result):
        self.result = result
        self.calls = 0

    def evaluate(self, context):
        self.calls += 1
        return self.result


class FailingRule:

    def evaluate(self, context):
        raise RuntimeError("rule failed")


class InvalidResultRule:

    def evaluate(self, context):
        return "invalid"


class RuleBasedReasonerTests(unittest.TestCase):

    def test_valid_rule_matches_protocol(self):
        rule = NoMatchRule()

        self.assertIsInstance(
            rule,
            ReasoningRule,
        )

    def test_invalid_rule_rejected(self):
        with self.assertRaises(TypeError):
            RuleBasedReasoner(
                rules=("invalid",),
            )

    def test_empty_rules_return_empty_result(self):
        reasoner = RuleBasedReasoner()

        result = reasoner.reason(
            IntelligenceContext(input="test")
        )

        self.assertIsInstance(
            result,
            ReasoningResult,
        )

        self.assertEqual(
            result,
            ReasoningResult(),
        )

    def test_first_matching_rule_wins(self):
        first = MatchingRule(
            ReasoningResult(
                interpretation="first",
            )
        )

        second = MatchingRule(
            ReasoningResult(
                interpretation="second",
            )
        )

        reasoner = RuleBasedReasoner(
            rules=(
                first,
                second,
            )
        )

        result = reasoner.reason(
            IntelligenceContext(input="test")
        )

        self.assertEqual(
            result.interpretation,
            "first",
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
            ReasoningResult(
                interpretation="second",
            )
        )

        result = RuleBasedReasoner(
            rules=(
                first,
                second,
            )
        ).reason(
            IntelligenceContext(input="test")
        )

        self.assertEqual(
            result.interpretation,
            "second",
        )

    def test_all_nonmatching_rules_return_empty_result(self):
        reasoner = RuleBasedReasoner(
            rules=(
                NoMatchRule(),
                NoMatchRule(),
            )
        )

        result = reasoner.reason(
            IntelligenceContext(input="test")
        )

        self.assertEqual(
            result,
            ReasoningResult(),
        )

    def test_rule_exception_propagates(self):
        reasoner = RuleBasedReasoner(
            rules=(FailingRule(),)
        )

        with self.assertRaises(RuntimeError):
            reasoner.reason(
                IntelligenceContext(input="test")
            )

    def test_invalid_rule_result_rejected(self):
        reasoner = RuleBasedReasoner(
            rules=(InvalidResultRule(),)
        )

        with self.assertRaises(TypeError):
            reasoner.reason(
                IntelligenceContext(input="test")
            )

    def test_invalid_context_rejected(self):
        reasoner = RuleBasedReasoner()

        with self.assertRaises(TypeError):
            reasoner.reason("invalid")

    def test_cancelled_before_reasoning(self):
        source = CancellationSource()
        source.cancel()

        reasoner = RuleBasedReasoner()

        with self.assertRaises(
            ReasoningCancelledError
        ):
            reasoner.reason(
                IntelligenceContext(input="test"),
                source.token,
            )

    def test_cancellation_between_rules(self):
        source = CancellationSource()

        first = NoMatchRule()

        class CancelRule:

            def evaluate(self, context):
                source.cancel()
                return None

        reasoner = RuleBasedReasoner(
            rules=(
                first,
                CancelRule(),
                NoMatchRule(),
            )
        )

        with self.assertRaises(
            ReasoningCancelledError
        ):
            reasoner.reason(
                IntelligenceContext(input="test"),
                source.token,
            )

    def test_successful_result_returns_before_later_cancellation(self):
        source = CancellationSource()

        class SuccessRule:

            def evaluate(self, context):
                return ReasoningResult(
                    interpretation="success",
                )

        result = RuleBasedReasoner(
            rules=(SuccessRule(),)
        ).reason(
            IntelligenceContext(input="test"),
            source.token,
        )

        self.assertEqual(
            result.interpretation,
            "success",
        )

    def test_reasoning_is_reusable(self):
        rule = MatchingRule(
            ReasoningResult(
                interpretation="stable",
            )
        )

        reasoner = RuleBasedReasoner(
            rules=(rule,)
        )

        first = reasoner.reason(
            IntelligenceContext(input="one")
        )

        second = reasoner.reason(
            IntelligenceContext(input="two")
        )

        self.assertEqual(
            first.interpretation,
            "stable",
        )

        self.assertEqual(
            second.interpretation,
            "stable",
        )

        self.assertEqual(
            rule.calls,
            2,
        )

    def test_reasoner_has_no_runtime_dependency(self):
        reasoner = RuleBasedReasoner()

        self.assertFalse(
            hasattr(reasoner, "runtime")
        )

        self.assertFalse(
            hasattr(reasoner, "scheduler")
        )

        self.assertFalse(
            hasattr(reasoner, "task_executor")
        )

        self.assertFalse(
            hasattr(reasoner, "task_registry")
        )

    def test_reasoner_has_no_execution_api(self):
        reasoner = RuleBasedReasoner()

        self.assertFalse(
            hasattr(reasoner, "execute")
        )

        self.assertFalse(
            hasattr(reasoner, "run")
        )

    def test_reasoner_does_not_create_execution_plan(self):
        result = RuleBasedReasoner(
            rules=(
                MatchingRule(
                    ReasoningResult(
                        interpretation="test",
                    )
                ),
            )
        ).reason(
            IntelligenceContext(input="test")
        )

        self.assertFalse(
            hasattr(result, "execution_plan")
        )

    def test_rule_output_can_contain_candidates(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(
                    goal="generate_report",
                ),
            ),
        )

        reasoner = RuleBasedReasoner(
            rules=(MatchingRule(result),)
        )

        output = reasoner.reason(
            IntelligenceContext(input="report")
        )

        self.assertEqual(
            output.intent_candidates[0].goal,
            "generate_report",
        )

    def test_rule_output_can_contain_ambiguity(self):
        result = ReasoningResult(
            ambiguities=(
                Ambiguity(
                    description="recipient is ambiguous"
                ),
            ),
        )

        output = RuleBasedReasoner(
            rules=(MatchingRule(result),)
        ).reason(
            IntelligenceContext(input="send it")
        )

        self.assertEqual(
            len(output.ambiguities),
            1,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)