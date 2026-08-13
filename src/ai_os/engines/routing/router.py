from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.engines.request import EngineRequest
from ai_os.engines.result import EngineResult


@runtime_checkable
class EngineRouter(Protocol):
    """Contract for selecting and dispatching requests to Engines."""

    def route(
        self,
        request: EngineRequest,
    ) -> EngineResult:
        ...