from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from ai_os.intelligence.orchestration_models import (
    IntelligenceOrchestrationResult,
)

from .generator import (
    DefaultResponseGenerator,
    ResponseGeneratorContract,
)
from .models import Response


@dataclass(frozen=True, slots=True)
class ResponseGenerationResult:
    """Immutable result of the 9.5.9 response-generation stage."""

    response: Response
    source: IntelligenceOrchestrationResult
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.response,
            Response,
        ):
            raise TypeError(
                "response must be a Response"
            )

        if not isinstance(
            self.source,
            IntelligenceOrchestrationResult,
        ):
            raise TypeError(
                "source must be an "
                "IntelligenceOrchestrationResult"
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


class ResponseGenerationPipeline:
    """
    9.5.9:

        IntelligenceOrchestrationResult
                    ↓
        ResponseGeneratorContract
                    ↓
                 Response
    """

    def __init__(
        self,
        generator: ResponseGeneratorContract | None = None,
    ) -> None:
        if generator is None:
            generator = DefaultResponseGenerator()

        if not isinstance(
            generator,
            ResponseGeneratorContract,
        ):
            raise TypeError(
                "generator must implement "
                "ResponseGeneratorContract"
            )

        self._generator = generator

    def run(
        self,
        result: IntelligenceOrchestrationResult,
    ) -> ResponseGenerationResult:
        if not isinstance(
            result,
            IntelligenceOrchestrationResult,
        ):
            raise TypeError(
                "result must be an "
                "IntelligenceOrchestrationResult"
            )

        response = self._generator.generate(
            result
        )

        if not isinstance(
            response,
            Response,
        ):
            raise TypeError(
                "generator must return a Response"
            )

        if response.source_status is not result.status:
            raise ValueError(
                "response source_status must match "
                "orchestration result status"
            )

        return ResponseGenerationResult(
            response=response,
            source=result,
            metadata={
                "stage": "response_generation",
            },
        )