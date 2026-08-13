from __future__ import annotations

from threading import Event
from typing import Protocol, runtime_checkable


@runtime_checkable
class CancellationToken(Protocol):
    """Read-only cancellation state for one execution."""

    @property
    def is_cancelled(self) -> bool:
        ...


class CancellationSource:
    """Mutable cancellation controller for one execution."""

    def __init__(self) -> None:
        self._event = Event()
        self._token = _CancellationToken(self._event)

    @property
    def token(self) -> CancellationToken:
        return self._token

    def cancel(self) -> None:
        """Request cancellation.

        Cancellation is idempotent.
        """
        self._event.set()


class _CancellationToken:
    """Internal read-only token implementation."""

    def __init__(self, event: Event) -> None:
        self._event = event

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()