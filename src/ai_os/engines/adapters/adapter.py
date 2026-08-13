from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ai_os.engines.request import EngineRequest
from ai_os.engines.result import EngineResult


@runtime_checkable
class EngineAdapter(Protocol):
    """Contract for translating external engine representations."""

    def adapt_request(
        self,
        request: EngineRequest,
    ) -> Any:
        ...

    def adapt_result(
        self,
        result: Any,
    ) -> EngineResult:
        ...