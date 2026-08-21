from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable
import json


def _freeze_json(value: Any, path: str = "value") -> Any:
    """Freeze JSON-compatible data into immutable structures."""
    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"{path} contains a non-finite float")
        return value

    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                str(key): _freeze_json(item, f"{path}.{key}")
                for key, item in value.items()
            }
        )

    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze_json(item, f"{path}[]")
            for item in value
        )

    raise TypeError(
        f"{path} must contain only JSON-compatible values"
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


def _validate_json(value: Any, field_name: str) -> None:
    try:
        json.dumps(
            _to_plain(value),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be JSON-serializable"
        ) from exc


@runtime_checkable
class Tool(Protocol):
    """Declarative contract for an external AI-OS capability."""

    @property
    def tool_id(self) -> str:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def version(self) -> str:
        ...

    @property
    def description(self) -> str:
        ...

    @property
    def capability(self) -> str:
        ...

    @property
    def input_schema(self) -> Mapping[str, Any]:
        ...

    @property
    def required_permissions(self) -> tuple[str, ...]:
        ...

    @property
    def metadata(self) -> Mapping[str, Any]:
        ...


@dataclass(frozen=True, slots=True)
class DefaultTool:
    """Immutable declarative Tool definition.

    This model intentionally contains no execution, lifecycle,
    runtime, workflow, intelligence, identity, or authorization API.
    """

    tool_id: str
    name: str
    version: str
    description: str
    capability: str
    input_schema: Mapping[str, Any] = field(default_factory=dict)
    required_permissions: tuple[str, ...] = field(
        default_factory=tuple
    )
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        for field_name in (
            "tool_id",
            "name",
            "version",
            "description",
            "capability",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a string"
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} must not be empty"
                )

        if not isinstance(
            self.input_schema,
            Mapping,
        ):
            raise TypeError(
                "input_schema must be a mapping"
            )

        if not isinstance(
            self.required_permissions,
            (tuple, list),
        ):
            raise TypeError(
                "required_permissions must be a "
                "sequence of strings"
            )

        permissions = tuple(
            self.required_permissions
        )

        for permission in permissions:
            if not isinstance(permission, str):
                raise TypeError(
                    "required_permissions must contain "
                    "only strings"
                )

            if not permission.strip():
                raise ValueError(
                    "required_permissions must not contain "
                    "empty strings"
                )

        if len(set(permissions)) != len(permissions):
            raise ValueError(
                "required_permissions must not contain duplicates"
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a mapping"
            )

        frozen_schema = _freeze_json(
            self.input_schema,
            "input_schema",
        )
        frozen_metadata = _freeze_json(
            self.metadata,
            "metadata",
        )

        # Keep the public permission collection immutable too.
        object.__setattr__(
            self,
            "input_schema",
            frozen_schema,
        )
        object.__setattr__(
            self,
            "required_permissions",
            permissions,
        )
        object.__setattr__(
            self,
            "metadata",
            frozen_metadata,
        )

        _validate_json(
            frozen_schema,
            "input_schema",
        )
        _validate_json(
            frozen_metadata,
            "metadata",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "capability": self.capability,
            "input_schema": _to_plain(
                self.input_schema
            ),
            "required_permissions": list(
                self.required_permissions
            ),
            "metadata": _to_plain(
                self.metadata
            ),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )
