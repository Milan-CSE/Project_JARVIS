from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.intelligence.reasoning.provider_models import (
    ProviderRequest,
    ProviderResponse,
)
from ai_os.runtime.cancellation import CancellationToken


@runtime_checkable
class ReasoningProvider(Protocol):
    """Contract for one external/internal reasoning provider."""

    def generate(
        self,
        request: ProviderRequest,
        cancellation_token: CancellationToken | None = None,
    ) -> ProviderResponse:
        ...