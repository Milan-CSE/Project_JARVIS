from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from ai_os.identity import Identity
from ai_os.foundation.security.security import SecurityContext

from .tool import Tool


@dataclass(frozen=True, slots=True)
class SecurityDecision:
    """Immutable authorization decision for one Tool request."""

    allowed: bool
    identity_id: str
    tool_id: str
    capability: str
    required_permissions: tuple[str, ...] = ()
    missing_permissions: tuple[str, ...] = ()
    reason: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise TypeError("allowed must be a bool")
        for name in ("identity_id", "tool_id", "capability", "reason"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            if name != "reason" and not value.strip():
                raise ValueError(f"{name} must not be empty")
        for name in ("required_permissions", "missing_permissions"):
            values = getattr(self, name)
            if not isinstance(values, tuple):
                object.__setattr__(self, name, tuple(values))
                values = getattr(self, name)
            if not all(isinstance(v, str) and v.strip() for v in values):
                raise TypeError(f"{name} must contain non-empty strings")
        if len(set(self.required_permissions)) != len(self.required_permissions):
            raise ValueError("required_permissions must not contain duplicates")
        if len(set(self.missing_permissions)) != len(self.missing_permissions):
            raise ValueError("missing_permissions must not contain duplicates")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        if not set(self.missing_permissions).issubset(self.required_permissions):
            raise ValueError("missing_permissions must be a subset of required_permissions")
        if self.allowed and self.missing_permissions:
            raise ValueError("allowed decision cannot contain missing_permissions")
        if not self.allowed and not self.reason.strip():
            raise ValueError("denied decision requires a reason")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@runtime_checkable
class ToolSecurityPolicy(Protocol):
    def authorize(
        self,
        identity: Identity,
        tool: Tool,
        security_context: SecurityContext,
    ) -> SecurityDecision:
        ...


class DefaultToolSecurityPolicy:
    """Exact-match, principal-scoped, fail-closed authorization policy."""

    def __init__(self, grants: Mapping[str, tuple[str, ...] | list[str] | set[str]] | None = None) -> None:
        if grants is None:
            grants = {}
        if not isinstance(grants, Mapping):
            raise TypeError("grants must be a mapping")
        normalized: dict[str, frozenset[str]] = {}
        for principal, permissions in grants.items():
            if not isinstance(principal, str) or not principal.strip():
                raise ValueError("grant principal must be a non-empty string")
            if isinstance(permissions, (str, bytes)):
                raise TypeError("grant permissions must be a collection of strings")
            permission_set = frozenset(permissions)
            if not all(isinstance(p, str) and p.strip() for p in permission_set):
                raise TypeError("grant permissions must contain non-empty strings")
            normalized[principal] = permission_set
        self._grants = MappingProxyType(normalized)

    def authorize(self, identity: Identity, tool: Tool, security_context: SecurityContext) -> SecurityDecision:
        if not isinstance(identity, Identity):
            raise TypeError("identity must be an Identity")
        if not isinstance(tool, Tool):
            raise TypeError("tool must implement Tool protocol")
        if not isinstance(security_context, SecurityContext):
            raise TypeError("security_context must be a SecurityContext")
        required = tuple(tool.required_permissions)
        missing: tuple[str, ...]
        if not security_context.authenticated:
            missing = required
            return SecurityDecision(
                allowed=False,
                identity_id=identity.identity_id,
                tool_id=tool.tool_id,
                capability=tool.capability,
                required_permissions=required,
                missing_permissions=missing,
                reason="identity is not authenticated",
            )
        if security_context.principal != identity.principal:
            return SecurityDecision(
                allowed=False,
                identity_id=identity.identity_id,
                tool_id=tool.tool_id,
                capability=tool.capability,
                required_permissions=required,
                missing_permissions=required,
                reason="security principal does not match identity principal",
            )
        granted = self._grants.get(identity.principal, frozenset())
        missing = tuple(p for p in required if p not in granted)
        if missing:
            return SecurityDecision(
                allowed=False,
                identity_id=identity.identity_id,
                tool_id=tool.tool_id,
                capability=tool.capability,
                required_permissions=required,
                missing_permissions=missing,
                reason="missing required permission(s)",
            )
        return SecurityDecision(
            allowed=True,
            identity_id=identity.identity_id,
            tool_id=tool.tool_id,
            capability=tool.capability,
            required_permissions=required,
            missing_permissions=(),
            reason="authorized",
        )


class ToolSecurity:
    """10.4 authorization boundary; never executes Tools or Tasks."""

    def __init__(self, policy: ToolSecurityPolicy) -> None:
        if not isinstance(policy, ToolSecurityPolicy):
            raise TypeError("policy must implement ToolSecurityPolicy")
        self._policy = policy

    def authorize(
        self,
        identity: Identity,
        tool: Tool,
        security_context: SecurityContext,
    ) -> SecurityDecision:
        if not isinstance(identity, Identity):
            raise TypeError("identity must be an Identity")
        if not isinstance(tool, Tool):
            raise TypeError("tool must implement Tool protocol")
        if not isinstance(security_context, SecurityContext):
            raise TypeError("security_context must be a SecurityContext")
        decision = self._policy.authorize(identity, tool, security_context)
        if not isinstance(decision, SecurityDecision):
            raise TypeError("policy must return SecurityDecision")
        if decision.identity_id != identity.identity_id:
            raise ValueError("security decision identity_id mismatch")
        if decision.tool_id != tool.tool_id:
            raise ValueError("security decision tool_id mismatch")
        if decision.capability != tool.capability:
            raise ValueError("security decision capability mismatch")
        return decision
