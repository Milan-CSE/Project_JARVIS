from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping
import json
import re

from .errors import InvalidPlanError, InvalidResultError


_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
_STEP_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")
_PLAN_ID_RE = _STEP_ID_RE


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def step_output_ref(step_id: str, path: str | None = None) -> dict[str, str]:
    """Create a serializable reference to a previous step's output."""
    _validate_identifier(step_id, "step_id")
    if path is not None and not path:
        raise ValueError("reference path must not be empty")
    value = f"steps.{step_id}.output"
    if path:
        value += f".{path}"
    return {"$ref": value}


def artifact_ref(artifact_id: str) -> dict[str, str]:
    """Create a serializable reference to an external artifact."""
    if not isinstance(artifact_id, str) or not artifact_id.strip():
        raise ValueError("artifact_id must be a non-empty string")
    return {"type": "artifact", "id": artifact_id}


def _validate_identifier(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value or not _STEP_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a non-empty identifier")


def _validate_capability(value: Any) -> None:
    if not isinstance(value, str) or not _CAPABILITY_RE.fullmatch(value):
        raise ValueError(
            "capability must be a lowercase namespace-qualified identifier "
            "such as 'web.search'"
        )


def _freeze_json(value: Any, path: str = "value") -> Any:
    """Recursively make JSON-compatible data immutable."""
    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"{path} contains a non-finite float")
        return value

    if isinstance(value, Mapping):
        frozen = {
            str(key): _freeze_json(item, f"{path}.{key}")
            for key, item in value.items()
        }
        return MappingProxyType(frozen)

    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item, f"{path}[]") for item in value)

    raise TypeError(
        f"{path} must contain only JSON-compatible values, "
        f"mappings, sequences, or supported references"
    )


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _to_plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


def _validate_json_serializable(value: Any, field_name: str) -> None:
    try:
        json.dumps(_to_plain(value), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} is not JSON serializable") from exc


def _validate_references(value: Any, known_step_ids: set[str], path: str = "input") -> None:
    if isinstance(value, Mapping):
        if "$ref" in value:
            ref = value["$ref"]
            if not isinstance(ref, str) or not ref.startswith("steps."):
                raise InvalidPlanError(f"{path} contains an invalid step reference")
            parts = ref.split(".")
            if len(parts) < 3 or parts[0] != "steps" or parts[2] != "output":
                raise InvalidPlanError(
                    f"{path} has invalid reference '{ref}'; "
                    "expected 'steps.<step_id>.output[.<path>]'"
                )
            if parts[1] not in known_step_ids:
                raise InvalidPlanError(
                    f"{path} references unknown step '{parts[1]}'"
                )
        if value.get("type") == "artifact":
            artifact_id = value.get("id")
            if not isinstance(artifact_id, str) or not artifact_id.strip():
                raise InvalidPlanError(f"{path} contains an invalid artifact reference")

        for key, item in value.items():
            _validate_references(item, known_step_ids, f"{path}.{key}")
    elif isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            _validate_references(item, known_step_ids, f"{path}[{index}]")


@dataclass(frozen=True, slots=True)
class ExecutionError:
    code: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("error code must not be empty")
        if not self.message.strip():
            raise ValueError("error message must not be empty")
        object.__setattr__(self, "details", _freeze_json(self.details, "details"))
        _validate_json_serializable(self.details, "details")

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": _to_plain(self.details),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutionError":
        return cls(
            code=data["code"],
            message=data["message"],
            details=data.get("details", {}),
        )


@dataclass(frozen=True, slots=True)
class ExecutionStep:
    step_id: str
    capability: str
    input: Mapping[str, Any] = field(default_factory=dict)
    dependencies: tuple[str, ...] = ()
    constraints: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_identifier(self.step_id, "step_id")
        _validate_capability(self.capability)

        dependencies = tuple(self.dependencies)
        if len(dependencies) != len(set(dependencies)):
            raise ValueError(f"step '{self.step_id}' contains duplicate dependencies")
        for dependency in dependencies:
            _validate_identifier(dependency, "dependency")
        if self.step_id in dependencies:
            raise ValueError(f"step '{self.step_id}' cannot depend on itself")

        object.__setattr__(self, "dependencies", dependencies)
        object.__setattr__(self, "input", _freeze_json(self.input, "input"))
        object.__setattr__(self, "constraints", _freeze_json(self.constraints, "constraints"))
        object.__setattr__(self, "metadata", _freeze_json(self.metadata, "metadata"))

        _validate_json_serializable(self.input, "input")
        _validate_json_serializable(self.constraints, "constraints")
        _validate_json_serializable(self.metadata, "metadata")

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "capability": self.capability,
            "input": _to_plain(self.input),
            "dependencies": list(self.dependencies),
            "constraints": _to_plain(self.constraints),
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutionStep":
        return cls(
            step_id=data["step_id"],
            capability=data["capability"],
            input=data.get("input", {}),
            dependencies=tuple(data.get("dependencies", ())),
            constraints=data.get("constraints", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    plan_id: str
    steps: tuple[ExecutionStep, ...]
    constraints: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_identifier(self.plan_id, "plan_id")
        steps = tuple(self.steps)
        if not steps:
            raise InvalidPlanError("execution plan must contain at least one step")

        step_ids = [step.step_id for step in steps]
        if len(step_ids) != len(set(step_ids)):
            raise InvalidPlanError("execution plan contains duplicate step IDs")

        known_step_ids = set(step_ids)
        for step in steps:
            unknown = set(step.dependencies) - known_step_ids
            if unknown:
                raise InvalidPlanError(
                    f"step '{step.step_id}' references unknown dependencies: "
                    f"{sorted(unknown)}"
                )
            _validate_references(step.input, known_step_ids, f"step '{step.step_id}' input")
            _validate_references(
                step.constraints,
                known_step_ids,
                f"step '{step.step_id}' constraints",
            )
            _validate_references(
                step.metadata,
                known_step_ids,
                f"step '{step.step_id}' metadata",
            )

        object.__setattr__(self, "steps", steps)
        object.__setattr__(self, "constraints", _freeze_json(self.constraints, "constraints"))
        object.__setattr__(self, "metadata", _freeze_json(self.metadata, "metadata"))

        _validate_json_serializable(self.constraints, "constraints")
        _validate_json_serializable(self.metadata, "metadata")
        self._validate_acyclic()

    def _validate_acyclic(self) -> None:
        graph = {step.step_id: set(step.dependencies) for step in self.steps}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(step_id: str) -> None:
            if step_id in visiting:
                raise InvalidPlanError("execution plan dependencies contain a cycle")
            if step_id in visited:
                return
            visiting.add(step_id)
            for dependency in graph[step_id]:
                visit(dependency)
            visiting.remove(step_id)
            visited.add(step_id)

        for step_id in graph:
            visit(step_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "steps": [step.to_dict() for step in self.steps],
            "constraints": _to_plain(self.constraints),
            "metadata": _to_plain(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutionPlan":
        return cls(
            plan_id=data["plan_id"],
            steps=tuple(ExecutionStep.from_dict(item) for item in data["steps"]),
            constraints=data.get("constraints", {}),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, value: str) -> "ExecutionPlan":
        return cls.from_dict(json.loads(value))


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    plan_id: str
    step_id: str
    status: ExecutionStatus
    output: Any = None
    error: ExecutionError | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_identifier(self.plan_id, "plan_id")
        _validate_identifier(self.step_id, "step_id")
        if not isinstance(self.status, ExecutionStatus):
            object.__setattr__(self, "status", ExecutionStatus(self.status))

        if self.status is ExecutionStatus.FAILED and self.error is None:
            raise InvalidResultError("FAILED result requires an ExecutionError")
        if self.status is ExecutionStatus.COMPLETED and self.error is not None:
            raise InvalidResultError("COMPLETED result cannot contain an error")

        object.__setattr__(self, "output", _freeze_json(self.output, "output"))
        object.__setattr__(self, "metadata", _freeze_json(self.metadata, "metadata"))

        _validate_json_serializable(self.output, "output")
        _validate_json_serializable(self.metadata, "metadata")

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "step_id": self.step_id,
            "status": self.status.value,
            "output": _to_plain(self.output),
            "error": self.error.to_dict() if self.error else None,
            "metadata": _to_plain(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutionResult":
        error_data = data.get("error")
        return cls(
            plan_id=data["plan_id"],
            step_id=data["step_id"],
            status=ExecutionStatus(data["status"]),
            output=data.get("output"),
            error=ExecutionError.from_dict(error_data) if error_data else None,
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, value: str) -> "ExecutionResult":
        return cls.from_dict(json.loads(value))
