from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import DesktopActionRequest, DesktopActionResult


@runtime_checkable
class DesktopController(Protocol):
    """Boundary for submitting OS action requests."""

    def request_action(
        self,
        request: DesktopActionRequest,
    ) -> DesktopActionResult:
        ...


class DefaultDesktopController:
    """Contract-only placeholder; does not execute OS operations."""

    def request_action(
        self,
        request: DesktopActionRequest,
    ) -> DesktopActionResult:
        raise NotImplementedError(
            "No concrete desktop controller configured"
        )
