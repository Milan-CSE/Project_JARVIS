from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from ai_os.runtime.contracts import ExecutionPlan, ExecutionStep


class PlanValidationStatus(str, Enum):
    VALID = "valid"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class PlanValidationIssue:
    """One deterministic plan-validation issue."""

    code: str
    message: str
    field: str | None = None
    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.code, str):
            raise TypeError(
                "code must be a string"
            )

        if not self.code.strip():
            raise ValueError(
                "code must not be empty"
            )

        if not isinstance(self.message, str):
            raise TypeError(
                "message must be a string"
            )

        if not self.message.strip():
            raise ValueError(
                "message must not be empty"
            )

        if self.field is not None:
            if not isinstance(self.field, str):
                raise TypeError(
                    "field must be a string or None"
                )

            if not self.field.strip():
                raise ValueError(
                    "field must not be empty"
                )

        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


@dataclass(frozen=True, slots=True)
class PlanValidationResult:
    """Immutable result of 9.6 plan validation."""

    status: PlanValidationStatus
    plan: ExecutionPlan
    issues: tuple[PlanValidationIssue, ...] = ()
    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            PlanValidationStatus,
        ):
            object.__setattr__(
                self,
                "status",
                PlanValidationStatus(self.status),
            )

        if not isinstance(
            self.plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "plan must be an ExecutionPlan"
            )

        if not isinstance(self.issues, tuple):
            object.__setattr__(
                self,
                "issues",
                tuple(self.issues),
            )

        if not all(
            isinstance(
                issue,
                PlanValidationIssue,
            )
            for issue in self.issues
        ):
            raise TypeError(
                "issues must contain "
                "PlanValidationIssue instances"
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )

        expected_status = (
            PlanValidationStatus.VALID
            if not self.issues
            else PlanValidationStatus.REJECTED
        )

        if self.status is not expected_status:
            raise ValueError(
                "status does not match validation issues"
            )


@runtime_checkable
class PlanValidatorContract(Protocol):
    """Structural contract for 9.6 plan validators."""

    def validate(
        self,
        plan: ExecutionPlan,
    ) -> PlanValidationResult:
        ...


class DefaultPlanValidator:
    """
    Deterministic 9.6 structural/safety validator.

    This class validates only the plan.
    It does not repair, schedule, select, or execute it.
    """

    def validate(
        self,
        plan: ExecutionPlan,
    ) -> PlanValidationResult:
        if not isinstance(
            plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "plan must be an ExecutionPlan"
            )

        issues: list[PlanValidationIssue] = []

        # -------------------------------------------------------------
        # Plan identity
        # -------------------------------------------------------------

        if not isinstance(plan.plan_id, str):
            issues.append(
                PlanValidationIssue(
                    code="INVALID_PLAN_ID",
                    message="plan_id must be a string",
                    field="plan.plan_id",
                )
            )
        elif not plan.plan_id.strip():
            issues.append(
                PlanValidationIssue(
                    code="EMPTY_PLAN_ID",
                    message="plan_id must not be empty",
                    field="plan.plan_id",
                )
            )

        # -------------------------------------------------------------
        # Steps
        # -------------------------------------------------------------

        steps = plan.steps

        if not isinstance(steps, tuple):
            # Existing ExecutionPlan normally guarantees this, but
            # keep the boundary defensive.
            try:
                steps = tuple(steps)
            except TypeError:
                issues.append(
                    PlanValidationIssue(
                        code="INVALID_STEPS",
                        message="steps must be iterable",
                        field="plan.steps",
                    )
                )
                steps = ()

        step_ids: set[str] = set()

        for index, step in enumerate(steps):
            field_prefix = f"plan.steps[{index}]"

            if not isinstance(
                step,
                ExecutionStep,
            ):
                issues.append(
                    PlanValidationIssue(
                        code="INVALID_STEP",
                        message=(
                            "plan step must be an "
                            "ExecutionStep"
                        ),
                        field=field_prefix,
                    )
                )
                continue

            # ---------------------------------------------------------
            # Step ID
            # ---------------------------------------------------------

            step_id = step.step_id

            if not isinstance(step_id, str):
                issues.append(
                    PlanValidationIssue(
                        code="INVALID_STEP_ID",
                        message=(
                            "step_id must be a string"
                        ),
                        field=f"{field_prefix}.step_id",
                    )
                )
            elif not step_id.strip():
                issues.append(
                    PlanValidationIssue(
                        code="EMPTY_STEP_ID",
                        message=(
                            "step_id must not be empty"
                        ),
                        field=f"{field_prefix}.step_id",
                    )
                )
            elif step_id in step_ids:
                issues.append(
                    PlanValidationIssue(
                        code="DUPLICATE_STEP_ID",
                        message=(
                            "step_id must be unique"
                        ),
                        field=f"{field_prefix}.step_id",
                        metadata={
                            "step_id": step_id,
                        },
                    )
                )
            else:
                step_ids.add(step_id)

            # ---------------------------------------------------------
            # Capability
            # ---------------------------------------------------------

            capability = step.capability

            if not isinstance(capability, str):
                issues.append(
                    PlanValidationIssue(
                        code="INVALID_CAPABILITY",
                        message=(
                            "capability must be a string"
                        ),
                        field=(
                            f"{field_prefix}.capability"
                        ),
                    )
                )
            elif not capability.strip():
                issues.append(
                    PlanValidationIssue(
                        code="EMPTY_CAPABILITY",
                        message=(
                            "capability must not be empty"
                        ),
                        field=(
                            f"{field_prefix}.capability"
                        ),
                    )
                )

            # ---------------------------------------------------------
            # Dependencies
            # ---------------------------------------------------------

            dependencies = step.dependencies

            if not isinstance(
                dependencies,
                tuple,
            ):
                try:
                    dependencies = tuple(
                        dependencies
                    )
                except TypeError:
                    issues.append(
                        PlanValidationIssue(
                            code="INVALID_DEPENDENCIES",
                            message=(
                                "dependencies must be "
                                "iterable"
                            ),
                            field=(
                                f"{field_prefix}"
                                ".dependencies"
                            ),
                        )
                    )
                    dependencies = ()

            seen_dependencies: set[str] = set()

            for dependency in dependencies:
                if not isinstance(
                    dependency,
                    str,
                ):
                    issues.append(
                        PlanValidationIssue(
                            code="INVALID_DEPENDENCY",
                            message=(
                                "dependency must be "
                                "a string"
                            ),
                            field=(
                                f"{field_prefix}"
                                ".dependencies"
                            ),
                        )
                    )
                    continue

                if not dependency.strip():
                    issues.append(
                        PlanValidationIssue(
                            code="EMPTY_DEPENDENCY",
                            message=(
                                "dependency must not "
                                "be empty"
                            ),
                            field=(
                                f"{field_prefix}"
                                ".dependencies"
                            ),
                        )
                    )
                    continue

                if dependency in seen_dependencies:
                    issues.append(
                        PlanValidationIssue(
                            code="DUPLICATE_DEPENDENCY",
                            message=(
                                "dependency must appear "
                                "only once"
                            ),
                            field=(
                                f"{field_prefix}"
                                ".dependencies"
                            ),
                            metadata={
                                "dependency": dependency,
                            },
                        )
                    )

                seen_dependencies.add(dependency)

                if (
                    isinstance(step_id, str)
                    and dependency == step_id
                ):
                    issues.append(
                        PlanValidationIssue(
                            code="SELF_DEPENDENCY",
                            message=(
                                "step cannot depend "
                                "on itself"
                            ),
                            field=(
                                f"{field_prefix}"
                                ".dependencies"
                            ),
                        )
                    )

        # -------------------------------------------------------------
        # Dependency references
        # -------------------------------------------------------------

        for index, step in enumerate(steps):
            if not isinstance(
                step,
                ExecutionStep,
            ):
                continue

            for dependency in step.dependencies:
                if not isinstance(
                    dependency,
                    str,
                ):
                    continue

                if dependency not in step_ids:
                    issues.append(
                        PlanValidationIssue(
                            code="UNKNOWN_DEPENDENCY",
                            message=(
                                "dependency references "
                                "an unknown step"
                            ),
                            field=(
                                f"plan.steps[{index}]"
                                ".dependencies"
                            ),
                            metadata={
                                "dependency": dependency,
                            },
                        )
                    )

        # -------------------------------------------------------------
        # Cycle detection
        # -------------------------------------------------------------

        if not issues:
            adjacency: dict[str, tuple[str, ...]] = {
                step.step_id: tuple(step.dependencies)
                for step in steps
                if isinstance(
                    step,
                    ExecutionStep,
                )
            }

            visiting: set[str] = set()
            visited: set[str] = set()

            def visit(step_id: str) -> bool:
                if step_id in visiting:
                    return True

                if step_id in visited:
                    return False

                visiting.add(step_id)

                for dependency in adjacency.get(
                    step_id,
                    (),
                ):
                    if visit(dependency):
                        return True

                visiting.remove(step_id)
                visited.add(step_id)

                return False

            for step_id in adjacency:
                if visit(step_id):
                    issues.append(
                        PlanValidationIssue(
                            code="DEPENDENCY_CYCLE",
                            message=(
                                "execution plan contains "
                                "a dependency cycle"
                            ),
                            field="plan.steps",
                        )
                    )
                    break

        status = (
            PlanValidationStatus.VALID
            if not issues
            else PlanValidationStatus.REJECTED
        )

        return PlanValidationResult(
            status=status,
            plan=plan,
            issues=tuple(issues),
            metadata={
                "stage": "plan_validation",
            },
        )


class PlanValidationPipeline:
    """
    9.6 validation boundary.

        ExecutionPlan
             ↓
        PlanValidatorContract
             ↓
        PlanValidationResult
    """

    def __init__(
        self,
        validator: PlanValidatorContract | None = None,
    ) -> None:
        if validator is None:
            validator = DefaultPlanValidator()

        if not isinstance(
            validator,
            PlanValidatorContract,
        ):
            raise TypeError(
                "validator must implement "
                "PlanValidatorContract"
            )

        self._validator = validator

    def run(
        self,
        plan: ExecutionPlan,
    ) -> PlanValidationResult:
        if not isinstance(
            plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "plan must be an ExecutionPlan"
            )

        result = self._validator.validate(plan)

        if not isinstance(
            result,
            PlanValidationResult,
        ):
            raise TypeError(
                "validator must return "
                "PlanValidationResult"
            )

        if result.plan is not plan:
            raise ValueError(
                "validator must preserve the exact plan"
            )

        return result