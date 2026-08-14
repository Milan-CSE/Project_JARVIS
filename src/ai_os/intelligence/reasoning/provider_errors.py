from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping


class ReasoningProviderError(RuntimeError):
    """Normalized provider-boundary failure."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        if not isinstance(code, str):
            raise TypeError(
                "code must be a string"
            )

        if not code.strip():
            raise ValueError(
                "code must not be empty"
            )

        if not isinstance(message, str):
            raise TypeError(
                "message must be a string"
            )

        if not message.strip():
            raise ValueError(
                "message must not be empty"
            )

        if details is None:
            details = {}

        if not isinstance(details, Mapping):
            raise TypeError(
                "details must be a mapping"
            )

        self.code = code
        self.message = message
        self.details = MappingProxyType(dict(details))

        super().__init__(message)