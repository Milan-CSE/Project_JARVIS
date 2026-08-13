from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
import json

from .types import IdentityType


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
class Identity:
    """Immutable representation of an actor."""

    identity_id: str
    principal: str
    identity_type: IdentityType
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.identity_id, str) or not self.identity_id.strip():
            raise ValueError("identity_id must be a non-empty string")

        if not isinstance(self.principal, str) or not self.principal.strip():
            raise ValueError("principal must be a non-empty string")

        if not isinstance(self.identity_type, IdentityType):
            raise TypeError("identity_type must be an IdentityType")

        metadata = _freeze_json(self.metadata)

        object.__setattr__(self, "metadata", metadata)

        json.dumps(
            _to_plain(metadata),
            allow_nan=False,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "principal": self.principal,
            "identity_type": self.identity_type.value,
            "metadata": _to_plain(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Identity":
        return cls(
            identity_id=data["identity_id"],
            principal=data["principal"],
            identity_type=IdentityType(data["identity_type"]),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, value: str) -> "Identity":
        return cls.from_dict(json.loads(value))