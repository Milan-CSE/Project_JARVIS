import unittest

from ai_os.intelligence import (
    AmbiguousIntentError,
    IntentCandidate,
    IntentExtractor,
    IntentSelector,
    NoIntentCandidateError,
    ReasoningResult,
)


class IntentSelectionTests(unittest.TestCase):

    def test_single_candidate_is_selected(self):
        candidate = IntentCandidate(
            goal="generate_report",
        )

        result = ReasoningResult(
            intent_candidates=(candidate,),
        )

        selected = IntentSelector().select(result)

        self.assertEqual(
            selected.goal,
            "generate_report",
        )

    def test_no_candidates_rejected(self):
        result = ReasoningResult()

        with self.assertRaises(
            NoIntentCandidateError
        ):
            IntentSelector().select(result)

    def test_multiple_candidates_require_explicit_selection(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(goal="sales_report"),
                IntentCandidate(goal="financial_report"),
            ),
        )

        with self.assertRaises(
            AmbiguousIntentError
        ):
            IntentSelector().select(result)

    def test_explicit_candidate_selection(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(goal="sales_report"),
                IntentCandidate(goal="financial_report"),
            ),
        )

        selected = IntentSelector().select(
            result,
            candidate_index=1,
        )

        self.assertEqual(
            selected.goal,
            "financial_report",
        )

    def test_negative_index_rejected(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(goal="report"),
            ),
        )

        with self.assertRaises(IndexError):
            IntentSelector().select(
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
            IntentSelector().select(
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
            IntentSelector().select(
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
            IntentSelector().select(
                result,
                candidate_index="0",
            )

    def test_invalid_result_rejected(self):
        with self.assertRaises(TypeError):
            IntentSelector().select("invalid")

    def test_extractor_creates_intent(self):
        candidate = IntentCandidate(
            goal="generate_report",
            parameters={
                "date": "today",
            },
            constraints={
                "format": "pdf",
            },
            metadata={
                "source": "reasoning",
            },
        )

        intent = IntentExtractor().extract(
            candidate,
            "intent:test",
        )

        self.assertEqual(
            intent.intent_id,
            "intent:test",
        )

        self.assertEqual(
            intent.goal,
            "generate_report",
        )

        self.assertEqual(
            intent.parameters["date"],
            "today",
        )

        self.assertEqual(
            intent.constraints["format"],
            "pdf",
        )

        self.assertEqual(
            intent.metadata["source"],
            "reasoning",
        )

    def test_extractor_does_not_generate_id(self):
        candidate = IntentCandidate(
            goal="report",
        )

        intent = IntentExtractor().extract(
            candidate,
            "intent:explicit",
        )

        self.assertEqual(
            intent.intent_id,
            "intent:explicit",
        )

    def test_empty_intent_id_rejected(self):
        candidate = IntentCandidate(
            goal="report",
        )

        with self.assertRaises(ValueError):
            IntentExtractor().extract(
                candidate,
                "",
            )

    def test_invalid_intent_id_type_rejected(self):
        candidate = IntentCandidate(
            goal="report",
        )

        with self.assertRaises(TypeError):
            IntentExtractor().extract(
                candidate,
                123,
            )

    def test_invalid_candidate_rejected(self):
        with self.assertRaises(TypeError):
            IntentExtractor().extract(
                "invalid",
                "intent:test",
            )

    def test_missing_information_does_not_block_extraction(self):
        candidate = IntentCandidate(
            goal="book_flight",
            parameters={
                "destination": "Paris",
            },
        )

        intent = IntentExtractor().extract(
            candidate,
            "intent:flight",
        )

        self.assertEqual(
            intent.goal,
            "book_flight",
        )

    def test_extraction_preserves_immutability(self):
        candidate = IntentCandidate(
            goal="report",
            parameters={
                "format": "pdf",
            },
        )

        intent = IntentExtractor().extract(
            candidate,
            "intent:test",
        )

        with self.assertRaises(TypeError):
            intent.parameters["format"] = "csv"

    def test_selector_does_not_execute(self):
        selector = IntentSelector()

        self.assertFalse(
            hasattr(selector, "execute")
        )

        self.assertFalse(
            hasattr(selector, "run")
        )

    def test_extractor_does_not_execute(self):
        extractor = IntentExtractor()

        self.assertFalse(
            hasattr(extractor, "execute")
        )

        self.assertFalse(
            hasattr(extractor, "run")
        )

    def test_selector_does_not_require_runtime(self):
        selector = IntentSelector()

        self.assertFalse(
            hasattr(selector, "runtime")
        )

        self.assertFalse(
            hasattr(selector, "scheduler")
        )

        self.assertFalse(
            hasattr(selector, "task_executor")
        )

    def test_extractor_does_not_require_runtime(self):
        extractor = IntentExtractor()

        self.assertFalse(
            hasattr(extractor, "runtime")
        )

        self.assertFalse(
            hasattr(extractor, "scheduler")
        )

        self.assertFalse(
            hasattr(extractor, "task_registry")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)