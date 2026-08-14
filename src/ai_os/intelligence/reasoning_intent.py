from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from ai_os.intelligence.context import IntelligenceContext
from ai_os.intelligence.intent import Intent
from ai_os.intelligence.reasoning import (
    IntentCandidate,
    IntentExtractor,
    IntentSelector,
    Reasoner,
    ReasoningResolution,
    ReasoningResolutionStatus,
    ReasoningResolver,
    ReasoningResult,
)
from ai_os.runtime.cancellation import CancellationToken


# ---------------------------------------------------------------------------
# 9.5.2 local behavioral contracts
# ---------------------------------------------------------------------------


@runtime_checkable
class ReasoningResolverContract(Protocol):
    """Contract required by the 9.5.2 reasoning-to-intent pipeline."""

    def resolve(
        self,
        result: ReasoningResult,
        candidate_index: int | None = None,
    ) -> ReasoningResolution:
        ...


@runtime_checkable
class IntentSelectorContract(Protocol):
    """Contract required by the 9.5.2 reasoning-to-intent pipeline."""

    def select(
        self,
        result: ReasoningResult,
        candidate_index: int | None = None,
    ) -> IntentCandidate:
        ...


@runtime_checkable
class IntentExtractorContract(Protocol):
    """Contract required by the 9.5.2 reasoning-to-intent pipeline."""

    def extract(
        self,
        candidate: IntentCandidate,
        intent_id: str,
    ) -> Intent:
        ...


# ---------------------------------------------------------------------------
# 9.5.2 result model
# ---------------------------------------------------------------------------


class ReasoningIntentStatus(str, Enum):
    RESOLVED = "resolved"

    CLARIFICATION_REQUIRED = "clarification_required"
    AMBIGUOUS = "clarification_required"

    UNRESOLVED = "unresolved"
    NO_INTENT = "unresolved"


@dataclass(frozen=True, slots=True)
class ReasoningIntentResult:
    """Immutable result of the 9.5.2 Reasoning → Intent pipeline."""

    status: ReasoningIntentStatus
    context: IntelligenceContext
    reasoning: ReasoningResult
    resolution: ReasoningResolution
    intent: Intent | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            ReasoningIntentStatus,
        ):
            object.__setattr__(
                self,
                "status",
                ReasoningIntentStatus(self.status),
            )

        if not isinstance(
            self.context,
            IntelligenceContext,
        ):
            raise TypeError(
                "context must be an IntelligenceContext"
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


# ---------------------------------------------------------------------------
# 9.5.2 pipeline
# ---------------------------------------------------------------------------


class ReasoningIntentPipeline:
    """
    9.5.2 pipeline:

        IntelligenceContext
                ↓
             Reasoner
                ↓
         ReasoningResult
                ↓
       Resolver Contract
                ↓
        ReasoningResolution
                ↓
       Selector Contract
                ↓
         IntentCandidate
                ↓
      Extractor Contract
                ↓
              Intent

    The pipeline intentionally stops at Intent.
    """

    def __init__(
        self,
        reasoner: Reasoner,
        resolver: ReasoningResolverContract | None = None,
        selector: IntentSelectorContract | None = None,
        extractor: IntentExtractorContract | None = None,
    ) -> None:
        # Reuse the frozen 9.4 Reasoner contract.
        if not isinstance(
            reasoner,
            Reasoner,
        ):
            raise TypeError(
                "reasoner must implement Reasoner protocol"
            )

        # Use structural contracts for injected dependencies.
        if resolver is not None and not isinstance(
            resolver,
            ReasoningResolverContract,
        ):
            raise TypeError(
                "resolver must implement "
                "ReasoningResolverContract"
            )

        if selector is not None and not isinstance(
            selector,
            IntentSelectorContract,
        ):
            raise TypeError(
                "selector must implement "
                "IntentSelectorContract"
            )

        if extractor is not None and not isinstance(
            extractor,
            IntentExtractorContract,
        ):
            raise TypeError(
                "extractor must implement "
                "IntentExtractorContract"
            )

        self._reasoner = reasoner

        # Existing 9.4 implementations remain the defaults.
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

    def run(
        self,
        context: IntelligenceContext,
        intent_id: str,
        candidate_index: int | None = None,
        cancellation_token: CancellationToken | None = None,
    ) -> ReasoningIntentResult:
        # ---------------------------------------------------------------
        # Input validation
        # ---------------------------------------------------------------

        if not isinstance(
            context,
            IntelligenceContext,
        ):
            raise TypeError(
                "context must be an IntelligenceContext"
            )

        if not isinstance(
            intent_id,
            str,
        ):
            raise TypeError(
                "intent_id must be a string"
            )

        if not intent_id.strip():
            raise ValueError(
                "intent_id must not be empty or whitespace"
            )

        # Do not duplicate the resolver's range semantics.
        # We only reject obviously invalid Python types here.
        if candidate_index is not None:
            if isinstance(
                candidate_index,
                bool,
            ):
                raise TypeError(
                    "candidate_index must be an int or None"
                )

            if not isinstance(
                candidate_index,
                int,
            ):
                raise TypeError(
                    "candidate_index must be an int or None"
                )

        # ---------------------------------------------------------------
        # Stage 1: Reasoning
        # ---------------------------------------------------------------

        reasoning = self._reasoner.reason(
            context,
            cancellation_token,
        )

        if not isinstance(
            reasoning,
            ReasoningResult,
        ):
            raise TypeError(
                "reasoner must return a ReasoningResult"
            )

        # ---------------------------------------------------------------
        # Stage 2: Resolution
        # ---------------------------------------------------------------

        resolution = self._resolver.resolve(
            reasoning,
            candidate_index,
        )

        if not isinstance(
            resolution,
            ReasoningResolution,
        ):
            raise TypeError(
                "resolver must return a ReasoningResolution"
            )

        # ---------------------------------------------------------------
        # Stage 3: Resolution outcome handling
        # ---------------------------------------------------------------

        if (
            resolution.status
            is ReasoningResolutionStatus.UNRESOLVED
        ):
            return ReasoningIntentResult(
                status=ReasoningIntentStatus.UNRESOLVED,
                context=context,
                reasoning=reasoning,
                resolution=resolution,
            )

        if (
            resolution.status
            is ReasoningResolutionStatus.CLARIFICATION_REQUIRED
        ):
            return ReasoningIntentResult(
                status=(
                    ReasoningIntentStatus
                    .CLARIFICATION_REQUIRED
                ),
                context=context,
                reasoning=reasoning,
                resolution=resolution,
            )

        # ---------------------------------------------------------------
        # Stage 4: Candidate selection
        # ---------------------------------------------------------------

        selected = self._selector.select(
            reasoning,
            candidate_index=resolution.candidate_index,
        )

        if not isinstance(
            selected,
            IntentCandidate,
        ):
            raise TypeError(
                "selector must return an IntentCandidate"
            )

        # ---------------------------------------------------------------
        # Stage 5: Intent extraction
        # ---------------------------------------------------------------

        intent = self._extractor.extract(
            selected,
            intent_id,
        )

        if not isinstance(
            intent,
            Intent,
        ):
            raise TypeError(
                "extractor must return an Intent"
            )

        # ---------------------------------------------------------------
        # Completed 9.5.2
        # ---------------------------------------------------------------

        return ReasoningIntentResult(
            status=ReasoningIntentStatus.RESOLVED,
            context=context,
            reasoning=reasoning,
            resolution=resolution,
            intent=intent,
            metadata={
                "stage": "reasoning_to_intent",
            },
        )