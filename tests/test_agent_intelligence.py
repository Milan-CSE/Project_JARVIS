from __future__ import annotations

import unittest

from ai_os.intelligence import (
    AgentCommandChannel,
    AgentCommandReceipt,
    AgentFeedbackChannel,
    AgentFeedbackReceipt,
    AgentIntelligenceBridge,
    AgentIntelligenceInteraction,
)
from ai_os.runtime.agents import (
    AgentDecision,
    AgentDecisionKind,
)
from ai_os.runtime.contracts import (
    ExecutionError,
    ExecutionResult,
    ExecutionStatus,
    ExecutionStep,
    ExecutionPlan,
)


class TrackingCommandChannel:
    def __init__(self, receipt_factory=None):
        self.calls = 0
        self.received_decisions = []
        self.receipt_factory = receipt_factory

    def send(self, agent_decision):
        self.calls += 1
        self.received_decisions.append(agent_decision)

        if self.receipt_factory is not None:
            return self.receipt_factory(agent_decision)

        return AgentCommandReceipt(
            accepted=True,
            agent_decision=agent_decision,
        )


class TrackingFeedbackChannel:
    def __init__(self, receipt_factory=None):
        self.calls = 0
        self.received_results = []
        self.receipt_factory = receipt_factory

    def receive(self, results):
        results = tuple(results)

        self.calls += 1
        self.received_results.append(results)

        if self.receipt_factory is not None:
            return self.receipt_factory(results)

        return AgentFeedbackReceipt(
            accepted=True,
            results=results,
        )


class WrongCommandChannel:
    def send(self, agent_decision):
        return "invalid"


class WrongFeedbackChannel:
    def receive(self, results):
        return "invalid"


class MissingSend:
    pass


class MissingReceive:
    pass


class RaisingCommandChannel:
    def send(self, agent_decision):
        raise RuntimeError("command channel failed")


class RaisingFeedbackChannel:
    def receive(self, results):
        raise RuntimeError("feedback channel failed")


class WrongDecisionReceiptChannel:
    def send(self, agent_decision):
        other = AgentDecision(
            kind=AgentDecisionKind.RESPOND,
        )

        return AgentCommandReceipt(
            accepted=True,
            agent_decision=other,
        )


class WrongResultsReceiptChannel:
    def receive(self, results):
        return AgentFeedbackReceipt(
            accepted=True,
            results=(),
        )


