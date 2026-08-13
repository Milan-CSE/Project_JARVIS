from dataclasses import dataclass


class SecurityError(Exception):
    """Raised when a security operation fails."""


@dataclass(frozen=True)
class SecurityContext:
    principal: str
    authenticated: bool = False


class SecretRedactor:
    REDACTED = "[REDACTED]"

    @classmethod
    def redact(cls, value: str) -> str:
        if not value:
            return value

        return cls.REDACTED