from enum import Enum


class IdentityType(Enum):
    USER = "user"
    SERVICE = "service"
    AGENT = "agent"
    SYSTEM = "system"