from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.intelligence.orchestration_models import (
    IntelligenceOrchestrationResult,
    IntelligenceOrchestrationStatus,
)

from .models import Response, ResponseStatus


@runtime_checkable
class ResponseGeneratorContract(Protocol):
    """9.5.9 contract for orchestration-result → Response."""

    def generate(
        self,
        result: IntelligenceOrchestrationResult,
    ) -> Response:
        ...


class DefaultResponseGenerator:
    """
    Deterministic baseline response generator.

    This does not execute anything and never claims that execution
    occurred.
    """

    def generate(
        self,
        result: IntelligenceOrchestrationResult,
    ) -> Response:
        if not isinstance(
            result,
            IntelligenceOrchestrationResult,
        ):
            raise TypeError(
                "result must be an "
                "IntelligenceOrchestrationResult"
            )

        if (
            result.status
            is IntelligenceOrchestrationStatus.COMPLETED
        ):
            content = (
                "Your request has been understood and "
                "prepared for the next execution stage."
            )
            response_status = ResponseStatus.COMPLETED

        elif (
            result.status
            is IntelligenceOrchestrationStatus.BLOCKED
        ):
            content = (
                "Your request could not proceed because "
                "the required conditions were not satisfied."
            )
            response_status = ResponseStatus.BLOCKED

        elif (
            result.status
            is IntelligenceOrchestrationStatus.CANCELLED
        ):
            content = (
                "Your request was cancelled before "
                "completion."
            )
            response_status = ResponseStatus.CANCELLED

        else:
            content = (
                "Your request could not be processed "
                "because an internal failure occurred."
            )
            response_status = ResponseStatus.FAILED

        return Response(
            status=response_status,
            content=content,
            source_status=result.status,
            metadata={
                "stage": "response_generation",
            },
        )