from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from ai_os.intelligence.decision import (
    Decision,
    DecisionKind,
)
from ai_os.intelligence.intent import Intent
from ai_os.runtime.cancellation import CancellationToken


class DecisionGenerationCancelledError(RuntimeError):
    """Raised when decision generation is cancelled."""

class DecisionUndeterminedError(RuntimeError):
    """Raised when no decision-generation rule matches."""


@runtime_checkable
class DecisionGenerationRule(Protocol):
    """Contract for one deterministic decision-generation rule."""

    def evaluate(
        self,
        intent: Intent,
    ) -> DecisionKind | None:
        ...


class RuleBasedDecisionGenerator:
    """Deterministic generator using ordered decision rules."""

    def __init__(
        self,
        rules: Iterable[DecisionGenerationRule] = (),
    ) -> None:
        self._rules = tuple(rules)

        for rule in self._rules:
            if not isinstance(
                rule,
                DecisionGenerationRule,
            ):
                raise TypeError(
                    "rules must implement "
                    "DecisionGenerationRule protocol"
                )

    def generate(
        self,
        intent: Intent,
        decision_id: str,
        cancellation_token: CancellationToken | None = None,
    ) -> Decision:
        if not isinstance(intent, Intent):
            raise TypeError(
                "intent must be an Intent"
            )

        if not isinstance(decision_id, str):
            raise TypeError(
                "decision_id must be a string"
            )

        if not decision_id.strip():
            raise ValueError(
                "decision_id must not be empty"
            )

        for rule in self._rules:
            if (
                cancellation_token is not None
                and cancellation_token.is_cancelled
            ):
                raise DecisionGenerationCancelledError(
                    "decision generation was cancelled"
                )

            result = rule.evaluate(intent)

            if result is None:
                continue

            if not isinstance(
                result,
                DecisionKind,
            ):
                try:
                    result = DecisionKind(result)
                except (TypeError, ValueError) as exc:
                    raise TypeError(
                        "DecisionGenerationRule must return "
                        "DecisionKind or None"
                    ) from exc

            return Decision(
                decision_id=decision_id,
                intent_id=intent.intent_id,
                kind=result,
            )

        if (
            cancellation_token is not None
            and cancellation_token.is_cancelled
        ):
            raise DecisionGenerationCancelledError(
                "decision generation was cancelled"
            )

        raise DecisionUndeterminedError(
            "no decision-generation rule matched the intent"
        )

    def __len__(self) -> int:
        return len(self._rules)