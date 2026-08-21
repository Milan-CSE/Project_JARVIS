from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.interfaces.api import APIEvent, APIRequest, APIResponse

from .models import (
    MobileConnectivityState,
    MobileViewModel,
)


@runtime_checkable
class MobileTransport(Protocol):
    """Transport-neutral mobile client contract."""

    def send(
        self,
        request: APIRequest,
    ) -> APIResponse:
        ...

    def subscribe(
        self,
        correlation_id: str,
    ) -> tuple[APIEvent, ...]:
        ...


class MobileApplicationClient:
    """
    Thin mobile client over the frozen 11.2 API boundary.

    No offline command queue, retry engine, authorization logic,
    identity authority, or direct Runtime/Tool access exists here.
    """

    def __init__(self, transport: MobileTransport) -> None:
        if not isinstance(transport, MobileTransport):
            raise TypeError(
                "transport must implement MobileTransport"
            )
        self._transport = transport

    def send(
        self,
        request: APIRequest,
        connectivity: MobileConnectivityState = (
            MobileConnectivityState.ONLINE
        ),
    ) -> MobileViewModel:
        if not isinstance(request, APIRequest):
            raise TypeError("request must be an APIRequest")

        if not isinstance(
            connectivity,
            MobileConnectivityState,
        ):
            connectivity = MobileConnectivityState(connectivity)

        if connectivity is not MobileConnectivityState.ONLINE:
            raise ConnectionError(
                "cannot send an API request while mobile "
                "connectivity is not online"
            )

        response = self._transport.send(request)

        if not isinstance(response, APIResponse):
            raise TypeError(
                "transport.send must return an APIResponse"
            )

        if response.request_id != request.request_id:
            raise ValueError(
                "response request_id must match request request_id"
            )

        return MobileViewModel.from_response(
            response,
            connectivity=connectivity,
        )

    def synchronize(
        self,
        request_id: str,
        current: MobileViewModel | None = None,
    ) -> MobileViewModel:
        if not isinstance(request_id, str):
            raise TypeError("request_id must be a string")
        if not request_id.strip():
            raise ValueError("request_id must not be empty")

        if current is None:
            current = MobileViewModel(
                request_id=request_id,
                state="pending",
            )

        if not isinstance(current, MobileViewModel):
            raise TypeError(
                "current must be a MobileViewModel or None"
            )

        if current.request_id != request_id:
            raise ValueError(
                "current request_id must match request_id"
            )

        events = self._transport.subscribe(request_id)
        state = current

        for event in events:
            state = state.with_event(event)

        return state

    def mark_background(
        self,
        current: MobileViewModel,
    ) -> MobileViewModel:
        if not isinstance(current, MobileViewModel):
            raise TypeError(
                "current must be a MobileViewModel"
            )
        return current.mark_background()

    def mark_disconnected(
        self,
        current: MobileViewModel,
    ) -> MobileViewModel:
        if not isinstance(current, MobileViewModel):
            raise TypeError(
                "current must be a MobileViewModel"
            )
        return current.mark_disconnected()

    def update_connectivity(
        self,
        current: MobileViewModel,
        connectivity: MobileConnectivityState,
    ) -> MobileViewModel:
        if not isinstance(current, MobileViewModel):
            raise TypeError(
                "current must be a MobileViewModel"
            )
        return current.with_connectivity(connectivity)
