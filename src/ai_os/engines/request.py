from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
import json

from ai_os.identity import Identity


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
class EngineRequest:
    """Immutable request sent to an Engine."""

    request_id: str
    identity: Identity
    input: Any
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str):
            raise TypeError("request_id must be a string")

        if not self.request_id.strip():
            raise ValueError("request_id must be a non-empty string")

        if not isinstance(self.identity, Identity):
            raise TypeError("identity must be an Identity")

        frozen_input = _freeze_json(self.input)
        frozen_metadata = _freeze_json(self.metadata)

        object.__setattr__(self, "input", frozen_input)
        object.__setattr__(self, "metadata", frozen_metadata)

        json.dumps(
            _to_plain(frozen_input),
            allow_nan=False,
        )

        json.dumps(
            _to_plain(frozen_metadata),
            allow_nan=False,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "identity": self.identity.to_dict(),
            "input": _to_plain(self.input),
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
    ) -> "EngineRequest":
        return cls(
            request_id=data["request_id"],
            identity=Identity.from_dict(data["identity"]),
            input=data["input"],
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, value: str) -> "EngineRequest":
        return cls.from_dict(json.loads(value))