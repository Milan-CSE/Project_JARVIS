import unittest

from ai_os.intelligence import (
    IntentCandidate,
    ReasoningResolutionStatus,
    ReasoningResolver,
    ReasoningResult,
)


class ReasoningResolutionTests(unittest.TestCase):

    def test_single_candidate_is_ready(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(
                    goal="generate_report",
                ),
            ),
        )

        resolution = ReasoningResolver().resolve(result)

        self.assertEqual(
            resolution.status,
            ReasoningResolutionStatus.READY,
        )

        self.assertEqual(
            resolution.candidate_index,
            0,
        )

    def test_zero_candidates_are_unresolved(self):
        resolution = ReasoningResolver().resolve(
            ReasoningResult()
        )

        self.assertEqual(
            resolution.status,
            ReasoningResolutionStatus.UNRESOLVED,
        )

        self.assertIsNone(
            resolution.candidate_index,
        )

        self.assertEqual(
            resolution.issues[0].code,
            "NO_INTENT_CANDIDATE",
        )

    def test_multiple_candidates_require_clarification(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(goal="sales_report"),
                IntentCandidate(goal="financial_report"),
            ),
        )

        resolution = ReasoningResolver().resolve(result)

        self.assertEqual(
            resolution.status,
            ReasoningResolutionStatus.CLARIFICATION_REQUIRED,
        )

        self.assertIsNone(
            resolution.candidate_index,
        )

        self.assertEqual(
            resolution.issues[0].code,
            "MULTIPLE_INTENT_CANDIDATES",
        )

    def test_explicit_selection_resolves_multiple_candidates(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(goal="sales_report"),
                IntentCandidate(goal="financial_report"),
            ),
        )

        resolution = ReasoningResolver().resolve(
            result,
            candidate_index=1,
        )

        self.assertEqual(
            resolution.status,
            ReasoningResolutionStatus.READY,
        )

        self.assertEqual(
            resolution.candidate_index,
            1,
        )

    def test_negative_index_rejected(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(goal="report"),
            ),
        )

        with self.assertRaises(IndexError):
            ReasoningResolver().resolve(
                result,
                candidate_index=-1,
            )

    def test_out_of_range_index_rejected(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(goal="report"),
            ),
        )

        with self.assertRaises(IndexError):
            ReasoningResolver().resolve(
                result,
                candidate_index=1,
            )

    def test_bool_index_rejected(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(goal="report"),
            ),
        )

        with self.assertRaises(TypeError):
            ReasoningResolver().resolve(
                result,
                candidate_index=True,
            )

    def test_invalid_index_type_rejected(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(goal="report"),
            ),
        )

        with self.assertRaises(TypeError):
            ReasoningResolver().resolve(
                result,
                candidate_index="0",
            )

    def test_invalid_result_rejected(self):
        with self.assertRaises(TypeError):
            ReasoningResolver().resolve(
                "invalid"
            )

    def test_ambiguity_does_not_automatically_block_single_candidate(
        self,
    ):
        from ai_os.intelligence import Ambiguity

        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(goal="report"),
            ),
            ambiguities=(
                Ambiguity(
                    description="format is unclear",
                ),
            ),
        )

        resolution = ReasoningResolver().resolve(result)

        self.assertEqual(
            resolution.status,
            ReasoningResolutionStatus.READY,
        )

    def test_missing_information_does_not_automatically_block(
        self,
    ):
        from ai_os.intelligence import MissingInformation

        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(goal="book_flight"),
            ),
            missing_information=(
                MissingInformation(
                    name="travel_date",
                ),
            ),
        )

        resolution = ReasoningResolver().resolve(result)

        self.assertEqual(
            resolution.status,
            ReasoningResolutionStatus.READY,
        )

    def test_uncertainty_does_not_automatically_block(self):
        from ai_os.intelligence import (
            ReasoningUncertainty,
        )

        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(goal="report"),
            ),
            uncertainty=ReasoningUncertainty(
                level="high",
            ),
        )

        resolution = ReasoningResolver().resolve(result)

        self.assertEqual(
            resolution.status,
            ReasoningResolutionStatus.READY,
        )

    def test_resolution_is_immutable(self):
        result = ReasoningResolver().resolve(
            ReasoningResult(
                intent_candidates=(
                    IntentCandidate(goal="report"),
                ),
            )
        )

        with self.assertRaises(AttributeError):
            result.status = (
                ReasoningResolutionStatus.UNRESOLVED
            )

    def test_issue_is_immutable(self):
        result = ReasoningResolver().resolve(
            ReasoningResult()
        )

        with self.assertRaises(AttributeError):
            result.issues[0].code = "changed"

    def test_resolution_has_no_execution_api(self):
        result = ReasoningResolver().resolve(
            ReasoningResult()
        )

        self.assertFalse(
            hasattr(result, "execute")
        )

        self.assertFalse(
            hasattr(result, "run")
        )

    def test_resolver_has_no_runtime_dependency(self):
        resolver = ReasoningResolver()

        self.assertFalse(
            hasattr(resolver, "runtime")
        )

        self.assertFalse(
            hasattr(resolver, "scheduler")
        )

        self.assertFalse(
            hasattr(resolver, "task_executor")
        )

        self.assertFalse(
            hasattr(resolver, "task_registry")
        )

    def test_resolution_does_not_create_intent(self):
        result = ReasoningResolver().resolve(
            ReasoningResult(
                intent_candidates=(
                    IntentCandidate(goal="report"),
                ),
            )
        )

        self.assertFalse(
            hasattr(result, "intent_id")
        )

        self.assertFalse(
            hasattr(result, "decision_id")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)