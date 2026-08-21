from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from .registry import ToolRegistry
from .tool import Tool


@dataclass(frozen=True, slots=True)
class ToolContribution:
    """Immutable declarative contribution containing one or more Tools."""

    contribution_id: str
    name: str
    version: str
    tools: tuple[Tool, ...]
    dependencies: tuple[str, ...] = ()
    compatibility: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in (
            "contribution_id",
            "name",
            "version",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a string"
                )
            if not value.strip():
                raise ValueError(
                    f"{field_name} must not be empty"
                )

        if not isinstance(self.tools, tuple):
            object.__setattr__(
                self,
                "tools",
                tuple(self.tools),
            )

        if not self.tools:
            raise ValueError(
                "tools must contain at least one Tool"
            )

        if not all(
            isinstance(tool, Tool)
            for tool in self.tools
        ):
            raise TypeError(
                "tools must contain only Tool instances"
            )

        if not isinstance(self.dependencies, tuple):
            object.__setattr__(
                self,
                "dependencies",
                tuple(self.dependencies),
            )

        if not all(
            isinstance(dep, str) and dep.strip()
            for dep in self.dependencies
        ):
            raise TypeError(
                "dependencies must contain only non-empty strings"
            )

        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError(
                "dependencies must not contain duplicates"
            )

        for field_name in ("compatibility", "metadata"):
            value = getattr(self, field_name)
            if not isinstance(value, Mapping):
                raise TypeError(
                    f"{field_name} must be a mapping"
                )
            object.__setattr__(
                self,
                field_name,
                MappingProxyType(dict(value)),
            )


@runtime_checkable
class ToolContributionValidator(Protocol):
    """Contract for validating an ecosystem contribution."""

    def validate(
        self,
        contribution: ToolContribution,
    ) -> None:
        ...


class DefaultToolContributionValidator:
    """Deterministic structural validator for 10.6 contributions."""

    def validate(
        self,
        contribution: ToolContribution,
    ) -> None:
        if not isinstance(
            contribution,
            ToolContribution,
        ):
            raise TypeError(
                "contribution must be a ToolContribution"
            )

        seen_tool_ids: set[str] = set()

        for tool in contribution.tools:
            if not isinstance(tool, Tool):
                raise TypeError(
                    "contribution contains an invalid Tool"
                )

            if tool.tool_id in seen_tool_ids:
                raise ValueError(
                    f"duplicate tool_id within contribution: "
                    f"{tool.tool_id}"
                )

            seen_tool_ids.add(tool.tool_id)


class ToolEcosystemConflictError(ValueError):
    """Raised when a contribution conflicts with registered Tools."""


class ToolEcosystemResultStatus(str):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ToolEcosystemResult:
    """Immutable admission decision.

    10.6 approves or rejects a contribution. It deliberately does not
    mutate the frozen 10.2 ToolRegistry because that contract has no
    transaction/rollback operation.
    """

    accepted: bool
    contribution_id: str
    tool_ids: tuple[str, ...]
    reason: str
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.accepted, bool):
            raise TypeError(
                "accepted must be a bool"
            )

        for name in (
            "contribution_id",
            "reason",
        ):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(
                    f"{name} must be a string"
                )
            if not value.strip():
                raise ValueError(
                    f"{name} must not be empty"
                )

        if not isinstance(self.tool_ids, tuple):
            object.__setattr__(
                self,
                "tool_ids",
                tuple(self.tool_ids),
            )

        if not all(
            isinstance(tool_id, str) and tool_id.strip()
            for tool_id in self.tool_ids
        ):
            raise TypeError(
                "tool_ids must contain only non-empty strings"
            )

        if len(set(self.tool_ids)) != len(self.tool_ids):
            raise ValueError(
                "tool_ids must not contain duplicates"
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


class ToolEcosystemManager:
    """
    10.6 ecosystem admission boundary.

    This stage validates a contribution and preflights registry conflicts.
    It intentionally does NOT mutate the frozen 10.2 registry because
    ToolRegistry has no transactional registration/rollback API.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        validator: ToolContributionValidator | None = None,
    ) -> None:
        if not isinstance(
            registry,
            ToolRegistry,
        ):
            raise TypeError(
                "registry must implement ToolRegistry protocol"
            )

        if validator is None:
            validator = DefaultToolContributionValidator()

        if not isinstance(
            validator,
            ToolContributionValidator,
        ):
            raise TypeError(
                "validator must implement "
                "ToolContributionValidator protocol"
            )

        self._registry = registry
        self._validator = validator
        self._admitted: set[str] = set()

    def admit(
        self,
        contribution: ToolContribution,
    ) -> ToolEcosystemResult:
        if not isinstance(
            contribution,
            ToolContribution,
        ):
            raise TypeError(
                "contribution must be a ToolContribution"
            )

        if (
            contribution.contribution_id
            in self._admitted
        ):
            return ToolEcosystemResult(
                accepted=False,
                contribution_id=contribution.contribution_id,
                tool_ids=tuple(
                    tool.tool_id
                    for tool in contribution.tools
                ),
                reason="duplicate contribution_id",
            )

        try:
            self._validator.validate(
                contribution
            )
        except Exception:
            raise

        tool_ids = tuple(
            tool.tool_id
            for tool in contribution.tools
        )

        for tool_id in tool_ids:
            existing = self._registry.resolve(
                tool_id
            )
            if existing is not None:
                return ToolEcosystemResult(
                    accepted=False,
                    contribution_id=(
                        contribution.contribution_id
                    ),
                    tool_ids=tool_ids,
                    reason=(
                        f"duplicate tool_id: {tool_id}"
                    ),
                )

        # Capability collisions are explicitly allowed.
        self._admitted.add(
            contribution.contribution_id
        )

        return ToolEcosystemResult(
            accepted=True,
            contribution_id=contribution.contribution_id,
            tool_ids=tool_ids,
            reason="contribution admitted",
            metadata={
                "stage": "tool_ecosystem",
                "registry_mutated": False,
            },
        )
