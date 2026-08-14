from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.intelligence.context import IntelligenceContext
from ai_os.intelligence.reasoning.result import ReasoningResult


@runtime_checkable
class ReasoningRule(Protocol):
    """Contract for one deterministic reasoning rule."""

    def evaluate(
        self,
        context: IntelligenceContext,
    ) -> ReasoningResult | None:
        ...