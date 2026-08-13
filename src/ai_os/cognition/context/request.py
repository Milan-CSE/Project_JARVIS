from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
import json


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

    raise TypeError("Value must contain only JSON-compatible values")


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
class ContextRequest:
    """
    Describes the information needed for a reasoning operation.
    """

    query: str
    max_items: int = 10
    filters: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("query must be a non-empty string")

        if not isinstance(self.max_items, int) or isinstance(
            self.max_items, bool
        ):
            raise TypeError("max_items must be an integer")

        if self.max_items <= 0:
            raise ValueError("max_items must be greater than 0")

        filters = _freeze_json(self.filters)
        metadata = _freeze_json(self.metadata)

        object.__setattr__(self, "filters", filters)
        object.__setattr__(self, "metadata", metadata)

        # Final JSON-compatibility check.
        json.dumps(_to_plain(filters), allow_nan=False)
        json.dumps(_to_plain(metadata), allow_nan=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "max_items": self.max_items,
            "filters": _to_plain(self.filters),
            "metadata": _to_plain(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContextRequest":
        return cls(
            query=data["query"],
            max_items=data.get("max_items", 10),
            filters=data.get("filters", {}),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, value: str) -> "ContextRequest":
        return cls.from_dict(json.loads(value))