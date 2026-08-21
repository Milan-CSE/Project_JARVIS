from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class PlatformContract:
    """Immutable identity of the AI-OS platform boundary."""

    platform_id: str
    version: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.platform_id, str):
            raise TypeError("platform_id must be a string")

        if not self.platform_id.strip():
            raise ValueError("platform_id must not be empty")

        if not isinstance(self.version, str):
            raise TypeError("version must be a string")

        if not self.version.strip():
            raise ValueError("version must not be empty")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@dataclass(frozen=True, slots=True)
class PlatformComponentDescriptor:
    """Immutable descriptor for a component admitted to the platform boundary."""

    component_id: str
    version: str
    component_type: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "component_id",
            "version",
            "component_type",
        ):
            value = getattr(self, name)

            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")

            if not value.strip():
                raise ValueError(f"{name} must not be empty")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@runtime_checkable
class PlatformComponent(Protocol):
    """Stable structural contract for a platform component descriptor provider."""

    @property
    def descriptor(self) -> PlatformComponentDescriptor:
        ...


@runtime_checkable
class PlatformBoundary(Protocol):
    """Stable structural contract for the future platform host boundary."""

    @property
    def contract(self) -> PlatformContract:
        ...
