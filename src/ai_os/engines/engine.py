from __future__ import annotations

from typing import Protocol, runtime_checkable

from .request import EngineRequest
from .result import EngineResult
from .types import EngineType


@runtime_checkable
class Engine(Protocol):
    """Contract implemented by all AI OS engines."""

    @property
    def engine_id(self) -> str:
        ...

    @property
    def engine_type(self) -> EngineType:
        ...

    def execute(
        self,
        request: EngineRequest,
    ) -> EngineResult:
        ...