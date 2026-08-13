from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
import json

from .item import InformationItem


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
class Context:
    """
    Immutable working set of information assembled for reasoning.
    """

    query: str
    items: tuple[InformationItem, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("query must be a non-empty string")

        if not isinstance(self.items, (tuple, list)):
            raise TypeError("items must be a sequence of InformationItem")

        normalized_items = tuple(self.items)

        if any(not isinstance(item, InformationItem)
               for item in normalized_items):
            raise TypeError("items must contain only InformationItem objects")

        metadata = _freeze_json(self.metadata)

        object.__setattr__(self, "items", normalized_items)
        object.__setattr__(self, "metadata", metadata)

        json.dumps(_to_plain(metadata), allow_nan=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "items": [item.to_dict() for item in self.items],
            "metadata": _to_plain(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Context":
        return cls(
            query=data["query"],
            items=tuple(
                InformationItem.from_dict(item)
                for item in data.get("items", [])
            ),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, value: str) -> "Context":
        return cls.from_dict(json.loads(value))