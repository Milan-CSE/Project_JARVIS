from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class DesktopSessionState(str, Enum):
    IDLE = "idle"
    OBSERVING = "observing"
    REQUESTING = "requesting"
    WAITING = "waiting"
    INTERRUPTED = "interrupted"
    DISCONNECTED = "disconnected"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class DisplayInfo:
    display_id: str
    width: int
    height: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.display_id, str):
            raise TypeError("display_id must be a string")
        if not self.display_id.strip():
            raise ValueError("display_id must not be empty")
        if isinstance(self.width, bool) or not isinstance(self.width, int):
            raise TypeError("width must be an int")
        if isinstance(self.height, bool) or not isinstance(self.height, int):
            raise TypeError("height must be an int")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be > 0")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@dataclass(frozen=True, slots=True)
class WindowInfo:
    window_id: str
    title: str
    application: str
    visible: bool = True
    focused: bool = False
    bounds: tuple[int, int, int, int] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in (
            ("window_id", self.window_id),
            ("title", self.title),
            ("application", self.application),
        ):
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            if not value.strip():
                raise ValueError(f"{name} must not be empty")

        if not isinstance(self.visible, bool):
            raise TypeError("visible must be a bool")
        if not isinstance(self.focused, bool):
            raise TypeError("focused must be a bool")

        if self.bounds is not None:
            if not isinstance(self.bounds, tuple):
                object.__setattr__(self, "bounds", tuple(self.bounds))
            if len(self.bounds) != 4 or not all(
                isinstance(v, int) and not isinstance(v, bool)
                for v in self.bounds
            ):
                raise TypeError("bounds must contain four integers")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@dataclass(frozen=True, slots=True)
class DesktopSnapshot:
    snapshot_id: str
    active_window_id: str | None = None
    windows: tuple[WindowInfo, ...] = ()
    displays: tuple[DisplayInfo, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot_id, str):
            raise TypeError("snapshot_id must be a string")
        if not self.snapshot_id.strip():
            raise ValueError("snapshot_id must not be empty")

        if self.active_window_id is not None:
            if not isinstance(self.active_window_id, str):
                raise TypeError(
                    "active_window_id must be a string or None"
                )

        if not isinstance(self.windows, tuple):
            object.__setattr__(self, "windows", tuple(self.windows))
        if not all(isinstance(w, WindowInfo) for w in self.windows):
            raise TypeError(
                "windows must contain only WindowInfo instances"
            )

        if not isinstance(self.displays, tuple):
            object.__setattr__(self, "displays", tuple(self.displays))
        if not all(isinstance(d, DisplayInfo) for d in self.displays):
            raise TypeError(
                "displays must contain only DisplayInfo instances"
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@dataclass(frozen=True, slots=True)
class DesktopActionRequest:
    request_id: str
    action: str
    target: str | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str):
            raise TypeError("request_id must be a string")
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")

        if not isinstance(self.action, str):
            raise TypeError("action must be a string")
        if not self.action.strip():
            raise ValueError("action must not be empty")

        if self.target is not None and not isinstance(self.target, str):
            raise TypeError("target must be a string or None")

        if not isinstance(self.parameters, Mapping):
            raise TypeError("parameters must be a mapping")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        object.__setattr__(
            self,
            "parameters",
            MappingProxyType(dict(self.parameters)),
        )
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@dataclass(frozen=True, slots=True)
class DesktopActionResult:
    request_id: str
    accepted: bool
    status: str
    output: Any = None
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str):
            raise TypeError("request_id must be a string")
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")
        if not isinstance(self.accepted, bool):
            raise TypeError("accepted must be a bool")
        if not isinstance(self.status, str):
            raise TypeError("status must be a string")
        if not self.status.strip():
            raise ValueError("status must not be empty")
        if self.error is not None and not isinstance(self.error, str):
            raise TypeError("error must be a string or None")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@dataclass(frozen=True, slots=True)
class DesktopSession:
    session_id: str
    state: DesktopSessionState
    active_request_id: str | None = None
    last_snapshot_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.session_id, str):
            raise TypeError("session_id must be a string")
        if not self.session_id.strip():
            raise ValueError("session_id must not be empty")

        if not isinstance(self.state, DesktopSessionState):
            object.__setattr__(
                self,
                "state",
                DesktopSessionState(self.state),
            )

        for name, value in (
            ("active_request_id", self.active_request_id),
            ("last_snapshot_id", self.last_snapshot_id),
        ):
            if value is not None and not isinstance(value, str):
                raise TypeError(f"{name} must be a string or None")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )
