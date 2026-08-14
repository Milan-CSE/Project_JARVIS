from __future__ import annotations

from typing import Any

from ai_os.intelligence.context import IntelligenceContext
from ai_os.intelligence.intelligence import Intelligence

from ai_os.intelligence.reasoning import (
    IntentExtractor,
    IntentSelector,
    Reasoner,
    ReasoningResolver,
    ReasoningResolution,
    ReasoningResolutionStatus,
    ReasoningResult,
    RuleBasedDecisionGenerator,
)

from ai_os.runtime.cancellation import CancellationToken

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from ai_os.intelligence.decision import Decision
from ai_os.intelligence.intent import Intent


class ReasoningPipelineStatus(str, Enum):
    READY = "ready"
    CLARIFICATION_REQUIRED = "clarification_required"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class ReasoningPipelineOutcome:
    """Immutable outcome of the 9.4.9 Reasoning → Intent → Decision pipeline."""

    status: ReasoningPipelineStatus
    reasoning: ReasoningResult
    resolution: ReasoningResolution
    intent: Intent | None = None
    decision: Decision | None = None
    metadata: Mapping[str, object] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            ReasoningPipelineStatus,
        ):
            object.__setattr__(
                self,
                "status",
                ReasoningPipelineStatus(self.status),
            )

        if not isinstance(
            self.reasoning,
            ReasoningResult,
        ):
            raise TypeError(
                "reasoning must be a ReasoningResult"
            )

        if not isinstance(
            self.resolution,
            ReasoningResolution,
        ):
            raise TypeError(
                "resolution must be a ReasoningResolution"
            )

        if self.intent is not None and not isinstance(
            self.intent,
            Intent,
        ):
            raise TypeError(
                "intent must be an Intent or None"
            )

        if self.decision is not None and not isinstance(
            self.decision,
            Decision,
        ):
            raise TypeError(
                "decision must be a Decision or None"
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


class ReasoningPipeline:
    """9.4.9 pipeline: Reasoning → Intent → Decision."""

    def __init__(
        self,
        reasoner: Reasoner,
        resolver: ReasoningResolver | None = None,
        selector: IntentSelector | None = None,
        extractor: IntentExtractor | None = None,
        decision_generator=None,
    ) -> None:
        if not isinstance(reasoner, Reasoner):
            raise TypeError(
                "reasoner must implement Reasoner protocol"
            )

        self._reasoner = reasoner
        self._resolver = (
            resolver
            if resolver is not None
            else ReasoningResolver()
        )
        self._selector = (
            selector
            if selector is not None
            else IntentSelector()
        )
        self._extractor = (
            extractor
            if extractor is not None
            else IntentExtractor()
        )
        self._decision_generator = (
            decision_generator
            if decision_generator is not None
            else RuleBasedDecisionGenerator()
        )

    def run(
        self,
        context: IntelligenceContext,
        intent_id: str,
        decision_id: str,
        candidate_index: int | None = None,
        cancellation_token: CancellationToken | None = None,
    ) -> ReasoningPipelineOutcome:
        if not isinstance(
            context,
            IntelligenceContext,
        ):
            raise TypeError(
                "context must be an IntelligenceContext"
            )

        reasoning = self._reasoner.reason(
            context,
            cancellation_token,
        )

        resolution = self._resolver.resolve(
            reasoning,
            candidate_index,
        )

        if (
            resolution.status
            is ReasoningResolutionStatus.UNRESOLVED
        ):
            return ReasoningPipelineOutcome(
                status=ReasoningPipelineStatus.UNRESOLVED,
                reasoning=reasoning,
                resolution=resolution,
            )

        if (
            resolution.status
            is ReasoningResolutionStatus.CLARIFICATION_REQUIRED
        ):
            return ReasoningPipelineOutcome(
                status=ReasoningPipelineStatus.CLARIFICATION_REQUIRED,
                reasoning=reasoning,
                resolution=resolution,
            )

        selected = self._selector.select(
            reasoning,
            candidate_index=resolution.candidate_index,
        )

        intent = self._extractor.extract(
            selected,
            intent_id,
        )

        decision = self._decision_generator.generate(
            intent,
            decision_id,
            cancellation_token,
        )

        return ReasoningPipelineOutcome(
            status=ReasoningPipelineStatus.READY,
            reasoning=reasoning,
            resolution=resolution,
            intent=intent,
            decision=decision,
        )


class IntegratedIntelligence:
    """9.1 Intelligence implementation backed by the 9.4 pipeline."""

    def __init__(
        self,
        pipeline: ReasoningPipeline,
    ) -> None:
        if not isinstance(
            pipeline,
            ReasoningPipeline,
        ):
            raise TypeError(
                "pipeline must be a ReasoningPipeline"
            )

        self._pipeline = pipeline

    def decide(
        self,
        input: Any,
        cancellation_token: CancellationToken | None = None,
    ) -> Any:
        if isinstance(
            input,
            IntelligenceContext,
        ):
            context = input
        else:
            context = IntelligenceContext(
                input=input,
            )

        return self._pipeline.run(
            context=context,
            intent_id="intent:integration",
            decision_id="decision:integration",
            cancellation_token=cancellation_token,
        )