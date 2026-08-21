from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import DesktopSnapshot


@runtime_checkable
class DesktopObserver(Protocol):
    """Passive observation contract for desktop state."""

    def snapshot(self) -> DesktopSnapshot:
        ...


class DefaultDesktopObserver:
    """Contract-only placeholder for OS-specific observers."""

    def snapshot(self) -> DesktopSnapshot:
        raise NotImplementedError(
            "No concrete desktop observer configured"
        )