class AgentIntelligenceTests(unittest.TestCase):

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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

    def create_step(
        self,
        step_id="step:test",
        capability="test.capability",
    ):
        return ExecutionStep(
            step_id=step_id,
            capability=capability,
        )

    def create_plan(self):
        return ExecutionPlan(
            plan_id="plan:test",
            steps=(
                self.create_step(),
            ),
        )

    def create_result(
        self,
        step_id="step:test",
        status=ExecutionStatus.COMPLETED,
        output=None,
        error=None,
    ):
        if (
            status is ExecutionStatus.FAILED
            and error is None
        ):
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

    # ------------------------------------------------------------------
    # Structural contracts
    # ------------------------------------------------------------------

    def test_valid_command_channel_matches_contract(self):
        channel = TrackingCommandChannel()

        self.assertIsInstance(
            channel,
            AgentCommandChannel,
        )

    def test_valid_feedback_channel_matches_contract(self):
        channel = TrackingFeedbackChannel()

        self.assertIsInstance(
            channel,
            AgentFeedbackChannel,
        )

    def test_invalid_command_channel_does_not_match_contract(self):
        self.assertFalse(
            isinstance(
                MissingSend(),
                AgentCommandChannel,
            )
        )

    def test_invalid_feedback_channel_does_not_match_contract(self):
        self.assertFalse(
            isinstance(
                MissingReceive(),
                AgentFeedbackChannel,
            )
        )

    def test_invalid_command_channel_rejected(self):
        with self.assertRaises(TypeError):
            AgentIntelligenceBridge(
                object(),
                TrackingFeedbackChannel(),
            )

    def test_invalid_feedback_channel_rejected(self):
        with self.assertRaises(TypeError):
            AgentIntelligenceBridge(
                TrackingCommandChannel(),
                object(),
            )

    # ------------------------------------------------------------------
    # Intelligence → Agent
    # ------------------------------------------------------------------

    def test_send_accepts_agent_decision(self):
        command_channel = TrackingCommandChannel()

        bridge = AgentIntelligenceBridge(
            command_channel,
            TrackingFeedbackChannel(),
        )

        decision = self.create_agent_decision()

        receipt = bridge.send(decision)

        self.assertIsInstance(
            receipt,
            AgentCommandReceipt,
        )

        self.assertTrue(
            receipt.accepted
        )

    def test_command_channel_called_once(self):
        command_channel = TrackingCommandChannel()

        bridge = AgentIntelligenceBridge(
            command_channel,
            TrackingFeedbackChannel(),
        )

        decision = self.create_agent_decision()

        bridge.send(decision)

        self.assertEqual(
            command_channel.calls,
            1,
        )

    def test_exact_agent_decision_is_forwarded(self):
        command_channel = TrackingCommandChannel()

        bridge = AgentIntelligenceBridge(
            command_channel,
            TrackingFeedbackChannel(),
        )

        decision = self.create_agent_decision()

        bridge.send(decision)

        self.assertIs(
            command_channel.received_decisions[0],
            decision,
        )

    def test_command_receipt_preserves_exact_decision(self):
        decision = self.create_agent_decision()

        receipt = AgentCommandReceipt(
            accepted=True,
            agent_decision=decision,
        )

        self.assertIs(
            receipt.agent_decision,
            decision,
        )

    def test_invalid_agent_decision_rejected(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        with self.assertRaises(TypeError):
            bridge.send(object())

    def test_wrong_command_channel_result_rejected(self):
        bridge = AgentIntelligenceBridge(
            WrongCommandChannel(),
            TrackingFeedbackChannel(),
        )

        with self.assertRaises(TypeError):
            bridge.send(
                self.create_agent_decision()
            )

    def test_command_channel_exception_propagates(self):
        bridge = AgentIntelligenceBridge(
            RaisingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        with self.assertRaises(RuntimeError):
            bridge.send(
                self.create_agent_decision()
            )

    def test_command_receipt_with_wrong_decision_rejected(self):
        bridge = AgentIntelligenceBridge(
            WrongDecisionReceiptChannel(),
            TrackingFeedbackChannel(),
        )

        with self.assertRaises(ValueError):
            bridge.send(
                self.create_agent_decision()
            )

    # ------------------------------------------------------------------
    # Agent → Intelligence
    # ------------------------------------------------------------------

    def test_receive_accepts_execution_results(self):
        feedback_channel = TrackingFeedbackChannel()

        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            feedback_channel,
        )

        result = self.create_result(
            output={"ok": True},
        )

        receipt = bridge.receive(
            (result,),
        )

        self.assertIsInstance(
            receipt,
            AgentFeedbackReceipt,
        )

        self.assertTrue(
            receipt.accepted
        )

    def test_feedback_channel_called_once(self):
        feedback_channel = TrackingFeedbackChannel()

        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            feedback_channel,
        )

        result = self.create_result()

        bridge.receive(
            (result,),
        )

        self.assertEqual(
            feedback_channel.calls,
            1,
        )

    def test_exact_feedback_results_are_forwarded(self):
        feedback_channel = TrackingFeedbackChannel()

        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            feedback_channel,
        )

        first = self.create_result(
            output={"value": 1},
        )

        second = self.create_result(
            output={"value": 2},
        )

        feedback = (
            first,
            second,
        )

        bridge.receive(feedback)

        self.assertEqual(
            feedback_channel.received_results[0],
            feedback,
        )

        self.assertIs(
            feedback_channel.received_results[0][0],
            first,
        )

        self.assertIs(
            feedback_channel.received_results[0][1],
            second,
        )

    def test_empty_feedback_is_allowed(self):
        feedback_channel = TrackingFeedbackChannel()

        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            feedback_channel,
        )

        receipt = bridge.receive(())

        self.assertTrue(
            receipt.accepted
        )

        self.assertEqual(
            receipt.results,
            (),
        )

    def test_invalid_feedback_type_rejected(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        with self.assertRaises(TypeError):
            bridge.receive(
                ("invalid",),
            )

    def test_string_feedback_rejected(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        with self.assertRaises(TypeError):
            bridge.receive("invalid")

    def test_wrong_feedback_channel_result_rejected(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            WrongFeedbackChannel(),
        )

        with self.assertRaises(TypeError):
            bridge.receive(
                (
                    self.create_result(),
                ),
            )

    def test_feedback_channel_exception_propagates(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            RaisingFeedbackChannel(),
        )

        with self.assertRaises(RuntimeError):
            bridge.receive(
                (
                    self.create_result(),
                ),
            )

    def test_feedback_receipt_with_wrong_results_rejected(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            WrongResultsReceiptChannel(),
        )

        with self.assertRaises(ValueError):
            bridge.receive(
                (
                    self.create_result(),
                ),
            )

    # ------------------------------------------------------------------
    # Exchange
    # ------------------------------------------------------------------

    def test_exchange_can_send_only(self):
        command_channel = TrackingCommandChannel()
        feedback_channel = TrackingFeedbackChannel()

        bridge = AgentIntelligenceBridge(
            command_channel,
            feedback_channel,
        )

        decision = self.create_agent_decision()

        interaction = bridge.exchange(
            decision,
        )

        self.assertIsInstance(
            interaction,
            AgentIntelligenceInteraction,
        )

        self.assertIsNone(
            interaction.feedback
        )

        self.assertIs(
            interaction.command.agent_decision,
            decision,
        )

    def test_exchange_can_send_and_receive_feedback(self):
        command_channel = TrackingCommandChannel()
        feedback_channel = TrackingFeedbackChannel()

        bridge = AgentIntelligenceBridge(
            command_channel,
            feedback_channel,
        )

        decision = self.create_agent_decision()

        result = self.create_result(
            output={"ok": True},
        )

        interaction = bridge.exchange(
            decision,
            (result,),
        )

        self.assertIsInstance(
            interaction,
            AgentIntelligenceInteraction,
        )

        self.assertIsNotNone(
            interaction.feedback
        )

        self.assertIs(
            interaction.command.agent_decision,
            decision,
        )

        self.assertEqual(
            interaction.feedback.results,
            (result,),
        )

    def test_exchange_calls_each_channel_once(self):
        command_channel = TrackingCommandChannel()
        feedback_channel = TrackingFeedbackChannel()

        bridge = AgentIntelligenceBridge(
            command_channel,
            feedback_channel,
        )

        bridge.exchange(
            self.create_agent_decision(),
            (
                self.create_result(),
            ),
        )

        self.assertEqual(
            command_channel.calls,
            1,
        )

        self.assertEqual(
            feedback_channel.calls,
            1,
        )

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------

    def test_command_receipt_is_immutable(self):
        receipt = AgentCommandReceipt(
            accepted=True,
            agent_decision=self.create_agent_decision(),
        )

        with self.assertRaises(AttributeError):
            receipt.accepted = False

    def test_feedback_receipt_is_immutable(self):
        receipt = AgentFeedbackReceipt(
            accepted=True,
            results=(
                self.create_result(),
            ),
        )

        with self.assertRaises(AttributeError):
            receipt.accepted = False

    def test_interaction_is_immutable(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        interaction = bridge.exchange(
            self.create_agent_decision(),
        )

        with self.assertRaises(AttributeError):
            interaction.command = None

    def test_command_metadata_is_immutable(self):
        receipt = AgentCommandReceipt(
            accepted=True,
            agent_decision=self.create_agent_decision(),
            metadata={
                "source": "test",
            },
        )

        with self.assertRaises(TypeError):
            receipt.metadata["source"] = "changed"

    def test_feedback_metadata_is_immutable(self):
        receipt = AgentFeedbackReceipt(
            accepted=True,
            results=(),
            metadata={
                "source": "test",
            },
        )

        with self.assertRaises(TypeError):
            receipt.metadata["source"] = "changed"

    def test_interaction_metadata_is_immutable(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        interaction = bridge.exchange(
            self.create_agent_decision(),
        )

        with self.assertRaises(TypeError):
            interaction.metadata["x"] = 1

    # ------------------------------------------------------------------
    # No execution / scheduling / replanning / memory
    # ------------------------------------------------------------------

    def test_bridge_has_no_execute_method(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        self.assertFalse(
            hasattr(
                bridge,
                "execute",
            )
        )

        self.assertFalse(
            hasattr(
                bridge,
                "execute_plan",
            )
        )

    def test_bridge_has_no_schedule_method(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        self.assertFalse(
            hasattr(
                bridge,
                "schedule",
            )
        )

        self.assertFalse(
            hasattr(
                bridge,
                "scheduler",
            )
        )

    def test_bridge_has_no_workflow_runner(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        self.assertFalse(
            hasattr(
                bridge,
                "workflow_runner",
            )
        )

        self.assertFalse(
            hasattr(
                bridge,
                "runner",
            )
        )

    def test_bridge_has_no_runtime_executor(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        self.assertFalse(
            hasattr(
                bridge,
                "runtime_executor",
            )
        )

        self.assertFalse(
            hasattr(
                bridge,
                "executor",
            )
        )

    def test_bridge_has_no_replan_method(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        self.assertFalse(
            hasattr(
                bridge,
                "replan",
            )
        )

    def test_bridge_has_no_memory_method(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        self.assertFalse(
            hasattr(
                bridge,
                "store_memory",
            )
        )

        self.assertFalse(
            hasattr(
                bridge,
                "persist_memory",
            )
        )

    def test_bridge_has_no_interpret_method(self):
        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        self.assertFalse(
            hasattr(
                bridge,
                "interpret",
            )
        )

    # ------------------------------------------------------------------
    # No mutation
    # ------------------------------------------------------------------

    def test_agent_decision_is_not_mutated(self):
        decision = self.create_agent_decision()

        original_kind = decision.kind
        original_metadata = decision.metadata

        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        bridge.send(decision)

        self.assertEqual(
            decision.kind,
            original_kind,
        )

        self.assertEqual(
            decision.metadata,
            original_metadata,
        )

    def test_execution_results_are_not_mutated(self):
        result = self.create_result(
            output={
                "value": 42,
            },
        )

        original_status = result.status
        original_output = result.output

        bridge = AgentIntelligenceBridge(
            TrackingCommandChannel(),
            TrackingFeedbackChannel(),
        )

        bridge.receive(
            (result,),
        )

        self.assertEqual(
            result.status,
            original_status,
        )

        self.assertEqual(
            result.output,
            original_output,
        )

    # ------------------------------------------------------------------
    # Reusability / statelessness
    # ------------------------------------------------------------------

    def test_bridge_is_reusable(self):
        command_channel = TrackingCommandChannel()
        feedback_channel = TrackingFeedbackChannel()

        bridge = AgentIntelligenceBridge(
            command_channel,
            feedback_channel,
        )

        first_decision = self.create_agent_decision(
            AgentDecisionKind.RESPOND,
        )

        second_decision = self.create_agent_decision(
            AgentDecisionKind.DECLINE,
        )

        first_result = self.create_result(
            output={"run": 1},
        )

        second_result = self.create_result(
            output={"run": 2},
        )

        first = bridge.exchange(
            first_decision,
            (first_result,),
        )

        second = bridge.exchange(
            second_decision,
            (second_result,),
        )

        self.assertIs(
            first.command.agent_decision,
            first_decision,
        )

        self.assertIs(
            second.command.agent_decision,
            second_decision,
        )

        self.assertEqual(
            first.feedback.results,
            (first_result,),
        )

        self.assertEqual(
            second.feedback.results,
            (second_result,),
        )

    def test_no_cross_run_state(self):
        command_channel = TrackingCommandChannel()
        feedback_channel = TrackingFeedbackChannel()

        bridge = AgentIntelligenceBridge(
            command_channel,
            feedback_channel,
        )

        bridge.exchange(
            self.create_agent_decision(),
            (
                self.create_result(
                    output={"run": 1},
                ),
            ),
        )

        bridge.exchange(
            self.create_agent_decision(),
            (
                self.create_result(
                    output={"run": 2},
                ),
            ),
        )

        self.assertEqual(
            len(
                command_channel.received_decisions
            ),
            2,
        )

        self.assertEqual(
            len(
                feedback_channel.received_results
            ),
            2,
        )

        self.assertEqual(
            feedback_channel.received_results[0][0].output,
            {"run": 1},
        )

        self.assertEqual(
            feedback_channel.received_results[1][0].output,
            {"run": 2},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)