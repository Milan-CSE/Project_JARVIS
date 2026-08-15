from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from ai_os.intelligence.orchestration_models import (
    IntelligenceOrchestrationStatus,
)


class ResponseStatus(str, Enum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class Response:
    """Immutable user-facing response envelope."""

    status: ResponseStatus
    content: str
    source_status: IntelligenceOrchestrationStatus
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            ResponseStatus,
        ):
            object.__setattr__(
                self,
                "status",
                ResponseStatus(self.status),
            )

        if not isinstance(
            self.content,
            str,
        ):
            raise TypeError(
                "content must be a string"
            )

        if not self.content.strip():
            raise ValueError(
                "content must not be empty or whitespace"
            )

        if not isinstance(
            self.source_status,
            IntelligenceOrchestrationStatus,
        ):
            raise TypeError(
                "source_status must be an "
                "IntelligenceOrchestrationStatus"
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