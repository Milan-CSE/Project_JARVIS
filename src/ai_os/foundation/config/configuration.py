from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable


class ConfigurationError(Exception):
    """Base error for configuration operations."""


class ConfigurationMissingError(ConfigurationError):
    """Raised when a required configuration key is missing."""


class ConfigurationValidationError(ConfigurationError):
    """Raised when a configuration snapshot is invalid."""


def _freeze(value: Any) -> Any:
    """Recursively convert common mutable containers into immutable values."""
    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                key: _freeze(item)
                for key, item in value.items()
            }
        )

    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)

    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)

    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)

    if isinstance(value, frozenset):
        return frozenset(_freeze(item) for item in value)

    return value


def _validate_key(key: str) -> None:
    if not isinstance(key, str):
        raise TypeError("configuration key must be a string")

    if not key.strip():
        raise ValueError(
            "configuration key must not be empty"
        )

    if key.startswith(".") or key.endswith(".") or ".." in key:
        raise ValueError(
            "configuration key must use non-empty dot-separated segments"
        )

    if any(not part.strip() for part in key.split(".")):
        raise ValueError(
            "configuration key must use non-empty dot-separated segments"
        )


@dataclass(frozen=True, slots=True)
class ConfigurationSnapshot:
    """Immutable point-in-time configuration state."""

    version: str
    values: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.version, str):
            raise TypeError("version must be a string")

        if not self.version.strip():
            raise ValueError(
                "version must not be empty"
            )

        if not isinstance(self.values, Mapping):
            raise TypeError(
                "values must be a mapping"
            )

        normalized: dict[str, Any] = {}

        for key, value in self.values.items():
            _validate_key(key)
            normalized[key] = _freeze(value)

        object.__setattr__(
            self,
            "values",
            MappingProxyType(normalized),
        )

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        _validate_key(key)
        return self.values.get(key, default)

    def require(
        self,
        key: str,
    ) -> Any:
        _validate_key(key)

        if key not in self.values:
            raise ConfigurationMissingError(
                f"required configuration key is missing: {key}"
            )

        return self.values[key]

    def contains(
        self,
        key: str,
    ) -> bool:
        _validate_key(key)
        return key in self.values

    def namespace(
        self,
        namespace: str,
    ) -> Mapping[str, Any]:
        if not isinstance(namespace, str):
            raise TypeError(
                "namespace must be a string"
            )

        namespace = namespace.strip(".")

        if not namespace:
            raise ValueError(
                "namespace must not be empty"
            )

        prefix = namespace + "."
        result = {
            key: value
            for key, value in self.values.items()
            if key == namespace or key.startswith(prefix)
        }

        return MappingProxyType(dict(result))


@runtime_checkable
class Configuration(Protocol):
    def snapshot(self) -> ConfigurationSnapshot:
        ...

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        ...

    def require(
        self,
        key: str,
    ) -> Any:
        ...

    def contains(
        self,
        key: str,
    ) -> bool:
        ...

    def namespace(
        self,
        namespace: str,
    ) -> Mapping[str, Any]:
        ...


@runtime_checkable
class ConfigurationSource(Protocol):
    def load(self) -> Mapping[str, Any]:
        ...


@runtime_checkable
class ConfigurationValidator(Protocol):
    def validate(
        self,
        snapshot: ConfigurationSnapshot,
    ) -> None:
        ...


class ConfigurationManager:
    """
    In-memory authoritative configuration manager for 12.1.

    It owns immutable snapshot replacement, but deliberately has no
    persistence, execution, authorization, plugin lifecycle, or service
    container responsibilities.
    """

    def __init__(
        self,
        initial: Mapping[str, Any] | None = None,
        *,
        sources: tuple[ConfigurationSource, ...] = (),
        validator: ConfigurationValidator | None = None,
    ) -> None:
        if initial is None:
            initial = {}

        if not isinstance(initial, Mapping):
            raise TypeError(
                "initial configuration must be a mapping"
            )

        if not isinstance(sources, tuple):
            sources = tuple(sources)

        if not all(
            isinstance(source, ConfigurationSource)
            for source in sources
        ):
            raise TypeError(
                "sources must contain ConfigurationSource instances"
            )

        if validator is not None and not isinstance(
            validator,
            ConfigurationValidator,
        ):
            raise TypeError(
                "validator must implement ConfigurationValidator"
            )

        merged: dict[str, Any] = {}

        for source in sources:
            values = source.load()

            if not isinstance(values, Mapping):
                raise TypeError(
                    "configuration source must return a mapping"
                )

            merged.update(values)

        merged.update(initial)

        self._validator = validator
        self._snapshot = ConfigurationSnapshot(
            version="config:0",
            values=merged,
        )

        self._validate(self._snapshot)

    def _validate(
        self,
        snapshot: ConfigurationSnapshot,
    ) -> None:
        if self._validator is None:
            return

        try:
            self._validator.validate(snapshot)
        except ConfigurationValidationError:
            raise
        except Exception as exc:
            raise ConfigurationValidationError(
                "configuration validation failed"
            ) from exc

    def snapshot(self) -> ConfigurationSnapshot:
        return self._snapshot

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self._snapshot.get(
            key,
            default,
        )

    def require(
        self,
        key: str,
    ) -> Any:
        return self._snapshot.require(key)

    def contains(
        self,
        key: str,
    ) -> bool:
        return self._snapshot.contains(key)

    def namespace(
        self,
        namespace: str,
    ) -> Mapping[str, Any]:
        return self._snapshot.namespace(namespace)

    def update(
        self,
        changes: Mapping[str, Any],
    ) -> ConfigurationSnapshot:
        if not isinstance(changes, Mapping):
            raise TypeError(
                "changes must be a mapping"
            )

        current = self._snapshot
        candidate_values = dict(current.values)

        for key, value in changes.items():
            _validate_key(key)
            candidate_values[key] = value

        candidate = ConfigurationSnapshot(
            version=f"config:{self._next_version()}",
            values=candidate_values,
        )

        self._validate(candidate)

        # Atomic replacement: candidate becomes visible only after
        # complete construction and validation.
        self._snapshot = candidate
        return candidate

    def remove(
        self,
        keys: str | tuple[str, ...],
    ) -> ConfigurationSnapshot:
        if isinstance(keys, str):
            keys = (keys,)
        elif not isinstance(keys, tuple):
            keys = tuple(keys)

        if not all(isinstance(key, str) for key in keys):
            raise TypeError(
                "keys must contain only strings"
            )

        current = self._snapshot
        candidate_values = dict(current.values)

        for key in keys:
            _validate_key(key)
            candidate_values.pop(key, None)

        candidate = ConfigurationSnapshot(
            version=f"config:{self._next_version()}",
            values=candidate_values,
        )

        self._validate(candidate)
        self._snapshot = candidate
        return candidate

    def _next_version(self) -> int:
        current = self._snapshot.version

        if not current.startswith("config:"):
            return 1

        suffix = current.removeprefix("config:")

        try:
            return int(suffix) + 1
        except ValueError:
            return 1


class MappingConfigurationSource:
    """Simple immutable-friendly source useful for composition/tests."""

    def __init__(self, values: Mapping[str, Any]) -> None:
        if not isinstance(values, Mapping):
            raise TypeError(
                "values must be a mapping"
            )
        self._values = dict(values)

    def load(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(self._values))
