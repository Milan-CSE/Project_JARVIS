from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field as dataclass_field
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from ai_os.runtime.agents import AgentDecision
from ai_os.runtime.contracts import ExecutionResult


@dataclass(frozen=True, slots=True)
class AgentCommandReceipt:
    """Immutable acknowledgement of Intelligence → Agent handoff."""

    accepted: bool
    agent_decision: AgentDecision
    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.accepted,
            bool,
        ):
            raise TypeError(
                "accepted must be a bool"
            )

        if not isinstance(
            self.agent_decision,
            AgentDecision,
        ):
            raise TypeError(
                "agent_decision must be an AgentDecision"
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


@dataclass(frozen=True, slots=True)
class AgentFeedbackReceipt:
    """Immutable acknowledgement of Agent → Intelligence feedback."""

    accepted: bool
    results: tuple[ExecutionResult, ...]
    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.accepted,
            bool,
        ):
            raise TypeError(
                "accepted must be a bool"
            )

        if not isinstance(
            self.results,
            tuple,
        ):
            object.__setattr__(
                self,
                "results",
                tuple(self.results),
            )

        if not all(
            isinstance(
                result,
                ExecutionResult,
            )
            for result in self.results
        ):
            raise TypeError(
                "results must contain only "
                "ExecutionResult instances"
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


@runtime_checkable
class AgentCommandChannel(Protocol):
    """Published contract for Intelligence → Agent communication."""

    def send(
        self,
        agent_decision: AgentDecision,
    ) -> AgentCommandReceipt:
        ...


@runtime_checkable
class AgentFeedbackChannel(Protocol):
    """Published contract for Agent → Intelligence feedback."""

    def receive(
        self,
        results: Iterable[ExecutionResult],
    ) -> AgentFeedbackReceipt:
        ...


@dataclass(frozen=True, slots=True)
class AgentIntelligenceInteraction:
    """
    Immutable record of one cross-boundary interaction.

    This is a transport/integration record only.
    """

    command: AgentCommandReceipt
    feedback: AgentFeedbackReceipt | None = None
    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.command,
            AgentCommandReceipt,
        ):
            raise TypeError(
                "command must be an AgentCommandReceipt"
            )

        if self.feedback is not None and not isinstance(
            self.feedback,
            AgentFeedbackReceipt,
        ):
            raise TypeError(
                "feedback must be an AgentFeedbackReceipt "
                "or None"
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


class AgentIntelligenceBridge:
    """
    9.11 Agent ↔ Intelligence integration boundary.

    Intelligence → Agent:
        AgentDecision -> AgentCommandChannel

    Agent → Intelligence:
        ExecutionResult(s) -> AgentFeedbackChannel

    This class does not execute or interpret either side.
    """

    def __init__(
        self,
        command_channel: AgentCommandChannel,
        feedback_channel: AgentFeedbackChannel,
    ) -> None:
        if not isinstance(
            command_channel,
            AgentCommandChannel,
        ):
            raise TypeError(
                "command_channel must implement "
                "AgentCommandChannel"
            )

        if not isinstance(
            feedback_channel,
            AgentFeedbackChannel,
        ):
            raise TypeError(
                "feedback_channel must implement "
                "AgentFeedbackChannel"
            )

        self._command_channel = command_channel
        self._feedback_channel = feedback_channel

    def send(
        self,
        agent_decision: AgentDecision,
    ) -> AgentCommandReceipt:
        if not isinstance(
            agent_decision,
            AgentDecision,
        ):
            raise TypeError(
                "agent_decision must be an AgentDecision"
            )

        receipt = self._command_channel.send(
            agent_decision
        )

        if not isinstance(
            receipt,
            AgentCommandReceipt,
        ):
            raise TypeError(
                "command channel must return "
                "AgentCommandReceipt"
            )

        if receipt.agent_decision is not agent_decision:
            raise ValueError(
                "command receipt must preserve the "
                "exact AgentDecision"
            )

        return receipt

    def receive(
        self,
        results: Iterable[ExecutionResult],
    ) -> AgentFeedbackReceipt:
        if isinstance(
            results,
            (str, bytes),
        ):
            raise TypeError(
                "results must be an iterable of "
                "ExecutionResult instances"
            )

        normalized = tuple(results)

        if not all(
            isinstance(
                result,
                ExecutionResult,
            )
            for result in normalized
        ):
            raise TypeError(
                "results must contain only "
                "ExecutionResult instances"
            )

        receipt = self._feedback_channel.receive(
            normalized
        )

        if not isinstance(
            receipt,
            AgentFeedbackReceipt,
        ):
            raise TypeError(
                "feedback channel must return "
                "AgentFeedbackReceipt"
            )

        if receipt.results != normalized:
            raise ValueError(
                "feedback receipt must preserve "
                "the exact feedback results"
            )

        return receipt

    def exchange(
        self,
        agent_decision: AgentDecision,
        results: Iterable[ExecutionResult] | None = None,
    ) -> AgentIntelligenceInteraction:
        command = self.send(
            agent_decision
        )

        feedback = None

        if results is not None:
            feedback = self.receive(
                results
            )

        return AgentIntelligenceInteraction(
            command=command,
            feedback=feedback,
            metadata={
                "stage": "agent_intelligence_integration",
            },
        )