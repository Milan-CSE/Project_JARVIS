from __future__ import annotations

import unittest

from ai_os.intelligence import (
    AgentCommandReceipt,
    AgentFeedbackReceipt,
    AgentIntelligenceBridge,
    ExecutionFeedback,
    FullIntelligenceIntegration,
    FullIntelligenceResult,
    FullIntelligenceStatus,
    IntelligenceContext,
    IntelligenceOrchestrationResult,
    IntelligenceOrchestrationStatus,
    MemoryCandidate,
    MemoryFeedbackPipeline,
    ResponseGenerationPipeline,
    ResultInterpretationPipeline,
)
from ai_os.runtime.agents import (
    AgentDecision,
    AgentDecisionKind,
)
from ai_os.runtime.contracts import (
    ExecutionError,
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
    ExecutionStep,
)


# ======================================================================
# Test doubles
# ======================================================================

class FakeOrchestrator:
    def __init__(
        self,
        result: IntelligenceOrchestrationResult | None = None,
        exception: Exception | None = None,
    ):
        self.result = result
        self.exception = exception
        self.calls = 0
        self.received_contexts = []
        self.received_tokens = []

    def orchestrate(
        self,
        context,
        cancellation_token=None,
    ):
        self.calls += 1
        self.received_contexts.append(context)
        self.received_tokens.append(cancellation_token)

        if self.exception is not None:
            raise self.exception

        return self.result


class TrackingCommandChannel:
    def __init__(self, accepted=True):
        self.accepted = accepted
        self.calls = 0
        self.received_decisions = []

    def send(self, agent_decision):
        self.calls += 1
        self.received_decisions.append(agent_decision)

        return AgentCommandReceipt(
            accepted=self.accepted,
            agent_decision=agent_decision,
        )


class TrackingFeedbackChannel:
    def __init__(self):
        self.calls = 0
        self.received_results = []

    def receive(self, results):
        normalized = tuple(results)

        self.calls += 1
        self.received_results.append(normalized)

        return AgentFeedbackReceipt(
            accepted=True,
            results=normalized,
        )


class TrackingResponseStage:
    def __init__(self, response_pipeline=None):
        self.calls = 0
        self.received_results = []
        self._pipeline = (
            response_pipeline
            if response_pipeline is not None
            else ResponseGenerationPipeline()
        )

    def run(self, result):
        self.calls += 1
        self.received_results.append(result)
        return self._pipeline.run(result)


class TrackingMemoryEvaluator:
    def __init__(self, candidates=()):
        self.candidates = tuple(candidates)
        self.calls = 0
        self.received_sources = []

    def evaluate(self, source):
        self.calls += 1
        self.received_sources.append(source)
        return self.candidates


class WrongResponseStage:
    def run(self, result):
        return "invalid"


class WrongOrchestrator:
    def orchestrate(self, context, cancellation_token=None):
        return "invalid"


class WrongCommandReceiptChannel:
    def send(self, agent_decision):
        return "invalid"


class WrongFeedbackReceiptChannel:
    def receive(self, results):
        return "invalid"


# ======================================================================
# Tests
# ======================================================================

