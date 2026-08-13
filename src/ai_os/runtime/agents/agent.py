from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.runtime.agents.request import AgentRequest
from ai_os.runtime.agents.response import AgentResponse
from ai_os.runtime.cancellation import CancellationToken


@runtime_checkable
class Agent(Protocol):
    """Contract for coordinating one Agent interaction."""

    def handle(
        self,
        request: AgentRequest,
        cancellation_token: CancellationToken | None = None,
    ) -> AgentResponse:
        ...