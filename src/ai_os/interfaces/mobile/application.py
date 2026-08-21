from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.interfaces.api import APIEvent, APIRequest

from .client import MobileApplicationClient
from .models import (
    MobileConnectivityState,
    MobileViewModel,
)


@runtime_checkable
class MobileApplication(Protocol):
    def send(
        self,
        request: APIRequest,
    ) -> MobileViewModel:
        ...

    def synchronize(
        self,
        request_id: str,
        current: MobileViewModel | None = None,
    ) -> MobileViewModel:
        ...

    def mark_background(
        self,
        current: MobileViewModel,
    ) -> MobileViewModel:
        ...

    def mark_disconnected(
        self,
        current: MobileViewModel,
    ) -> MobileViewModel:
        ...


class DefaultMobileApplication:
    """Thin composition boundary for the mobile interface."""

    def __init__(
        self,
        client: MobileApplicationClient,
    ) -> None:
        if not isinstance(client, MobileApplicationClient):
            raise TypeError(
                "client must be a MobileApplicationClient"
            )
        self._client = client

    def send(
        self,
        request: APIRequest,
    ) -> MobileViewModel:
        return self._client.send(request)

    def synchronize(
        self,
        request_id: str,
        current: MobileViewModel | None = None,
    ) -> MobileViewModel:
        return self._client.synchronize(
            request_id,
            current=current,
        )

    def mark_background(
        self,
        current: MobileViewModel,
    ) -> MobileViewModel:
        return self._client.mark_background(current)

    def mark_disconnected(
        self,
        current: MobileViewModel,
    ) -> MobileViewModel:
        return self._client.mark_disconnected(current)

    def update_connectivity(
        self,
        current: MobileViewModel,
        connectivity: MobileConnectivityState,
    ) -> MobileViewModel:
        return self._client.update_connectivity(
            current,
            connectivity,
        )