class FullIntelligenceIntegrationTests(unittest.TestCase):

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def create_context(self, value="open vscode"):
        return IntelligenceContext(
            input=value,
        )

    def create_agent_decision(
        self,
        kind=AgentDecisionKind.RESPOND,
    ):
        return AgentDecision(
            kind=kind,
            metadata={
                "source": "test",
            },
        )

    def create_orchestration(
        self,
        status=IntelligenceOrchestrationStatus.COMPLETED,
        context=None,
        agent_decision=None,
    ):
        if context is None:
            context = self.create_context()

        return IntelligenceOrchestrationResult(
            status=status,
            context=context,
            agent_decision=agent_decision,
        )

    def create_step(
        self,
        step_id="step:test",
        capability="test.capability",
    ):
        return ExecutionStep(
            step_id=step_id,
            capability=capability,
        )

    def create_plan(
        self,
        plan_id="plan:test",
        step_id="step:test",
    ):
        return ExecutionPlan(
            plan_id=plan_id,
            steps=(
                self.create_step(
                    step_id=step_id,
                ),
            ),
        )

    def create_result(
        self,
        step_id="step:test",
        status=ExecutionStatus.COMPLETED,
        output=None,
    ):
        error = None

        if status is ExecutionStatus.FAILED:
            error = ExecutionError(
                code="TEST_FAILURE",
                message="test failure",
            )

        return ExecutionResult(
            plan_id="plan:test",
            step_id=step_id,
            status=status,
            output=output,
            error=error,
        )

    def create_bridge(
        self,
        accepted=True,
    ):
        command_channel = TrackingCommandChannel(
            accepted=accepted,
        )

        feedback_channel = TrackingFeedbackChannel()

        bridge = AgentIntelligenceBridge(
            command_channel,
            feedback_channel,
        )

        return (
            bridge,
            command_channel,
            feedback_channel,
        )

    def create_integration(
        self,
        orchestration,
        accepted=True,
        memory_candidates=(),
        response_stage=None,
    ):
        (
            bridge,
            command_channel,
            feedback_channel,
        ) = self.create_bridge(
            accepted=accepted,
        )

        orchestrator = FakeOrchestrator(
            result=orchestration,
        )

        memory_evaluator = TrackingMemoryEvaluator(
            memory_candidates,
        )

        memory_pipeline = MemoryFeedbackPipeline(
            evaluator=memory_evaluator,
        )

        integration = FullIntelligenceIntegration(
            orchestrator=orchestrator,
            agent_bridge=bridge,
            result_interpretation=ResultInterpretationPipeline(),
            memory_feedback=memory_pipeline,
            response_generation=(
                response_stage
                if response_stage is not None
                else ResponseGenerationPipeline()
            ),
        )

        return (
            integration,
            orchestrator,
            command_channel,
            feedback_channel,
            memory_evaluator,
        )

    # ------------------------------------------------------------------
    # Constructor / contract
    # ------------------------------------------------------------------

    def test_valid_orchestrator_is_accepted(self):
        context = self.create_context()
        decision = self.create_agent_decision()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=decision,
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        self.assertIsInstance(
            integration,
            FullIntelligenceIntegration,
        )

    def test_invalid_orchestrator_rejected(self):
        bridge, _, _ = self.create_bridge()

        with self.assertRaises(TypeError):
            FullIntelligenceIntegration(
                orchestrator=object(),
                agent_bridge=bridge,
            )

    def test_invalid_agent_bridge_rejected(self):
        orchestrator = FakeOrchestrator(
            result=self.create_orchestration(),
        )

        with self.assertRaises(TypeError):
            FullIntelligenceIntegration(
                orchestrator=orchestrator,
                agent_bridge=object(),
            )

    def test_invalid_response_stage_rejected(self):
        orchestrator = FakeOrchestrator(
            result=self.create_orchestration(),
        )

        bridge, _, _ = self.create_bridge()

        with self.assertRaises(TypeError):
            FullIntelligenceIntegration(
                orchestrator=orchestrator,
                agent_bridge=bridge,
                response_generation=object(),
            )

    # ------------------------------------------------------------------
    # Normal successful lifecycle
    # ------------------------------------------------------------------

    def test_completed_without_execution_feedback_waits(self):
        context = self.create_context()
        decision = self.create_agent_decision()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=decision,
        )

        (
            integration,
            orchestrator,
            command_channel,
            feedback_channel,
            _,
        ) = self.create_integration(
            orchestration,
        )

        result = integration.run(
            context,
        )

        self.assertIsInstance(
            result,
            FullIntelligenceResult,
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.WAITING_FOR_EXECUTION,
        )

        self.assertIs(
            result.context,
            context,
        )

        self.assertIs(
            result.orchestration,
            orchestration,
        )

        self.assertIsNotNone(
            result.response,
        )

        self.assertIsNotNone(
            result.command,
        )

        self.assertIsNone(
            result.feedback,
        )

        self.assertEqual(
            orchestrator.calls,
            1,
        )

        self.assertEqual(
            command_channel.calls,
            1,
        )

        self.assertEqual(
            feedback_channel.calls,
            0,
        )

    def test_completed_with_execution_feedback_reaches_final_result(self):
        context = self.create_context()
        decision = self.create_agent_decision()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=decision,
        )

        (
            integration,
            _,
            command_channel,
            feedback_channel,
            memory_evaluator,
        ) = self.create_integration(
            orchestration,
        )

        plan = self.create_plan()

        execution_result = self.create_result(
            output={"ok": True},
        )

        feedback = ExecutionFeedback(
            plan=plan,
            results=(execution_result,),
        )

        result = integration.run(
            context,
            execution_feedback=feedback,
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.COMPLETED,
        )

        self.assertIs(
            result.context,
            context,
        )

        self.assertIs(
            result.orchestration,
            orchestration,
        )

        self.assertIs(
            result.command.agent_decision,
            decision,
        )

        self.assertIsNotNone(
            result.feedback,
        )

        self.assertIsNotNone(
            result.interpretation,
        )

        self.assertIsNotNone(
            result.memory_feedback,
        )

        self.assertEqual(
            result.interpretation.interpretation.status.value,
            "completed",
        )

        self.assertEqual(
            result.memory_feedback.candidates,
            (),
        )

        self.assertEqual(
            command_channel.calls,
            1,
        )

        self.assertEqual(
            feedback_channel.calls,
            1,
        )

        self.assertEqual(
            memory_evaluator.calls,
            1,
        )

    # ------------------------------------------------------------------
    # Input normalization
    # ------------------------------------------------------------------

    def test_decide_accepts_raw_input(self):
        context = self.create_context(
            "open vscode",
        )

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            orchestrator,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        result = integration.decide(
            "open vscode",
        )

        self.assertIs(
            orchestrator.received_contexts[0],
            result.context,
        )

        self.assertEqual(
            result.context.input,
            "open vscode",
        )

    def test_decide_preserves_existing_context(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            orchestrator,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        result = integration.decide(
            context,
        )

        self.assertIs(
            orchestrator.received_contexts[0],
            context,
        )

        self.assertIs(
            result.context,
            context,
        )

    # ------------------------------------------------------------------
    # Orchestration terminal states
    # ------------------------------------------------------------------

    def test_blocked_orchestration_stops_before_agent(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            status=IntelligenceOrchestrationStatus.BLOCKED,
            context=context,
        )

        (
            integration,
            _,
            command_channel,
            feedback_channel,
            _,
        ) = self.create_integration(
            orchestration,
        )

        result = integration.run(
            context,
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.BLOCKED,
        )

        self.assertIs(
            result.orchestration,
            orchestration,
        )

        self.assertIsNotNone(
            result.response,
        )

        self.assertIsNone(
            result.command,
        )

        self.assertIsNone(
            result.feedback,
        )

        self.assertEqual(
            command_channel.calls,
            0,
        )

        self.assertEqual(
            feedback_channel.calls,
            0,
        )

    def test_failed_orchestration_stops_before_agent(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            status=IntelligenceOrchestrationStatus.FAILED,
            context=context,
        )

        (
            integration,
            _,
            command_channel,
            feedback_channel,
            _,
        ) = self.create_integration(
            orchestration,
        )

        result = integration.run(
            context,
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.FAILED,
        )

        self.assertIsNone(
            result.command,
        )

        self.assertIsNone(
            result.feedback,
        )

        self.assertEqual(
            command_channel.calls,
            0,
        )

        self.assertEqual(
            feedback_channel.calls,
            0,
        )

    def test_cancelled_orchestration_stops_before_agent(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            status=IntelligenceOrchestrationStatus.CANCELLED,
            context=context,
        )

        (
            integration,
            _,
            command_channel,
            feedback_channel,
            _,
        ) = self.create_integration(
            orchestration,
        )

        result = integration.run(
            context,
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.CANCELLED,
        )

        self.assertIsNone(
            result.command,
        )

        self.assertIsNone(
            result.feedback,
        )

        self.assertEqual(
            command_channel.calls,
            0,
        )

        self.assertEqual(
            feedback_channel.calls,
            0,
        )

    # ------------------------------------------------------------------
    # Missing / invalid AgentDecision
    # ------------------------------------------------------------------

    def test_completed_orchestration_without_agent_decision_fails(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            status=IntelligenceOrchestrationStatus.COMPLETED,
            context=context,
            agent_decision=None,
        )

        (
            integration,
            _,
            command_channel,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        result = integration.run(
            context,
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.FAILED,
        )

        self.assertIsNotNone(
            result.response,
        )

        self.assertIsNone(
            result.command,
        )

        self.assertEqual(
            command_channel.calls,
            0,
        )

    # ------------------------------------------------------------------
    # Agent rejection
    # ------------------------------------------------------------------

    def test_agent_rejection_is_terminal_for_current_run(self):
        context = self.create_context()
        decision = self.create_agent_decision()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=decision,
        )

        (
            integration,
            _,
            command_channel,
            feedback_channel,
            _,
        ) = self.create_integration(
            orchestration,
            accepted=False,
        )

        result = integration.run(
            context,
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.AGENT_REJECTED,
        )

        self.assertIsNotNone(
            result.command,
        )

        self.assertFalse(
            result.command.accepted,
        )

        self.assertEqual(
            command_channel.calls,
            1,
        )

        self.assertEqual(
            feedback_channel.calls,
            0,
        )

    # ------------------------------------------------------------------
    # Execution result scenarios
    # ------------------------------------------------------------------

    def test_failed_execution_becomes_failed(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        feedback = ExecutionFeedback(
            plan=self.create_plan(),
            results=(
                self.create_result(
                    status=ExecutionStatus.FAILED,
                ),
            ),
        )

        result = integration.run(
            context,
            execution_feedback=feedback,
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.FAILED,
        )

        self.assertIsNotNone(
            result.interpretation,
        )

        self.assertTrue(
            result.interpretation
            .interpretation
            .replan_recommended
        )

    def test_cancelled_execution_becomes_cancelled(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        feedback = ExecutionFeedback(
            plan=self.create_plan(),
            results=(
                self.create_result(
                    status=ExecutionStatus.CANCELLED,
                ),
            ),
        )

        result = integration.run(
            context,
            execution_feedback=feedback,
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.CANCELLED,
        )

    def test_pending_execution_becomes_incomplete(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        feedback = ExecutionFeedback(
            plan=self.create_plan(),
            results=(
                self.create_result(
                    status=ExecutionStatus.PENDING,
                ),
            ),
        )

        result = integration.run(
            context,
            execution_feedback=feedback,
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.EXECUTION_INCOMPLETE,
        )

    # ------------------------------------------------------------------
    # Memory feedback
    # ------------------------------------------------------------------

    def test_memory_candidates_are_preserved(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        candidate = MemoryCandidate(
            content="User prefers dark mode",
            category="user_preference",
            confidence=0.95,
        )

        (
            integration,
            _,
            _,
            _,
            memory_evaluator,
        ) = self.create_integration(
            orchestration,
            memory_candidates=(candidate,),
        )

        feedback = ExecutionFeedback(
            plan=self.create_plan(),
            results=(
                self.create_result(
                    output={"ok": True},
                ),
            ),
        )

        result = integration.run(
            context,
            execution_feedback=feedback,
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.COMPLETED,
        )

        self.assertEqual(
            result.memory_feedback.candidates,
            (candidate,),
        )

        self.assertEqual(
            memory_evaluator.calls,
            1,
        )

    # ------------------------------------------------------------------
    # Exact object preservation
    # ------------------------------------------------------------------

    def test_exact_orchestration_result_preserved(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        result = integration.run(
            context,
        )

        self.assertIs(
            result.orchestration,
            orchestration,
        )

    def test_exact_context_preserved(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        result = integration.run(
            context,
        )

        self.assertIs(
            result.context,
            context,
        )

    def test_exact_agent_decision_preserved(self):
        context = self.create_context()
        decision = self.create_agent_decision()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=decision,
        )

        (
            integration,
            _,
            command_channel,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        result = integration.run(
            context,
        )

        self.assertIs(
            command_channel.received_decisions[0],
            decision,
        )

        self.assertIs(
            result.command.agent_decision,
            decision,
        )

    # ------------------------------------------------------------------
    # Custom response stage
    # ------------------------------------------------------------------

    def test_custom_response_stage_is_called_once(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        response_stage = TrackingResponseStage()

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
            response_stage=response_stage,
        )

        integration.run(
            context,
        )

        self.assertEqual(
            response_stage.calls,
            1,
        )

        self.assertIs(
            response_stage.received_results[0],
            orchestration,
        )

    # ------------------------------------------------------------------
    # Validation of feedback boundary
    # ------------------------------------------------------------------

    def test_invalid_execution_feedback_rejected(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        with self.assertRaises(TypeError):
            integration.run(
                context,
                execution_feedback=object(),
            )

    def test_invalid_execution_result_rejected_at_feedback_boundary(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        with self.assertRaises(TypeError):
            ExecutionFeedback(
                plan=self.create_plan(),
                results=("invalid",),
            )

    # ------------------------------------------------------------------
    # No direct execution / replan / persistence APIs
    # ------------------------------------------------------------------

    def test_integration_has_no_execute_api(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        self.assertFalse(
            hasattr(
                integration,
                "execute",
            )
        )

        self.assertFalse(
            hasattr(
                integration,
                "execute_plan",
            )
        )

    def test_integration_has_no_runtime_executor(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        self.assertFalse(
            hasattr(
                integration,
                "runtime_executor",
            )
        )

        self.assertFalse(
            hasattr(
                integration,
                "executor",
            )
        )

    def test_integration_has_no_workflow_runner(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        self.assertFalse(
            hasattr(
                integration,
                "workflow_runner",
            )
        )

        self.assertFalse(
            hasattr(
                integration,
                "runner",
            )
        )

    def test_integration_has_no_replan_api(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        self.assertFalse(
            hasattr(
                integration,
                "replan",
            )
        )

    def test_integration_has_no_memory_persistence_api(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        self.assertFalse(
            hasattr(
                integration,
                "persist_memory",
            )
        )

        self.assertFalse(
            hasattr(
                integration,
                "store_memory",
            )
        )

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------

    def test_full_result_is_immutable(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        result = integration.run(
            context,
        )

        with self.assertRaises(AttributeError):
            result.status = FullIntelligenceStatus.FAILED

    def test_full_result_metadata_is_immutable(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        result = FullIntelligenceResult(
            status=FullIntelligenceStatus.WAITING_FOR_EXECUTION,
            context=context,
            orchestration=orchestration,
            metadata={
                "stage": "test",
            },
        )

        with self.assertRaises(TypeError):
            result.metadata["changed"] = True

    def test_execution_feedback_is_immutable(self):
        feedback = ExecutionFeedback(
            plan=self.create_plan(),
            results=(
                self.create_result(),
            ),
        )

        with self.assertRaises(AttributeError):
            feedback.plan = None

    # ------------------------------------------------------------------
    # Stateless / repeatability
    # ------------------------------------------------------------------

    def test_integration_is_reusable(self):
        first_context = self.create_context(
            "first",
        )

        second_context = self.create_context(
            "second",
        )

        first_orchestration = self.create_orchestration(
            context=first_context,
            agent_decision=self.create_agent_decision(),
        )

        second_orchestration = self.create_orchestration(
            context=second_context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            orchestrator,
            _,
            _,
            _,
        ) = self.create_integration(
            first_orchestration,
        )

        first = integration.run(
            first_context,
        )

        # Replace only the fake's output for the second independent run.
        orchestrator.result = second_orchestration

        second = integration.run(
            second_context,
        )

        self.assertIs(
            first.context,
            first_context,
        )

        self.assertIs(
            second.context,
            second_context,
        )

        self.assertIs(
            first.orchestration,
            first_orchestration,
        )

        self.assertIs(
            second.orchestration,
            second_orchestration,
        )

        self.assertEqual(
            orchestrator.calls,
            2,
        )

    def test_orchestrator_called_once_per_run(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            orchestrator,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        integration.run(context)

        self.assertEqual(
            orchestrator.calls,
            1,
        )

    # ------------------------------------------------------------------
    # Wrong downstream return types
    # ------------------------------------------------------------------

    def test_invalid_response_stage_output_fails(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
            response_stage=WrongResponseStage(),
        )

        result = integration.run(
            context,
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.FAILED,
        )

    def test_invalid_orchestrator_output_fails(self):
        bridge, _, _ = self.create_bridge()

        integration = FullIntelligenceIntegration(
            orchestrator=WrongOrchestrator(),
            agent_bridge=bridge,
        )

        result = integration.run(
            self.create_context(),
        )

        self.assertEqual(
            result.status,
            FullIntelligenceStatus.FAILED,
        )

    # ------------------------------------------------------------------
    # Result type
    # ------------------------------------------------------------------

    def test_final_result_type(self):
        context = self.create_context()

        orchestration = self.create_orchestration(
            context=context,
            agent_decision=self.create_agent_decision(),
        )

        (
            integration,
            _,
            _,
            _,
            _,
        ) = self.create_integration(
            orchestration,
        )

        result = integration.run(
            context,
        )

        self.assertIsInstance(
            result,
            FullIntelligenceResult,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)