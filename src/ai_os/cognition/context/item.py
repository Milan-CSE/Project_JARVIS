from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping
import json


def _freeze_json(value: Any, path: str = "value") -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"{path} contains a non-finite float")
        return value
    if isinstance(value, Mapping):
        return MappingProxyType({
            str(key): _freeze_json(item, f"{path}.{key}")
            for key, item in value.items()
        })
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item, f"{path}[]") for item in value)
    raise TypeError(f"{path} must contain only JSON-compatible values")


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _to_plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    return value


def _validate_json(value: Any, field_name: str) -> None:
    try:
        json.dumps(_to_plain(value), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be JSON-serializable") from exc


@dataclass(frozen=True, slots=True)
class InformationItem:
    """Canonical normalized unit of information exposed by Cognition."""

    item_id: str
    content: Any
    source: str
    relevance: float | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.item_id, str) or not self.item_id.strip():
            raise ValueError("item_id must be a non-empty string")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty string")

        if self.relevance is not None:
            if not isinstance(self.relevance, (int, float)) or isinstance(self.relevance, bool):
                raise TypeError("relevance must be a number or None")
            if not isfinite(float(self.relevance)):
                raise ValueError("relevance must be finite")
            if not 0.0 <= float(self.relevance) <= 1.0:
                raise ValueError("relevance must be between 0.0 and 1.0")
            object.__setattr__(self, "relevance", float(self.relevance))

        content = _freeze_json(self.content, "content")
        provenance = _freeze_json(self.provenance, "provenance")
        metadata = _freeze_json(self.metadata, "metadata")

        object.__setattr__(self, "content", content)
        object.__setattr__(self, "provenance", provenance)
        object.__setattr__(self, "metadata", metadata)

        _validate_json(content, "content")
        _validate_json(provenance, "provenance")
        _validate_json(metadata, "metadata")

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "content": _to_plain(self.content),
            "source": self.source,
            "relevance": self.relevance,
            "provenance": _to_plain(self.provenance),
            "metadata": _to_plain(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "InformationItem":
        return cls(
            item_id=data["item_id"],
            content=data["content"],
            source=data["source"],
            relevance=data.get("relevance"),
            provenance=data.get("provenance", {}),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, value: str) -> "InformationItem":
        return cls.from_dict(json.loads(value))
