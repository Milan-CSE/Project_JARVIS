import unittest

from ai_os.runtime.contracts import ExecutionStep
from ai_os.runtime.workflows import (
    DefaultWorkflow,
    Workflow,
)


class ValidWorkflow:

    @property
    def workflow_id(self):
        return "workflow.test"

    @property
    def version(self):
        return "1.0"

    @property
    def metadata(self):
        return {}

    def build_steps(self, parameters):
        return (
            ExecutionStep(
                step_id="step:a",
                capability="test.action",
            ),
        )


class MissingBuildStepsWorkflow:
    @property
    def workflow_id(self):
        return "workflow.test"

    @property
    def version(self):
        return "1.0"

    @property
    def metadata(self):
        return {}


class WorkflowTests(unittest.TestCase):

    def test_valid_implementation_matches_protocol(self):
        workflow = ValidWorkflow()

        self.assertIsInstance(
            workflow,
            Workflow,
        )

    def test_invalid_workflow_rejected(self):
        workflow = MissingBuildStepsWorkflow()

        self.assertFalse(
            isinstance(
                workflow,
                Workflow,
            )
        )

    def test_default_workflow_is_immutable(self):
        step = ExecutionStep(
            step_id="step:a",
            capability="test.action",
        )

        workflow = DefaultWorkflow(
            workflow_id="workflow.test",
            version="1.0",
            steps=(step,),
        )

        with self.assertRaises(AttributeError):
            workflow.workflow_id = "changed"

    def test_default_workflow_preserves_steps(self):
        step = ExecutionStep(
            step_id="step:a",
            capability="test.action",
        )

        workflow = DefaultWorkflow(
            workflow_id="workflow.test",
            version="1.0",
            steps=(step,),
        )

        result = workflow.build_steps({})

        self.assertEqual(
            result,
            (step,),
        )

    def test_workflow_does_not_require_engine(self):
        workflow = ValidWorkflow()

        self.assertFalse(
            hasattr(workflow, "engine")
        )

        self.assertFalse(
            hasattr(workflow, "route")
        )

    def test_workflow_does_not_require_intelligence(self):
        workflow = ValidWorkflow()

        self.assertFalse(
            hasattr(workflow, "reason")
        )

        self.assertFalse(
            hasattr(workflow, "think")
        )

    def test_workflow_does_not_require_task_registry(self):
        workflow = ValidWorkflow()

        self.assertFalse(
            hasattr(workflow, "registry")
        )

        self.assertFalse(
            hasattr(workflow, "task_registry")
        )

    def test_workflow_does_not_execute_tasks(self):
        workflow = ValidWorkflow()

        self.assertFalse(
            hasattr(workflow, "execute")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)