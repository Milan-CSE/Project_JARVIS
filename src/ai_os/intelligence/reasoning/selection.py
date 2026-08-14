from __future__ import annotations

from ai_os.intelligence.reasoning.result import (
    IntentCandidate,
    ReasoningResult,
)
from ai_os.intelligence.intent import Intent


class NoIntentCandidateError(ValueError):
    """Raised when reasoning produced no Intent candidates."""


class AmbiguousIntentError(ValueError):
    """Raised when multiple Intent candidates exist without explicit selection."""


class IntentSelector:
    """Selects one IntentCandidate without inventing meaning."""

    def select(
        self,
        result: ReasoningResult,
        candidate_index: int | None = None,
    ) -> IntentCandidate:
        if not isinstance(result, ReasoningResult):
            raise TypeError(
                "result must be a ReasoningResult"
            )

        candidates = result.intent_candidates

        if not candidates:
            raise NoIntentCandidateError(
                "reasoning produced no intent candidates"
            )

        if candidate_index is None:
            if len(candidates) != 1:
                raise AmbiguousIntentError(
                    "multiple intent candidates require "
                    "explicit selection"
                )

            return candidates[0]

        if isinstance(candidate_index, bool):
            raise TypeError(
                "candidate_index must be an integer"
            )

        if not isinstance(candidate_index, int):
            raise TypeError(
                "candidate_index must be an integer"
            )

        if (
            candidate_index < 0
            or candidate_index >= len(candidates)
        ):
            raise IndexError(
                "candidate_index is out of range"
            )

        return candidates[candidate_index]


class IntentExtractor:
    """Converts a selected IntentCandidate into an immutable Intent."""

    def extract(
        self,
        candidate: IntentCandidate,
        intent_id: str,
    ) -> Intent:
        if not isinstance(
            candidate,
            IntentCandidate,
        ):
            raise TypeError(
                "candidate must be an IntentCandidate"
            )

        if not isinstance(intent_id, str):
            raise TypeError(
                "intent_id must be a string"
            )

        if not intent_id.strip():
            raise ValueError(
                "intent_id must not be empty"
            )

        return Intent(
            intent_id=intent_id,
            goal=candidate.goal,
            parameters=candidate.parameters,
            constraints=candidate.constraints,
            metadata=candidate.metadata,
        )