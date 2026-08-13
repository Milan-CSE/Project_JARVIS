from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from ai_os.intelligence.context.source import ContextSource


def _freeze_value(value: Any) -> Any:
    """Recursively freeze common container types."""

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

    return deepcopy(value)


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
class ContextItem:
    """One immutable piece of information available to Intelligence."""

    kind: str
    source: ContextSource
    value: Any
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.kind, str):
            raise TypeError(
                "kind must be a string"
            )

        if not self.kind.strip():
            raise ValueError(
                "kind must not be empty"
            )

        if not isinstance(
            self.source,
            ContextSource,
        ):
            object.__setattr__(
                self,
                "source",
                ContextSource(self.source),
            )

        object.__setattr__(
            self,
            "value",
            _freeze_value(self.value),
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
            _freeze_mapping(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class IntelligenceContext:
    """Immutable, per-request snapshot provided to Intelligence."""

    input: Any
    identity: Any = None
    items: tuple[ContextItem, ...] = ()
    constraints: Mapping[str, Any] = field(
        default_factory=dict
    )
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.items,
            tuple,
        ):
            object.__setattr__(
                self,
                "items",
                tuple(self.items),
            )

        if not all(
            isinstance(item, ContextItem)
            for item in self.items
        ):
            raise TypeError(
                "items must contain ContextItem instances"
            )

        object.__setattr__(
            self,
            "input",
            _freeze_value(self.input),
        )

        object.__setattr__(
            self,
            "identity",
            _freeze_value(self.identity),
        )

        if not isinstance(
            self.constraints,
            Mapping,
        ):
            raise TypeError(
                "constraints must be a mapping"
            )

        object.__setattr__(
            self,
            "constraints",
            _freeze_mapping(self.constraints),
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
            _freeze_mapping(self.metadata),
        )