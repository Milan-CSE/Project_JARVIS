from __future__ import annotations

from dataclasses import replace
from typing import Protocol, runtime_checkable

from .models import (
    DesktopActionRequest,
    DesktopActionResult,
    DesktopSession,
    DesktopSessionState,
    DesktopSnapshot,
)
from .observer import DesktopObserver
from .controller import DesktopController


@runtime_checkable
class DesktopApplication(Protocol):
    def observe(self) -> DesktopSnapshot:
        ...

    def request_action(
        self,
        request: DesktopActionRequest,
    ) -> DesktopActionResult:
        ...

    def mark_disconnected(
        self,
        session: DesktopSession,
    ) -> DesktopSession:
        ...

    def interrupt(
        self,
        session: DesktopSession,
    ) -> DesktopSession:
        ...


class DefaultDesktopApplication:
    """
    Thin Desktop/OS interface.

    Observation and action requests are deliberately separate.
    This class does not execute OS operations and does not own
    Runtime/Tool/Security/Identity behavior.
    """

    def __init__(
        self,
        observer: DesktopObserver,
        controller: DesktopController,
    ) -> None:
        if not isinstance(observer, DesktopObserver):
            raise TypeError(
                "observer must implement DesktopObserver"
            )
        if not isinstance(controller, DesktopController):
            raise TypeError(
                "controller must implement DesktopController"
            )

        self._observer = observer
        self._controller = controller

    def observe(self) -> DesktopSnapshot:
        snapshot = self._observer.snapshot()

        if not isinstance(snapshot, DesktopSnapshot):
            raise TypeError(
                "observer.snapshot must return a DesktopSnapshot"
            )

        return snapshot

    def request_action(
        self,
        request: DesktopActionRequest,
    ) -> DesktopActionResult:
        if not isinstance(
            request,
            DesktopActionRequest,
        ):
            raise TypeError(
                "request must be a DesktopActionRequest"
            )

        result = self._controller.request_action(request)

        if not isinstance(
            result,
            DesktopActionResult,
        ):
            raise TypeError(
                "controller.request_action must return "
                "a DesktopActionResult"
            )

        if result.request_id != request.request_id:
            raise ValueError(
                "result request_id must match request request_id"
            )

        return result

    def mark_disconnected(
        self,
        session: DesktopSession,
    ) -> DesktopSession:
        if not isinstance(
            session,
            DesktopSession,
        ):
            raise TypeError(
                "session must be a DesktopSession"
            )

        return replace(
            session,
            state=DesktopSessionState.DISCONNECTED,
        )

    def interrupt(
        self,
        session: DesktopSession,
    ) -> DesktopSession:
        if not isinstance(
            session,
            DesktopSession,
        ):
            raise TypeError(
                "session must be a DesktopSession"
            )

        return replace(
            session,
            state=DesktopSessionState.INTERRUPTED,
        )
