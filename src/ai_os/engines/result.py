from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
import json

from .types import EngineStatus


def _freeze_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value

    if isinstance(value, Mapping):
        return MappingProxyType({
            str(key): _freeze_json(item)
            for key, item in value.items()
        })

    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)

    raise TypeError(
        "Value must contain only JSON-compatible values"
    )


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _to_plain(item)
            for key, item in value.items()
        }

    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]

    return value


@dataclass(frozen=True, slots=True)
class EngineResult:
    """Immutable result produced by an Engine."""

    status: EngineStatus
    output: Any = None
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.status, EngineStatus):
            raise TypeError(
                "status must be an EngineStatus"
            )

        if self.status is EngineStatus.FAILED:
            if self.error is None:
                raise ValueError(
                    "FAILED result requires an error"
                )

            if not isinstance(self.error, str):
                raise TypeError(
                    "error must be a string"
                )

            if not self.error.strip():
                raise ValueError(
                    "error must be a non-empty string"
                )

        if self.status is not EngineStatus.FAILED:
            if self.error is not None:
                raise ValueError(
                    "Only FAILED results may contain an error"
                )

        frozen_output = _freeze_json(self.output)
        frozen_metadata = _freeze_json(self.metadata)

        object.__setattr__(
            self,
            "output",
            frozen_output,
        )

        object.__setattr__(
            self,
            "metadata",
            frozen_metadata,
        )

        json.dumps(
            _to_plain(frozen_output),
            allow_nan=False,
        )

        json.dumps(
            _to_plain(frozen_metadata),
            allow_nan=False,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "output": _to_plain(self.output),
            "error": self.error,
            "metadata": _to_plain(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "EngineResult":
        return cls(
            status=EngineStatus(data["status"]),
            output=data.get("output"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, value: str) -> "EngineResult":
        return cls.from_dict(json.loads(value))