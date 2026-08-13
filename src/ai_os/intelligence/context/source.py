from __future__ import annotations

from enum import Enum


class ContextSource(str, Enum):
    """Origin of an Intelligence context item."""

    SYSTEM = "system"
    IDENTITY = "identity"
    USER = "user"
    MEMORY = "memory"
    DOCUMENT = "document"
    EXTERNAL = "external"