from __future__ import annotations

from typing import Protocol, runtime_checkable

from .identity import Identity


@runtime_checkable
class IdentityResolver(Protocol):
    """Contract for resolving an already validated identity reference."""

    def resolve(
        self,
        identity_id: str,
    ) -> Identity | None:
        ...