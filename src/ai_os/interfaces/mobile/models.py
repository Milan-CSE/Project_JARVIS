from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from ai_os.interfaces.api import APIEvent, APIResponse


class MobileConnectivityState(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"


class MobileOperationState(str, Enum):
    IDLE = "idle"
    PENDING = "pending"
    SUCCESS = "success"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"
    DISCONNECTED = "disconnected"
    BACKGROUND = "background"


@dataclass(frozen=True, slots=True)
class MobileViewModel:
    """Immutable presentation-only mobile state."""

    request_id: str
    state: MobileOperationState
    connectivity: MobileConnectivityState = MobileConnectivityState.ONLINE
    output: Any = None
    events: tuple[APIEvent, ...] = ()
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str):
            raise TypeError("request_id must be a string")
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")

        if not isinstance(self.state, MobileOperationState):
            object.__setattr__(
                self,
                "state",
                MobileOperationState(self.state),
            )

        if not isinstance(
            self.connectivity,
            MobileConnectivityState,
        ):
            object.__setattr__(
                self,
                "connectivity",
                MobileConnectivityState(self.connectivity),
            )

        if not isinstance(self.events, tuple):
            object.__setattr__(
                self,
                "events",
                tuple(self.events),
            )

        if not all(
            isinstance(event, APIEvent)
            for event in self.events
        ):
            raise TypeError(
                "events must contain only APIEvent instances"
            )

        if self.error is not None and not isinstance(
            self.error,
            str,
        ):
            raise TypeError("error must be a string or None")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    @classmethod
    def from_response(
        cls,
        response: APIResponse,
        connectivity: MobileConnectivityState = (
            MobileConnectivityState.ONLINE
        ),
    ) -> MobileViewModel:
        if not isinstance(response, APIResponse):
            raise TypeError("response must be an APIResponse")

        status_map = {
            "success": MobileOperationState.SUCCESS,
            "accepted": MobileOperationState.PENDING,
            "blocked": MobileOperationState.BLOCKED,
            "failed": MobileOperationState.FAILED,
            "cancelled": MobileOperationState.CANCELLED,
            "incomplete": MobileOperationState.INCOMPLETE,
        }

        return cls(
            request_id=response.request_id,
            state=status_map[response.status.value],
            connectivity=connectivity,
            output=response.output,
            error=(
                response.error.message
                if response.error is not None
                else None
            ),
            metadata=response.metadata,
        )

    def with_event(self, event: APIEvent) -> MobileViewModel:
        if not isinstance(event, APIEvent):
            raise TypeError("event must be an APIEvent")

        if event.correlation_id != self.request_id:
            raise ValueError(
                "event correlation_id must match request_id"
            )

        if any(
            existing.event_id == event.event_id
            for existing in self.events
        ):
            return self

        return MobileViewModel(
            request_id=self.request_id,
            state=MobileOperationState.PENDING,
            connectivity=self.connectivity,
            output=self.output,
            events=self.events + (event,),
            error=self.error,
            metadata=self.metadata,
        )

    def mark_background(self) -> MobileViewModel:
        return MobileViewModel(
            request_id=self.request_id,
            state=MobileOperationState.BACKGROUND,
            connectivity=self.connectivity,
            output=self.output,
            events=self.events,
            error=self.error,
            metadata=self.metadata,
        )

    def mark_disconnected(self) -> MobileViewModel:
        return MobileViewModel(
            request_id=self.request_id,
            state=MobileOperationState.DISCONNECTED,
            connectivity=MobileConnectivityState.DISCONNECTED,
            output=self.output,
            events=self.events,
            error=self.error,
            metadata=self.metadata,
        )

    def with_connectivity(
        self,
        state: MobileConnectivityState,
    ) -> MobileViewModel:
        if not isinstance(state, MobileConnectivityState):
            state = MobileConnectivityState(state)

        return MobileViewModel(
            request_id=self.request_id,
            state=self.state,
            connectivity=state,
            output=self.output,
            events=self.events,
            error=self.error,
            metadata=self.metadata,
        )
