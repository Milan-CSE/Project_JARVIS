from __future__ import annotations

import unittest

from ai_os.intelligence import (
    AgentDecisionHandoffPipeline,
    DefaultIntelligenceOrchestrator,
    DecisionAdapter,
    DecisionProposalPipeline,
    DecisionProposalResult,
    DecisionProposalStatus,
    IntelligenceContext,
    IntelligenceOrchestrationResult,
    IntelligenceOrchestrationStatus,
    IntelligenceOrchestrator,
    IntentDecisionResult,
    IntentDecisionStatus,
    ReasoningIntentResult,
    ReasoningIntentStatus,
    SemanticValidationPipeline,
    SemanticValidator,
)
from ai_os.intelligence.decision import (
    Decision,
    DecisionKind,
    ProposalKind,
    WorkflowProposal,
)
from ai_os.intelligence.intent import Intent
from ai_os.intelligence.reasoning import ReasoningResult
from ai_os.runtime.cancellation import CancellationSource


class FakeReasoningIntentStage:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def run(
        self,
        context,
        intent_id,
        candidate_index=None,
        cancellation_token=None,
    ):
        self.calls += 1
        return self.result


class FakeIntentDecisionStage:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def run(
        self,
        intent,
        decision_id,
        cancellation_token=None,
    ):
        self.calls += 1
        return self.result


class FakeDecisionProposalStage:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def run(self, decision, proposal_id):
        self.calls += 1
        return self.result


class FakeValidationStage:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def run(self, intent, decision, proposal):
        self.calls += 1
        return self.result


class FakeHandoffStage:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def run(self, validated):
        self.calls += 1
        return self.result


class IntelligenceEndToEndTests(unittest.TestCase):

    def create_context(self):
        return IntelligenceContext(
            input="generate my report"
        )

    def create_intent(self):
        return Intent(
            intent_id="intent:test",
            goal="generate_report",
        )

    def create_decision(self):
        return Decision(
            decision_id="decision:test",
            intent_id="intent:test",
            kind=DecisionKind.ANSWER,
        )

    def test_concrete_orchestrator_matches_protocol(self):
        orchestrator = self.make_orchestrator()

        self.assertIsInstance(
            orchestrator,
            IntelligenceOrchestrator,
        )

    def make_orchestrator(self):
        context = self.create_context()
        intent = self.create_intent()
        decision = self.create_decision()

        reasoning_result = ReasoningIntentResult(
            status=ReasoningIntentStatus.RESOLVED,
            context=context,
            reasoning=ReasoningResult(),
            resolution=MagicResolution.ready(),
            intent=intent,
        )

        decision_result = IntentDecisionResult(
            status=IntentDecisionStatus.RESOLVED,
            intent=intent,
            decision=decision,
        )

        proposal_result = DecisionProposalResult(
            status=DecisionProposalStatus.NO_PROPOSAL_REQUIRED,
            decision=decision,
        )

        validation = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            intent,
            decision,
            None,
        )

        handoff = AgentDecisionHandoffPipeline(
            DecisionAdapter()
        ).run(validation)

        return DefaultIntelligenceOrchestrator(
            FakeReasoningIntentStage(
                reasoning_result
            ),
            FakeIntentDecisionStage(
                decision_result
            ),
            FakeDecisionProposalStage(
                proposal_result
            ),
            FakeValidationStage(
                validation
            ),
            FakeHandoffStage(
                handoff
            ),
            intent_id="intent:test",
            decision_id="decision:test",
            proposal_id="proposal:test",
        )

    def test_result_is_orchestration_result(self):
        result = self.make_orchestrator().orchestrate(
            self.create_context()
        )

        self.assertIsInstance(
            result,
            IntelligenceOrchestrationResult,
        )

    def test_full_pipeline_completes(self):
        result = self.make_orchestrator().orchestrate(
            self.create_context()
        )

        self.assertEqual(
            result.status,
            IntelligenceOrchestrationStatus.COMPLETED,
        )

        self.assertIsNotNone(
            result.intent
        )

        self.assertIsNotNone(
            result.decision
        )

        self.assertIsNotNone(
            result.agent_decision
        )

    def test_context_is_preserved(self):
        context = self.create_context()

        result = self.make_orchestrator().orchestrate(
            context
        )

        self.assertIs(
            result.context,
            context,
        )

    def test_zero_intent_blocks_pipeline(self):
        context = self.create_context()

        result = ReasoningIntentResult(
            status=ReasoningIntentStatus.UNRESOLVED,
            context=context,
            reasoning=ReasoningResult(),
            resolution=MagicResolution.unresolved(),
        )

        reasoner = FakeReasoningIntentStage(result)
        decision = FakeIntentDecisionStage(None)
        proposal = FakeDecisionProposalStage(None)
        validation = FakeValidationStage(None)
        handoff = FakeHandoffStage(None)

        orchestrator = DefaultIntelligenceOrchestrator(
            reasoner,
            decision,
            proposal,
            validation,
            handoff,
            intent_id="intent:test",
            decision_id="decision:test",
            proposal_id="proposal:test",
        )

        output = orchestrator.orchestrate(context)

        self.assertEqual(
            output.status,
            IntelligenceOrchestrationStatus.BLOCKED,
        )

        self.assertIsNone(output.intent)
        self.assertIsNone(output.decision)
        self.assertEqual(decision.calls, 0)
        self.assertEqual(proposal.calls, 0)
        self.assertEqual(validation.calls, 0)
        self.assertEqual(handoff.calls, 0)

    def test_ambiguous_reasoning_blocks_pipeline(self):
        context = self.create_context()

        result = ReasoningIntentResult(
            status=ReasoningIntentStatus.AMBIGUOUS,
            context=context,
            reasoning=ReasoningResult(),
            resolution=MagicResolution.clarification(),
        )

        reasoner = FakeReasoningIntentStage(result)
        decision = FakeIntentDecisionStage(None)
        proposal = FakeDecisionProposalStage(None)
        validation = FakeValidationStage(None)
        handoff = FakeHandoffStage(None)

        orchestrator = DefaultIntelligenceOrchestrator(
            reasoner,
            decision,
            proposal,
            validation,
            handoff,
            intent_id="intent:test",
            decision_id="decision:test",
            proposal_id="proposal:test",
        )

        output = orchestrator.orchestrate(context)

        self.assertEqual(
            output.status,
            IntelligenceOrchestrationStatus.BLOCKED,
        )

        self.assertEqual(
            decision.calls,
            0,
        )

    def test_semantic_rejection_blocks_before_handoff(self):
        context = self.create_context()
        intent = self.create_intent()
        decision = self.create_decision()

        reasoning = self.make_orchestrator()._reasoning_intent.result

        intent_stage = FakeReasoningIntentStage(
            reasoning
        )

        decision_stage = FakeIntentDecisionStage(
            IntentDecisionResult(
                status=IntentDecisionStatus.RESOLVED,
                intent=intent,
                decision=decision,
            )
        )

        proposal_stage = FakeDecisionProposalStage(
            DecisionProposalResult(
                status=DecisionProposalStatus.NO_PROPOSAL_REQUIRED,
                decision=decision,
            )
        )

        rejected = SemanticValidationPipeline(
            SemanticValidator()
        ).run(
            intent,
            Decision(
                decision_id="decision:test",
                intent_id="wrong:intent",
                kind=DecisionKind.ANSWER,
            ),
            None,
        )

        validation_stage = FakeValidationStage(
            rejected
        )

        handoff = FakeHandoffStage(None)

        orchestrator = DefaultIntelligenceOrchestrator(
            intent_stage,
            decision_stage,
            proposal_stage,
            validation_stage,
            handoff,
            intent_id="intent:test",
            decision_id="decision:test",
            proposal_id="proposal:test",
        )

        output = orchestrator.orchestrate(context)

        self.assertEqual(
            output.status,
            IntelligenceOrchestrationStatus.BLOCKED,
        )

        self.assertEqual(
            handoff.calls,
            0,
        )

    def test_each_stage_called_once(self):
        orchestrator = self.make_orchestrator()

        result = orchestrator.orchestrate(
            self.create_context()
        )

        self.assertEqual(
            result.status,
            IntelligenceOrchestrationStatus.COMPLETED,
        )

        self.assertEqual(
            orchestrator._reasoning_intent.calls,
            1,
        )

        self.assertEqual(
            orchestrator._intent_decision.calls,
            1,
        )

        self.assertEqual(
            orchestrator._decision_proposal.calls,
            1,
        )

        self.assertEqual(
            orchestrator._semantic_validation.calls,
            1,
        )

        self.assertEqual(
            orchestrator._agent_handoff.calls,
            1,
        )

    def test_no_execution_api(self):
        orchestrator = self.make_orchestrator()

        self.assertFalse(
            hasattr(orchestrator, "execute")
        )

        self.assertFalse(
            hasattr(orchestrator, "run_task")
        )

    def test_no_runtime_dependency(self):
        orchestrator = self.make_orchestrator()

        self.assertFalse(
            hasattr(orchestrator, "runtime")
        )

        self.assertFalse(
            hasattr(orchestrator, "scheduler")
        )

        self.assertFalse(
            hasattr(orchestrator, "task_executor")
        )

    def test_result_is_immutable(self):
        result = self.make_orchestrator().orchestrate(
            self.create_context()
        )

        with self.assertRaises(AttributeError):
            result.status = IntelligenceOrchestrationStatus.FAILED


# ----------------------------------------------------------------------
# Minimal helpers used by the test.
# ----------------------------------------------------------------------

class MagicResolution:

    @staticmethod
    def ready():
        from ai_os.intelligence.reasoning import (
            ReasoningResolution,
            ReasoningResolutionStatus,
        )

        return ReasoningResolution(
            status=ReasoningResolutionStatus.READY,
            candidate_index=0,
        )

    @staticmethod
    def unresolved():
        from ai_os.intelligence.reasoning import (
            ReasoningResolution,
            ReasoningResolutionStatus,
        )

        return ReasoningResolution(
            status=ReasoningResolutionStatus.UNRESOLVED,
        )

    @staticmethod
    def clarification():
        from ai_os.intelligence.reasoning import (
            ReasoningResolution,
            ReasoningResolutionStatus,
        )

        return ReasoningResolution(
            status=(
                ReasoningResolutionStatus
                .CLARIFICATION_REQUIRED
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)