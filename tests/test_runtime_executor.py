import unittest

from ai_os.runtime import RuntimeExecutor
from ai_os.runtime.contracts import (
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
    ExecutionStep,
)

from ai_os.runtime.executor_impl import (
    DefaultRuntimeExecutor,
    ExecutionStalledError,
)
from ai_os.runtime.scheduler import Scheduler
from ai_os.runtime.scheduler_impl import DefaultScheduler
from ai_os.runtime.tasks import (
    DefaultTaskExecutor,
    DefaultTaskRegistry,
)

from ai_os.runtime.scheduling import DependencyScheduler
from ai_os.runtime.cancellation import CancellationSource


class ValidExecutor:

    def execute(self, plan):
        return ExecutionResult(
            plan_id=plan.plan_id,
            step_id=plan.steps[0].step_id,
            status=ExecutionStatus.COMPLETED,
            output={},
        )


class MissingExecuteExecutor:
    pass


def create_plan():
    step = ExecutionStep(
        step_id="step:test",
        capability="test.capability",
    )

    return ExecutionPlan(
        plan_id="plan:test",
        steps=[step],
    )


class RuntimeExecutorTests(unittest.TestCase):

    def test_valid_implementation_matches_protocol(self):
        executor = ValidExecutor()

        self.assertIsInstance(
            executor,
            RuntimeExecutor,
        )

    def test_invalid_executor_rejected(self):
        executor = MissingExecuteExecutor()

        self.assertFalse(
            isinstance(
                executor,
                RuntimeExecutor,
            )
        )

    def test_execute_returns_execution_result(self):
        executor = ValidExecutor()

        plan = create_plan()

        result = executor.execute(plan)

        self.assertIsInstance(
            result,
            ExecutionResult,
        )

    def test_execute_accepts_execution_plan(self):
        executor = ValidExecutor()

        plan = create_plan()

        result = executor.execute(plan)

        self.assertEqual(
            result.status,
            ExecutionStatus.COMPLETED,
        )

    def test_executor_does_not_require_engine(self):
        executor = ValidExecutor()

        self.assertFalse(
            hasattr(executor, "engine")
        )

        self.assertFalse(
            hasattr(executor, "route")
        )

    def test_executor_does_not_require_intelligence(self):
        executor = ValidExecutor()

        self.assertFalse(
            hasattr(executor, "reason")
        )

        self.assertFalse(
            hasattr(executor, "think")
        )

        self.assertFalse(
            hasattr(executor, "plan")
        )

    def test_executor_is_structural_contract(self):
        executor = ValidExecutor()

        self.assertIsInstance(
            executor,
            RuntimeExecutor,
        )

        self.assertNotIn(
            RuntimeExecutor,
            ValidExecutor.__bases__,
        )

    def test_executor_result_is_runtime_result(self):
        executor = ValidExecutor()

        result = executor.execute(
            create_plan()
        )

        self.assertIsInstance(
            result,
            ExecutionResult,
        )

        self.assertNotIsInstance(
            result,
            dict,
        )

    def test_concrete_executor_accepts_scheduler_and_task_executor(self):
        registry = DefaultTaskRegistry()

        class ValidTask:

            @property
            def capability(self):
                return "test.capability"

            def execute(self, step):
                return {"ok": True}

        registry.register(ValidTask())
        registry.freeze()

        task_executor = DefaultTaskExecutor(registry)
        scheduler = DefaultScheduler()

        executor = DefaultRuntimeExecutor(
            scheduler,
            task_executor,
        )

        self.assertIsInstance(
            executor,
            RuntimeExecutor,
        )

    def test_invalid_scheduler_rejected(self):
        class BadScheduler:
            pass

        registry = DefaultTaskRegistry()
        task_executor = DefaultTaskExecutor(registry)

        with self.assertRaises(TypeError):
            DefaultRuntimeExecutor(
                BadScheduler(),
                task_executor,
            )

    def test_invalid_task_executor_rejected(self):
        scheduler = DefaultScheduler()

        with self.assertRaises(TypeError):
            DefaultRuntimeExecutor(
                scheduler,
                object(),
            )

    def test_single_step_execution(self):
        class TestTask:

            @property
            def capability(self):
                return "test.capability"

            def execute(self, step):
                return {"value": 42}

        registry = DefaultTaskRegistry()
        registry.register(TestTask())
        registry.freeze()

        task_executor = DefaultTaskExecutor(registry)

        executor = DefaultRuntimeExecutor(
            DefaultScheduler(),
            task_executor,
        )

        step = ExecutionStep(
            step_id="step:a",
            capability="test.capability",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step],
        )

        results = executor.execute(plan)

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0].plan_id,
            "plan:test",
        )

        self.assertEqual(
            results[0].step_id,
            "step:a",
        )

        self.assertEqual(
            results[0].status,
            ExecutionStatus.COMPLETED,
        )

        self.assertEqual(
            results[0].output,
            {"value": 42},
        )

    def test_independent_steps_all_execute(self):
        executed = []

        class TestTask:

            @property
            def capability(self):
                return "test.capability"

            def execute(self, step):
                executed.append(step.step_id)
                return step.step_id

        registry = DefaultTaskRegistry()
        registry.register(TestTask())
        registry.freeze()

        executor = DefaultRuntimeExecutor(
            DefaultScheduler(),
            DefaultTaskExecutor(registry),
        )

        first = ExecutionStep(
            step_id="step:a",
            capability="test.capability",
        )

        second = ExecutionStep(
            step_id="step:b",
            capability="test.capability",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[first, second],
        )

        results = executor.execute(plan)

        self.assertEqual(
            executed,
            ["step:a", "step:b"],
        )

        self.assertEqual(
            tuple(result.step_id for result in results),
            ("step:a", "step:b"),
        )

    def test_result_order_follows_plan_order(self):
        class TestTask:

            @property
            def capability(self):
                return "test.capability"

            def execute(self, step):
                return step.step_id

        registry = DefaultTaskRegistry()
        registry.register(TestTask())
        registry.freeze()

        executor = DefaultRuntimeExecutor(
            DefaultScheduler(),
            DefaultTaskExecutor(registry),
        )

        step_b = ExecutionStep(
            step_id="step:b",
            capability="test.capability",
        )

        step_a = ExecutionStep(
            step_id="step:a",
            capability="test.capability",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step_b, step_a],
        )

        results = executor.execute(plan)

        self.assertEqual(
            tuple(result.step_id for result in results),
            ("step:b", "step:a"),
        )

    def test_executor_state_does_not_leak_between_runs(self):
        class TestTask:

            @property
            def capability(self):
                return "test.capability"

            def execute(self, step):
                return step.step_id

        registry = DefaultTaskRegistry()
        registry.register(TestTask())
        registry.freeze()

        executor = DefaultRuntimeExecutor(
            DefaultScheduler(),
            DefaultTaskExecutor(registry),
        )

        first_step = ExecutionStep(
            step_id="step:first",
            capability="test.capability",
        )

        second_step = ExecutionStep(
            step_id="step:second",
            capability="test.capability",
        )

        first_plan = ExecutionPlan(
            plan_id="plan:first",
            steps=[first_step],
        )

        second_plan = ExecutionPlan(
            plan_id="plan:second",
            steps=[second_step],
        )

        first_results = executor.execute(first_plan)
        second_results = executor.execute(second_plan)

        self.assertEqual(
            tuple(result.step_id for result in first_results),
            ("step:first",),
        )

        self.assertEqual(
            tuple(result.step_id for result in second_results),
            ("step:second",),
        )

    def test_scheduler_stall_is_rejected(self):
        class StalledScheduler:

            def get_ready_steps(
                self,
                plan,
                completed_steps,
            ):
                return ()

        class TestTaskExecutor:

            def execute_step(self, step):
                return {"ok": True}

        executor = DefaultRuntimeExecutor(
            StalledScheduler(),
            TestTaskExecutor(),
        )

        step = ExecutionStep(
            step_id="step:a",
            capability="test.capability",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step],
        )

        with self.assertRaises(
            ExecutionStalledError
        ):
            executor.execute(plan)

    def test_dependency_chain_executes_through_runtime(self):
        executed = []

        class TestTask:

            @property
            def capability(self):
                return "test.capability"

            def execute(self, step):
                executed.append(step.step_id)
                return step.step_id

        registry = DefaultTaskRegistry()
        registry.register(TestTask())
        registry.freeze()

        executor = DefaultRuntimeExecutor(
            DependencyScheduler(),
            DefaultTaskExecutor(registry),
        )

        first = ExecutionStep(
            step_id="step:a",
            capability="test.capability",
        )

        second = ExecutionStep(
            step_id="step:b",
            capability="test.capability",
            dependencies=("step:a",),
        )

        third = ExecutionStep(
            step_id="step:c",
            capability="test.capability",
            dependencies=("step:b",),
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[first, second, third],
        )

        results = executor.execute(plan)

        self.assertEqual(
            executed,
            [
                "step:a",
                "step:b",
                "step:c",
            ],
        )

        self.assertEqual(
            tuple(result.step_id for result in results),
            (
                "step:a",
                "step:b",
                "step:c",
            ),
        )

    def test_task_failure_produces_failed_result(self):
        class FailingTask:

            @property
            def capability(self):
                return "failing.capability"

            def execute(self, step):
                raise RuntimeError("secret/internal message")

        registry = DefaultTaskRegistry()
        registry.register(FailingTask())
        registry.freeze()

        executor = DefaultRuntimeExecutor(
            DependencyScheduler(),
            DefaultTaskExecutor(registry),
        )

        step = ExecutionStep(
            step_id="step:a",
            capability="failing.capability",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step],
        )

        results = executor.execute(plan)

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0].status,
            ExecutionStatus.FAILED,
        )

        self.assertIsNotNone(
            results[0].error,
        )

        self.assertEqual(
            results[0].error.code,
            "TASK_EXECUTION_FAILED",
        )

        self.assertEqual(
            results[0].error.details["exception_type"],
            "RuntimeError",
        )

        self.assertNotIn(
            "secret/internal message",
            results[0].error.message,
        )

    def test_failed_dependency_cancels_dependent(self):
        class TestTask:

            def __init__(self, capability, failing=False):
                self._capability = capability
                self._failing = failing

            @property
            def capability(self):
                return self._capability

            def execute(self, step):
                if self._failing:
                    raise RuntimeError("failed")
                return {"ok": True}

        registry = DefaultTaskRegistry()
        registry.register(
            TestTask("task.a", failing=True)
        )
        registry.register(
            TestTask("task.b")
        )
        registry.freeze()

        executor = DefaultRuntimeExecutor(
            DependencyScheduler(),
            DefaultTaskExecutor(registry),
        )

        first = ExecutionStep(
            step_id="step:a",
            capability="task.a",
        )

        second = ExecutionStep(
            step_id="step:b",
            capability="task.b",
            dependencies=("step:a",),
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[first, second],
        )

        results = executor.execute(plan)

        self.assertEqual(
            results[0].status,
            ExecutionStatus.FAILED,
        )

        self.assertEqual(
            results[1].status,
            ExecutionStatus.CANCELLED,
        )

        self.assertEqual(
            results[1].metadata["termination_reason"],
            "dependency_failed",
        )

    def test_independent_branch_continues_after_failure(self):
        executed = []

        class TestTask:

            def __init__(self, capability, failing=False):
                self._capability = capability
                self._failing = failing

            @property
            def capability(self):
                return self._capability

            def execute(self, step):
                if self._failing:
                    raise RuntimeError("failed")

                executed.append(step.step_id)
                return step.step_id

        registry = DefaultTaskRegistry()
        registry.register(
            TestTask("test.failing", failing=True)
        )
        registry.register(
            TestTask("test.independent")
        )
        registry.freeze()

        executor = DefaultRuntimeExecutor(
            DependencyScheduler(),
            DefaultTaskExecutor(registry),
        )

        failing = ExecutionStep(
            step_id="step:failing",
            capability="test.failing",
        )

        independent = ExecutionStep(
            step_id="step:independent",
            capability="test.independent",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[
                failing,
                independent,
            ],
        )

        results = executor.execute(plan)

        self.assertEqual(
            results[0].status,
            ExecutionStatus.FAILED,
        )

        self.assertEqual(
            results[1].status,
            ExecutionStatus.COMPLETED,
        )

        self.assertEqual(
            executed,
            ["step:independent"],
        )

    def test_failure_propagates_transitively(self):
        class TestTask:

            def __init__(self, capability, failing=False):
                self._capability = capability
                self._failing = failing

            @property
            def capability(self):
                return self._capability

            def execute(self, step):
                if self._failing:
                    raise RuntimeError("failed")
                return step.step_id

        registry = DefaultTaskRegistry()

        registry.register(
            TestTask("task.a", failing=True)
        )
        registry.register(
            TestTask("task.b")
        )
        registry.register(
            TestTask("task.c")
        )

        registry.freeze()

        executor = DefaultRuntimeExecutor(
            DependencyScheduler(),
            DefaultTaskExecutor(registry),
        )

        a = ExecutionStep(
            step_id="step:a",
            capability="task.a",
        )

        b = ExecutionStep(
            step_id="step:b",
            capability="task.b",
            dependencies=("step:a",),
        )

        c = ExecutionStep(
            step_id="step:c",
            capability="task.c",
            dependencies=("step:b",),
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[a, b, c],
        )

        results = executor.execute(plan)

        self.assertEqual(
            tuple(result.status for result in results),
            (
                ExecutionStatus.FAILED,
                ExecutionStatus.CANCELLED,
                ExecutionStatus.CANCELLED,
            ),
        )

    def test_multiple_dependents_are_cancelled(self):
        class TestTask:

            @property
            def capability(self):
                return "task"

            def execute(self, step):
                raise RuntimeError("failed")

        class NoopTask:

            @property
            def capability(self):
                return "noop"

            def execute(self, step):
                raise AssertionError(
                    "dependent task must not execute"
                )

        registry = DefaultTaskRegistry()
        registry.register(
            TestTask()
        )

        registry.register(
            type(
                "SecondFailingTask",
                (),
                {
                    "capability": property(
                        lambda self: "task2"
                    ),
                    "execute": lambda self, step:
                        (_ for _ in ()).throw(
                            RuntimeError("failed")
                        ),
                },
            )()
        )

        registry.register(NoopTask())
        registry.freeze()

    def test_cancellation_before_execution_cancels_all_steps(self):
        source = CancellationSource()

        source.cancel()

        executed = []

        class TestTask:

            @property
            def capability(self):
                return "test.capability"

            def execute(self, step):
                executed.append(step.step_id)
                return {"ok": True}

        registry = DefaultTaskRegistry()
        registry.register(TestTask())
        registry.freeze()

        executor = DefaultRuntimeExecutor(
            DependencyScheduler(),
            DefaultTaskExecutor(registry),
        )

        first = ExecutionStep(
            step_id="step:a",
            capability="test.capability",
        )

        second = ExecutionStep(
            step_id="step:b",
            capability="test.capability",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[first, second],
        )

        results = executor.execute(
            plan,
            source.token,
        )

        self.assertEqual(
            executed,
            [],
        )

        self.assertEqual(
            tuple(
                result.status
                for result in results
            ),
            (
                ExecutionStatus.CANCELLED,
                ExecutionStatus.CANCELLED,
            ),
        )

    def test_cancellation_after_completed_step_cancels_remaining_steps(self):
        source = CancellationSource()
        executed = []

        class TestTask:

            @property
            def capability(self):
                return "test.capability"

            def execute(self, step):
                executed.append(step.step_id)

                if step.step_id == "step:a":
                    source.cancel()

                return step.step_id

        registry = DefaultTaskRegistry()
        registry.register(TestTask())
        registry.freeze()

        executor = DefaultRuntimeExecutor(
            DependencyScheduler(),
            DefaultTaskExecutor(registry),
        )

        first = ExecutionStep(
            step_id="step:a",
            capability="test.capability",
        )

        second = ExecutionStep(
            step_id="step:b",
            capability="test.capability",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[first, second],
        )

        results = executor.execute(
            plan,
            source.token,
        )

        self.assertEqual(
            executed,
            ["step:a"],
        )

        self.assertEqual(
            results[0].status,
            ExecutionStatus.COMPLETED,
        )

        self.assertEqual(
            results[1].status,
            ExecutionStatus.CANCELLED,
        )

    def test_cancellation_after_completion_has_no_effect(self):
        source = CancellationSource()

        class TestTask:

            @property
            def capability(self):
                return "test.capability"

            def execute(self, step):
                return {"ok": True}

        registry = DefaultTaskRegistry()
        registry.register(TestTask())
        registry.freeze()

        executor = DefaultRuntimeExecutor(
            DependencyScheduler(),
            DefaultTaskExecutor(registry),
        )

        step = ExecutionStep(
            step_id="step:a",
            capability="test.capability",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step],
        )

        results = executor.execute(
            plan,
            source.token,
        )

        source.cancel()

        self.assertEqual(
            results[0].status,
            ExecutionStatus.COMPLETED,
        )

    

if __name__ == "__main__":
    unittest.main(verbosity=2)