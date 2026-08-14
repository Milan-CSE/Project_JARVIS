from __future__ import annotations

from collections.abc import Iterable

from ai_os.intelligence.context import IntelligenceContext
from ai_os.intelligence.reasoning.reasoner import Reasoner
from ai_os.intelligence.reasoning.result import ReasoningResult
from ai_os.intelligence.reasoning.rule import ReasoningRule
from ai_os.runtime.cancellation import CancellationToken

from ai_os.intelligence.reasoning.parser import (
    ReasoningOutputParser,
    ReasoningOutputParserProtocol,
)
from ai_os.intelligence.reasoning.provider import (
    ReasoningProvider,
)
from ai_os.intelligence.reasoning.provider_errors import (
    ReasoningProviderError,
)
from ai_os.intelligence.reasoning.provider_models import (
    ProviderRequest,
)


class ReasoningCancelledError(RuntimeError):
    """Raised when deterministic reasoning is cancelled."""


class RuleBasedReasoner:
    """Deterministic Reasoner using ordered rules."""

    def __init__(
        self,
        rules: Iterable[ReasoningRule] = (),
    ) -> None:
        self._rules = tuple(rules)

        for rule in self._rules:
            if not isinstance(rule, ReasoningRule):
                raise TypeError(
                    "rules must implement ReasoningRule protocol"
                )

    def reason(
        self,
        context: IntelligenceContext,
        cancellation_token: CancellationToken | None = None,
    ) -> ReasoningResult:
        if not isinstance(context, IntelligenceContext):
            raise TypeError(
                "context must be an IntelligenceContext"
            )

        for rule in self._rules:
            if (
                cancellation_token is not None
                and cancellation_token.is_cancelled
            ):
                raise ReasoningCancelledError(
                    "reasoning was cancelled"
                )

            result = rule.evaluate(context)

            if result is None:
                continue

            if not isinstance(result, ReasoningResult):
                raise TypeError(
                    "ReasoningRule must return "
                    "ReasoningResult or None"
                )

            return result

        if (
            cancellation_token is not None
            and cancellation_token.is_cancelled
        ):
            raise ReasoningCancelledError(
                "reasoning was cancelled"
            )

        return ReasoningResult()

    def __len__(self) -> int:
        return len(self._rules)

class ProviderBackedReasoner:
    """Reasoner backed by one normalized ReasoningProvider."""

    def __init__(
        self,
        provider: ReasoningProvider,
        parser: ReasoningOutputParser | None = None,
    ) -> None:
        if not isinstance(
            provider,
            ReasoningProvider,
        ):
            raise TypeError(
                "provider must implement "
                "ReasoningProvider protocol"
            )

        if parser is None:
            parser = ReasoningOutputParser()

        if not isinstance(
            parser,
            ReasoningOutputParserProtocol,
        ):
            raise TypeError(
                "parser must implement "
                "ReasoningOutputParser protocol"
            )

        self._provider = provider
        self._parser = parser

    def reason(
        self,
        context: IntelligenceContext,
        cancellation_token: CancellationToken | None = None,
    ) -> ReasoningResult:
        if not isinstance(
            context,
            IntelligenceContext,
        ):
            raise TypeError(
                "context must be an IntelligenceContext"
            )

        request = ProviderRequest(
            input={
                "input": context.input,
                "identity": context.identity,
                "items": context.items,
                "constraints": context.constraints,
                "metadata": context.metadata,
            },
            requested_output={
                "type": "reasoning_result",
                "schema": "ai_os.reasoning_result.v1",
            },
        )

        try:
            response = self._provider.generate(
                request,
                cancellation_token,
            )
        except ReasoningProviderError as exc:
            if exc.code == "provider_cancelled":
                raise ReasoningCancelledError(
                    "reasoning was cancelled"
                ) from exc

            raise

        return self._parser.parse(
            response.output
        )