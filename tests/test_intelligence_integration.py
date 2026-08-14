import unittest

from ai_os.intelligence import (
    DecisionKind,
    IntelligenceContext,
    IntelligenceOrchestrator,
    ReasoningPipelineStatus,
    IntegratedIntelligence,
    IntentCandidate,
    ReasoningResult,
    RuleBasedDecisionGenerator,
    ReasoningPipeline
)
from ai_os.runtime.cancellation import CancellationSource


class FakeReasoner:

    def __init__(self, result):
        self.result = result
        self.calls = 0

    def reason(self, context, cancellation_token=None):
        self.calls += 1
        return self.result


class MatchingDecisionRule:

    def evaluate(self, intent):
        return DecisionKind.ANSWER


class IntegrationTests(unittest.TestCase):

    def make_reasoner(self, *candidates):
        return FakeReasoner(
            ReasoningResult(
                intent_candidates=tuple(candidates)
            )
        )

    def test_single_candidate_runs_full_pipeline(self):
        reasoner = self.make_reasoner(
            IntentCandidate(
                goal="generate_report",
            )
        )

        from ai_os.intelligence import (
            RuleBasedDecisionGenerator,
        )

        orchestrator = ReasoningPipeline(
            reasoner=reasoner,
            decision_generator=RuleBasedDecisionGenerator(
                rules=(MatchingDecisionRule(),)
            ),
        )

        outcome = orchestrator.run(
            IntelligenceContext(
                input="generate report",
            ),
            intent_id="intent:test",
            decision_id="decision:test",
        )

        self.assertEqual(
            outcome.status,
            ReasoningPipelineStatus.READY,
        )

        self.assertEqual(
            outcome.intent.goal,
            "generate_report",
        )

        self.assertEqual(
            outcome.decision.kind,
            DecisionKind.ANSWER,
        )

    def test_multiple_candidates_stop_before_intent(self):
        reasoner = self.make_reasoner(
            IntentCandidate(goal="sales_report"),
            IntentCandidate(goal="financial_report"),
        )

        orchestrator = ReasoningPipeline(
            reasoner=reasoner,
            decision_generator=RuleBasedDecisionGenerator(
                rules=(MatchingDecisionRule(),)
            ),
        )

        outcome = orchestrator.run(
            IntelligenceContext(input="report"),
            intent_id="intent:test",
            decision_id="decision:test",
        )

        self.assertEqual(
            outcome.status,
            ReasoningPipelineStatus.CLARIFICATION_REQUIRED,
        )

        self.assertIsNone(outcome.intent)
        self.assertIsNone(outcome.decision)

    def test_explicit_candidate_selection_continues(self):
        reasoner = self.make_reasoner(
            IntentCandidate(goal="sales_report"),
            IntentCandidate(goal="financial_report"),
        )

        orchestrator = ReasoningPipeline(
            reasoner=reasoner,
            decision_generator=RuleBasedDecisionGenerator(
                rules=(MatchingDecisionRule(),)
            ),
        )

        outcome = orchestrator.run(
            IntelligenceContext(input="report"),
            intent_id="intent:test",
            decision_id="decision:test",
            candidate_index=1,
        )

        self.assertEqual(
            outcome.status,
            ReasoningPipelineStatus.READY,
        )

        self.assertEqual(
            outcome.intent.goal,
            "financial_report",
        )

    def test_zero_candidates_stop_before_intent(self):
        orchestrator = ReasoningPipeline(
            reasoner=FakeReasoner(
                ReasoningResult()
            ),
            decision_generator=RuleBasedDecisionGenerator(
                rules=(MatchingDecisionRule(),)
            ),
        )

        outcome = orchestrator.run(
            IntelligenceContext(input="unknown"),
            intent_id="intent:test",
            decision_id="decision:test",
        )

        self.assertEqual(
            outcome.status,
            ReasoningPipelineStatus.UNRESOLVED,
        )

        self.assertIsNone(outcome.intent)
        self.assertIsNone(outcome.decision)

    def test_decision_is_not_generated_for_ambiguous_reasoning(self):
        rule = MatchingDecisionRule()

        class TrackingGenerator:

            def __init__(self):
                self.called = False

            def generate(
                self,
                intent,
                decision_id,
                cancellation_token=None,
            ):
                self.called = True
                return None

        generator = TrackingGenerator()

        orchestrator = ReasoningPipeline(
            reasoner=self.make_reasoner(
                IntentCandidate(goal="a"),
                IntentCandidate(goal="b"),
            ),
            decision_generator=generator,
        )

        outcome = orchestrator.run(
            IntelligenceContext(input="ambiguous"),
            intent_id="intent:test",
            decision_id="decision:test",
        )

        self.assertEqual(
            outcome.status,
            ReasoningPipelineStatus.CLARIFICATION_REQUIRED,
        )

        self.assertFalse(
            generator.called
        )

    def test_reasoner_is_called_once(self):
        reasoner = self.make_reasoner(
            IntentCandidate(goal="report"),
        )

        orchestrator = ReasoningPipeline(
            reasoner=reasoner,
            decision_generator=RuleBasedDecisionGenerator(
                rules=(MatchingDecisionRule(),)
            ),
        )

        orchestrator.run(
            IntelligenceContext(input="report"),
            intent_id="intent:test",
            decision_id="decision:test",
        )

        self.assertEqual(
            reasoner.calls,
            1,
        )

    def test_outcome_is_immutable(self):
        orchestrator = ReasoningPipeline(
            reasoner=self.make_reasoner(
                IntentCandidate(goal="report"),
            ),
            decision_generator=RuleBasedDecisionGenerator(
                rules=(MatchingDecisionRule(),)
            ),
        )

        outcome = orchestrator.run(
            IntelligenceContext(input="report"),
            intent_id="intent:test",
            decision_id="decision:test",
        )

        with self.assertRaises(AttributeError):
            outcome.status = ReasoningPipelineStatus.UNRESOLVED

    def test_integrated_intelligence_matches_protocol(self):
        orchestrator = ReasoningPipeline(
            reasoner=self.make_reasoner(
                IntentCandidate(goal="report"),
            ),
            decision_generator=RuleBasedDecisionGenerator(
                rules=(MatchingDecisionRule(),)
            ),
        )

        intelligence = IntegratedIntelligence(
            orchestrator,
        )

        from ai_os.intelligence import Intelligence

        self.assertIsInstance(
            intelligence,
            Intelligence,
        )

    def test_integrated_intelligence_preserves_context(self):
        orchestrator = ReasoningPipeline(
            reasoner=self.make_reasoner(
                IntentCandidate(goal="report"),
            ),
            decision_generator=RuleBasedDecisionGenerator(
                rules=(MatchingDecisionRule(),)
            ),
        )

        result = IntegratedIntelligence(
            orchestrator
        ).decide(
            IntelligenceContext(
                input="report"
            )
        )

        self.assertEqual(
            result.status,
            ReasoningPipelineStatus.READY,
        )

    def test_orchestrator_has_no_runtime_dependency(self):
        orchestrator =ReasoningPipeline(
            reasoner=self.make_reasoner()
        )

        self.assertFalse(
            hasattr(orchestrator, "runtime")
        )

        self.assertFalse(
            hasattr(orchestrator, "scheduler")
        )

        self.assertFalse(
            hasattr(orchestrator, "task_executor")
        )

        self.assertFalse(
            hasattr(orchestrator, "task_registry")
        )

    def test_orchestrator_does_not_execute(self):
        orchestrator = ReasoningPipeline(
            reasoner=self.make_reasoner()
        )

        self.assertFalse(
            hasattr(orchestrator, "execute")
        )

        self.assertFalse(
            hasattr(orchestrator, "run_task")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)