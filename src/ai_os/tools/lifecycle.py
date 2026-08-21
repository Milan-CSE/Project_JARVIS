from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from ai_os.runtime.tasks.task import Task  # noqa: F401 - boundary guard documentation

from .registry import ToolRegistry
from .tool import Tool


class ToolLifecycleState(str, Enum):
    REGISTERED = "registered"
    VALIDATED = "validated"
    ENABLED = "enabled"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class ToolNotFoundError(LookupError):
    """Raised when a lifecycle operation targets an unknown Tool."""


class ToolLifecycleTransitionError(RuntimeError):
    """Raised when a requested Tool lifecycle transition is invalid."""


class ToolLifecycleValidationError(RuntimeError):
    """Raised when Tool lifecycle validation fails."""


@runtime_checkable
class ToolLifecycleValidator(Protocol):
    """Contract for operational validation of a registered Tool."""

    def validate(self, tool: Tool) -> None:
        ...


class DefaultToolLifecycleValidator:
    """Minimal 10.5 validator; structural validity belongs to 10.1."""

    def validate(self, tool: Tool) -> None:
        if not isinstance(tool, Tool):
            raise TypeError("tool must implement Tool protocol")

        for name in (
            "tool_id",
            "name",
            "version",
            "description",
            "capability",
        ):
            value = getattr(tool, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"tool.{name} must be a non-empty string"
                )


class ToolLifecycleManager:
    """
    10.5 lifecycle state authority for Tools already known by ToolRegistry.

    Registration remains owned by 10.2. Lifecycle state is stored outside
    the immutable Tool object. Authorization remains owned by 10.4.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        validator: ToolLifecycleValidator | None = None,
    ) -> None:
        if not isinstance(registry, ToolRegistry):
            raise TypeError(
                "registry must implement ToolRegistry protocol"
            )

        if validator is None:
            validator = DefaultToolLifecycleValidator()

        if not isinstance(validator, ToolLifecycleValidator):
            raise TypeError(
                "validator must implement ToolLifecycleValidator protocol"
            )

        self._registry = registry
        self._validator = validator
        self._states: dict[str, ToolLifecycleState] = {}

    def get_state(self, tool_id: str) -> ToolLifecycleState | None:
        tool = self._get_registered_tool(tool_id)
        if tool is None:
            return None

        return self._states.get(
            tool_id,
            ToolLifecycleState.REGISTERED,
        )

    def validate(self, tool_id: str) -> None:
        tool = self._require_tool(tool_id)
        current = self.get_state(tool_id)

        if current is ToolLifecycleState.DEPRECATED:
            raise ToolLifecycleTransitionError(
                "deprecated Tool cannot be validated"
            )

        if current is ToolLifecycleState.FAILED:
            raise ToolLifecycleTransitionError(
                "failed Tool cannot be validated"
            )

        if current not in (
            ToolLifecycleState.REGISTERED,
        ):
            raise ToolLifecycleTransitionError(
                f"cannot validate Tool from state: {current.value}"
            )

        try:
            self._validator.validate(tool)
        except Exception as exc:
            self._states[tool_id] = ToolLifecycleState.FAILED
            if isinstance(exc, ToolLifecycleValidationError):
                raise
            raise ToolLifecycleValidationError(
                f"Tool validation failed: {tool_id}"
            ) from exc

        self._states[tool_id] = ToolLifecycleState.VALIDATED

    def enable(self, tool_id: str) -> None:
        self._transition(
            tool_id,
            ToolLifecycleState.ENABLED,
            {
                ToolLifecycleState.VALIDATED,
                ToolLifecycleState.DISABLED,
            },
        )

    def disable(self, tool_id: str) -> None:
        self._transition(
            tool_id,
            ToolLifecycleState.DISABLED,
            {
                ToolLifecycleState.VALIDATED,
                ToolLifecycleState.ENABLED,
            },
        )

    def deprecate(self, tool_id: str) -> None:
        self._transition(
            tool_id,
            ToolLifecycleState.DEPRECATED,
            {
                ToolLifecycleState.VALIDATED,
                ToolLifecycleState.ENABLED,
                ToolLifecycleState.DISABLED,
            },
        )

    def list_states(self) -> MappingProxyType:
        """Return an immutable snapshot of known lifecycle state."""
        snapshot = {
            tool.tool_id: self._states.get(
                tool.tool_id,
                ToolLifecycleState.REGISTERED,
            )
            for tool in self._registry.list_tools()
        }
        return MappingProxyType(snapshot)

    def _get_registered_tool(self, tool_id: str) -> Tool | None:
        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ValueError(
                "tool_id must be a non-empty string"
            )

        tool = self._registry.resolve(tool_id)
        if tool is None:
            return None
        if not isinstance(tool, Tool):
            raise TypeError(
                "ToolRegistry returned an invalid Tool"
            )
        return tool

    def _require_tool(self, tool_id: str) -> Tool:
        tool = self._get_registered_tool(tool_id)
        if tool is None:
            raise ToolNotFoundError(
                f"Tool not registered: {tool_id}"
            )
        return tool

    def _transition(
        self,
        tool_id: str,
        new_state: ToolLifecycleState,
        allowed_states: set[ToolLifecycleState],
    ) -> None:
        self._require_tool(tool_id)
        current = self.get_state(tool_id)

        if current not in allowed_states:
            raise ToolLifecycleTransitionError(
                f"invalid Tool lifecycle transition: "
                f"{current.value} -> {new_state.value}"
            )

        self._states[tool_id] = new_state
