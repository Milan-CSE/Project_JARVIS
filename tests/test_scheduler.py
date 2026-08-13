import unittest

from ai_os.runtime.contracts import ExecutionPlan, ExecutionStep
from ai_os.runtime.scheduler import Scheduler
# from ai_os.runtime.scheduler_impl import DefaultScheduler
from ai_os.runtime.scheduling import DependencyScheduler


class ValidScheduler:

    def get_ready_steps(
        self,
        plan,
        completed_steps,
    ):
        return tuple(plan.steps)


class MissingGetReadyStepsScheduler:
    pass


class SchedulerTests(unittest.TestCase):

    def test_valid_implementation_matches_protocol(self):
        scheduler = ValidScheduler()

        self.assertIsInstance(
            scheduler,
            Scheduler,
        )

    def test_invalid_scheduler_rejected(self):
        scheduler = MissingGetReadyStepsScheduler()

        self.assertFalse(
            isinstance(
                scheduler,
                Scheduler,
            )
        )

    def test_scheduler_is_structural_contract(self):
        scheduler = ValidScheduler()

        self.assertIsInstance(
            scheduler,
            Scheduler,
        )

        self.assertNotIn(
            Scheduler,
            ValidScheduler.__bases__,
        )


    def test_scheduler_does_not_require_task_registry(self):
        scheduler = DependencyScheduler()

        self.assertFalse(
            hasattr(scheduler, "task_registry")
        )

        self.assertFalse(
            hasattr(scheduler, "registry")
        )


    def test_scheduler_does_not_require_engine(self):
        scheduler = DependencyScheduler()

        self.assertFalse(
            hasattr(scheduler, "engine")
        )


    def test_scheduler_does_not_require_intelligence(self):
        scheduler = DependencyScheduler()

        self.assertFalse(
            hasattr(scheduler, "reason")
        )

        self.assertFalse(
            hasattr(scheduler, "think")
        )


    def test_get_ready_steps_accepts_execution_plan(self):
        scheduler = ValidScheduler()

        step = ExecutionStep(
            step_id="step:test",
            capability="test.capability",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step],
        )

        result = scheduler.get_ready_steps(
            plan,
            set(),
        )

        self.assertIsInstance(
            result,
            tuple,
        )

    def test_scheduler_is_stateless(self):
        scheduler = DependencyScheduler()

        first = ExecutionStep(
            step_id="step:a",
            capability="test.a",
        )

        second = ExecutionStep(
            step_id="step:b",
            capability="test.b",
            dependencies=("step:a",),
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[first, second],
        )

        self.assertEqual(
            scheduler.get_ready_steps(
                plan,
                {"step:a"},
            ),
            (second,),
        )

        self.assertEqual(
            scheduler.get_ready_steps(
                plan,
                set(),
            ),
            (first,),
        )

    def test_get_ready_steps_returns_execution_steps(self):
        scheduler = ValidScheduler()

        step = ExecutionStep(
            step_id="step:test",
            capability="test.capability",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step],
        )

        result = scheduler.get_ready_steps(
            plan,
            set(),
        )

        self.assertEqual(
            result,
            (step,),
        )

    def test_scheduler_does_not_execute_tasks(self):
        scheduler = ValidScheduler()

        step = ExecutionStep(
            step_id="step:test",
            capability="test.capability",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step],
        )

        scheduler.get_ready_steps(
            plan,
            set(),
        )

        self.assertFalse(
            hasattr(scheduler, "execute")
        )

    def test_scheduler_does_not_mutate_plan(self):
        scheduler = ValidScheduler()

        step = ExecutionStep(
            step_id="step:test",
            capability="test.capability",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step],
        )

        original_steps = plan.steps

        scheduler.get_ready_steps(
            plan,
            set(),
        )

        self.assertEqual(
            plan.steps,
            original_steps,
        )

    def test_no_dependencies_are_ready(self):
        scheduler = DependencyScheduler()

        step = ExecutionStep(
            step_id="step:a",
            capability="test.a",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step],
        )

        result = scheduler.get_ready_steps(plan, set())

        self.assertEqual(result, (step,))

    def test_completed_step_is_not_ready(self):
        scheduler = DependencyScheduler()

        step = ExecutionStep(
            step_id="step:a",
            capability="test.a",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step],
        )

        result = scheduler.get_ready_steps(
            plan,
            {"step:a"},
        )

        self.assertEqual(
            result,
            (),
        )

    def test_dependency_must_be_completed(self):
        scheduler = DependencyScheduler()

        first = ExecutionStep(
            step_id="step:a",
            capability="test.a",
        )

        second = ExecutionStep(
            step_id="step:b",
            capability="test.b",
            dependencies=("step:a",),
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[first, second],
        )

        result = scheduler.get_ready_steps(
            plan,
            set(),
        )

        self.assertEqual(
            result,
            (first,),
        )

        result = scheduler.get_ready_steps(
            plan,
            {"step:a"},
        )

        self.assertEqual(
            result,
            (second,),
        )

    def test_independent_ready_steps_are_returned_together(self):
        scheduler = DependencyScheduler()

        first = ExecutionStep(
            step_id="step:a",
            capability="test.a",
        )

        second = ExecutionStep(
            step_id="step:b",
            capability="test.b",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[first, second],
        )

        result = scheduler.get_ready_steps(plan, set())

        self.assertEqual(
            result,
            (first, second),
        )

    def test_dependency_scheduler_matches_protocol(self):
        scheduler = DependencyScheduler()

        self.assertIsInstance(
            scheduler,
            Scheduler,
        )

    def test_root_step_is_ready(self):
        scheduler = DependencyScheduler()

        step = ExecutionStep(
            step_id="step:a",
            capability="test.a",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step],
        )

        result = scheduler.get_ready_steps(
            plan,
            set(),
        )

        self.assertEqual(
            result,
            (step,),
        )

    def test_all_dependencies_must_be_completed(self):
        scheduler = DependencyScheduler()

        first = ExecutionStep(
            step_id="step:a",
            capability="test.a",
        )

        second = ExecutionStep(
            step_id="step:b",
            capability="test.b",
        )

        third = ExecutionStep(
            step_id="step:c",
            capability="test.c",
            dependencies=(
                "step:a",
                "step:b",
            ),
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[
                first,
                second,
                third,
            ],
        )

        result = scheduler.get_ready_steps(
            plan,
            {"step:a"},
        )

        self.assertEqual(
            result,
            (second,),
        )

        result = scheduler.get_ready_steps(
            plan,
            {"step:a", "step:b"},
        )

        self.assertEqual(
            result,
            (third,),
        )

    def test_parallel_branches_become_ready_together(self):
        scheduler = DependencyScheduler()

        root = ExecutionStep(
            step_id="step:a",
            capability="test.a",
        )

        branch_one = ExecutionStep(
            step_id="step:b",
            capability="test.b",
            dependencies=("step:a",),
        )

        branch_two = ExecutionStep(
            step_id="step:c",
            capability="test.c",
            dependencies=("step:a",),
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[
                root,
                branch_one,
                branch_two,
            ],
        )

        result = scheduler.get_ready_steps(
            plan,
            {"step:a"},
        )

        self.assertEqual(
            result,
            (
                branch_one,
                branch_two,
            ),
        )

    def test_multi_level_chain_unlocks_one_step_at_a_time(self):
        scheduler = DependencyScheduler()

        first = ExecutionStep(
            step_id="step:a",
            capability="test.a",
        )

        second = ExecutionStep(
            step_id="step:b",
            capability="test.b",
            dependencies=("step:a",),
        )

        third = ExecutionStep(
            step_id="step:c",
            capability="test.c",
            dependencies=("step:b",),
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[
                first,
                second,
                third,
            ],
        )

        self.assertEqual(
            scheduler.get_ready_steps(
                plan,
                set(),
            ),
            (first,),
        )

        self.assertEqual(
            scheduler.get_ready_steps(
                plan,
                {"step:a"},
            ),
            (second,),
        )

        self.assertEqual(
            scheduler.get_ready_steps(
                plan,
                {"step:a", "step:b"},
            ),
            (third,),
        )

    def test_ready_steps_preserve_plan_order(self):
        scheduler = DependencyScheduler()

        third = ExecutionStep(
            step_id="step:c",
            capability="test.c",
        )

        first = ExecutionStep(
            step_id="step:a",
            capability="test.a",
        )

        second = ExecutionStep(
            step_id="step:b",
            capability="test.b",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[
                third,
                first,
                second,
            ],
        )

        result = scheduler.get_ready_steps(
            plan,
            set(),
        )

        self.assertEqual(
            result,
            (
                third,
                first,
                second,
            ),
        )

    def test_invalid_plan_rejected(self):
        scheduler = DependencyScheduler()

        with self.assertRaises(TypeError):
            scheduler.get_ready_steps(
                object(),
                set(),
            )

    def test_invalid_completed_steps_rejected(self):
        scheduler = DependencyScheduler()

        step = ExecutionStep(
            step_id="step:a",
            capability="test.a",
        )

        plan = ExecutionPlan(
            plan_id="plan:test",
            steps=[step],
        )

        with self.assertRaises(TypeError):
            scheduler.get_ready_steps(
                plan,
                {"step:a", 123},
            )
    

if __name__ == "__main__":
    unittest.main(verbosity=2)