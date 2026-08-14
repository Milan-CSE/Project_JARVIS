from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                key: _freeze_value(item)
                for key, item in value.items()
            }
        )

    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze_value(item)
            for item in value
        )

    if isinstance(value, (set, frozenset)):
        return frozenset(
            _freeze_value(item)
            for item in value
        )

    return value


def _freeze_mapping(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    return MappingProxyType(
        {
            key: _freeze_value(item)
            for key, item in value.items()
        }
    )


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    """Immutable provider-facing input snapshot."""

    input: Any
    requested_output: Any = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "input",
            _freeze_value(self.input),
        )

        object.__setattr__(
            self,
            "requested_output",
            _freeze_value(self.requested_output),
        )

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    """Immutable normalized output from one Provider invocation."""

    output: Any
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )
    usage: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping"
            )

        if not isinstance(self.usage, Mapping):
            raise TypeError(
                "usage must be a mapping"
            )

        object.__setattr__(
            self,
            "output",
            _freeze_value(self.output),
        )

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )

        object.__setattr__(
            self,
            "usage",
            _freeze_mapping(self.usage),
        )