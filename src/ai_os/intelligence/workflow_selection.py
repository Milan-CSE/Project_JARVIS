from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from ai_os.intelligence.plan_validation import (
    PlanValidationResult,
    PlanValidationStatus,
)
from ai_os.runtime.contracts import ExecutionPlan
from ai_os.runtime.workflows.workflow import Workflow


class WorkflowSelectionStatus(str, Enum):
    SELECTED = "selected"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class WorkflowSelectionResult:
    """Immutable result of the 9.7 Workflow Selection stage."""

    status: WorkflowSelectionStatus
    plan: ExecutionPlan
    selected_workflow: Workflow | None = None
    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            WorkflowSelectionStatus,
        ):
            object.__setattr__(
                self,
                "status",
                WorkflowSelectionStatus(self.status),
            )

        if not isinstance(
            self.plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "plan must be an ExecutionPlan"
            )

        if self.selected_workflow is not None and not isinstance(
            self.selected_workflow,
            Workflow,
        ):
            raise TypeError(
                "selected_workflow must implement Workflow"
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
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

        if (
            self.status is WorkflowSelectionStatus.SELECTED
            and self.selected_workflow is None
        ):
            raise ValueError(
                "SELECTED result requires a selected_workflow"
            )

        if (
            self.status is not WorkflowSelectionStatus.SELECTED
            and self.selected_workflow is not None
        ):
            raise ValueError(
                "non-selected result cannot contain "
                "a selected_workflow"
            )


@runtime_checkable
class WorkflowSelectorContract(Protocol):
    """
    9.7 structural contract.

    Selection is identity/routing only.
    It does not execute or build the workflow.
    """

    def select(
        self,
        plan: ExecutionPlan,
        workflows: Iterable[Workflow],
        requested_workflow_id: str | None = None,
    ) -> WorkflowSelectionResult:
        ...


class DefaultWorkflowSelector:
    """
    Deterministic identity-based workflow selector.

    Selection policy:

    1. An explicitly supplied workflow_id wins.
    2. Otherwise plan.metadata["workflow_id"] is used when present.
    3. With no requested id:
       - zero workflows -> NOT_FOUND
       - exactly one workflow -> SELECTED
       - more than one -> AMBIGUOUS
    4. Duplicate workflow IDs are never resolved by version or
       iteration order; they are AMBIGUOUS.
    """

    def select(
        self,
        plan: ExecutionPlan,
        workflows: Iterable[Workflow],
        requested_workflow_id: str | None = None,
    ) -> WorkflowSelectionResult:
        if not isinstance(
            plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "plan must be an ExecutionPlan"
            )

        candidates = tuple(workflows)

        for workflow in candidates:
            if not isinstance(
                workflow,
                Workflow,
            ):
                raise TypeError(
                    "all workflows must implement Workflow"
                )

        requested_id = requested_workflow_id

        if requested_id is not None:
            if not isinstance(
                requested_id,
                str,
            ):
                raise TypeError(
                    "requested_workflow_id must be a string or None"
                )

            if not requested_id.strip():
                raise ValueError(
                    "requested_workflow_id must not be "
                    "empty or whitespace"
                )

        if requested_id is None:
            metadata_id = plan.metadata.get(
                "workflow_id"
            )

            if metadata_id is not None:
                if not isinstance(
                    metadata_id,
                    str,
                ):
                    raise TypeError(
                        "plan.metadata['workflow_id'] "
                        "must be a string"
                    )

                if not metadata_id.strip():
                    raise ValueError(
                        "plan.metadata['workflow_id'] "
                        "must not be empty"
                    )

                requested_id = metadata_id

        if not candidates:
            return WorkflowSelectionResult(
                status=WorkflowSelectionStatus.NOT_FOUND,
                plan=plan,
                metadata={
                    "stage": "workflow_selection",
                    "reason": "no_workflows_available",
                },
            )

        if requested_id is not None:
            matches = tuple(
                workflow
                for workflow in candidates
                if workflow.workflow_id == requested_id
            )

            if not matches:
                return WorkflowSelectionResult(
                    status=WorkflowSelectionStatus.NOT_FOUND,
                    plan=plan,
                    metadata={
                        "stage": "workflow_selection",
                        "reason": "workflow_id_not_found",
                        "workflow_id": requested_id,
                    },
                )

            if len(matches) > 1:
                return WorkflowSelectionResult(
                    status=WorkflowSelectionStatus.AMBIGUOUS,
                    plan=plan,
                    metadata={
                        "stage": "workflow_selection",
                        "reason": "duplicate_workflow_id",
                        "workflow_id": requested_id,
                        "candidate_count": len(matches),
                    },
                )

            return WorkflowSelectionResult(
                status=WorkflowSelectionStatus.SELECTED,
                plan=plan,
                selected_workflow=matches[0],
                metadata={
                    "stage": "workflow_selection",
                    "selection_mode": "explicit_id",
                },
            )

        if len(candidates) == 1:
            return WorkflowSelectionResult(
                status=WorkflowSelectionStatus.SELECTED,
                plan=plan,
                selected_workflow=candidates[0],
                metadata={
                    "stage": "workflow_selection",
                    "selection_mode": "single_candidate",
                },
            )

        distinct_ids = {
            workflow.workflow_id
            for workflow in candidates
        }

        if len(distinct_ids) == 1:
            return WorkflowSelectionResult(
                status=WorkflowSelectionStatus.AMBIGUOUS,
                plan=plan,
                metadata={
                    "stage": "workflow_selection",
                    "reason": "multiple_versions_same_workflow",
                    "workflow_id": next(
                        iter(distinct_ids)
                    ),
                    "candidate_count": len(candidates),
                },
            )

        return WorkflowSelectionResult(
            status=WorkflowSelectionStatus.AMBIGUOUS,
            plan=plan,
            metadata={
                "stage": "workflow_selection",
                "reason": "multiple_workflows_available",
                "candidate_count": len(candidates),
            },
        )


class WorkflowSelectionPipeline:
    """
    9.7 boundary:

        PlanValidationResult
              ↓
        VALID plan only
              ↓
        WorkflowSelectorContract
              ↓
        WorkflowSelectionResult

    This stage does not execute, build, mutate, or replan workflows.
    """

    def __init__(
        self,
        selector: WorkflowSelectorContract | None = None,
    ) -> None:
        if selector is None:
            selector = DefaultWorkflowSelector()

        if not isinstance(
            selector,
            WorkflowSelectorContract,
        ):
            raise TypeError(
                "selector must implement "
                "WorkflowSelectorContract"
            )

        self._selector = selector

    def run(
        self,
        validation: PlanValidationResult,
        workflows: Iterable[Workflow],
        requested_workflow_id: str | None = None,
    ) -> WorkflowSelectionResult:
        if not isinstance(
            validation,
            PlanValidationResult,
        ):
            raise TypeError(
                "validation must be a PlanValidationResult"
            )

        if (
            validation.status
            is not PlanValidationStatus.VALID
        ):
            raise ValueError(
                "workflow selection requires a VALID "
                "PlanValidationResult"
            )

        result = self._selector.select(
            validation.plan,
            workflows,
            requested_workflow_id,
        )

        if not isinstance(
            result,
            WorkflowSelectionResult,
        ):
            raise TypeError(
                "selector must return a "
                "WorkflowSelectionResult"
            )

        if result.plan is not validation.plan:
            raise ValueError(
                "selector must preserve the exact validated plan"
            )

        return result