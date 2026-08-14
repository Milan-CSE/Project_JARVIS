import unittest

from ai_os.intelligence import (
    Ambiguity,
    ContextSource,
    IntentCandidate,
    MissingInformation,
    ReasoningObservation,
    ReasoningResult,
    ReasoningUncertainty,
    UncertaintyLevel,
)


class ReasoningResultTests(unittest.TestCase):

    def test_intent_candidate_can_be_created(self):
        candidate = IntentCandidate(
            goal="generate_report",
        )

        self.assertEqual(
            candidate.goal,
            "generate_report",
        )

    def test_intent_candidate_accepts_parameters(self):
        candidate = IntentCandidate(
            goal="generate_report",
            parameters={
                "date": "today",
            },
        )

        self.assertEqual(
            candidate.parameters["date"],
            "today",
        )

    def test_observation_preserves_source(self):
        observation = ReasoningObservation(
            value="today",
            source=ContextSource.SYSTEM,
        )

        self.assertEqual(
            observation.source,
            ContextSource.SYSTEM,
        )

    def test_ambiguity_can_be_created(self):
        ambiguity = Ambiguity(
            description="Recipient is unclear.",
            candidates=(
                "John Smith",
                "John Patel",
            ),
        )

        self.assertEqual(
            len(ambiguity.candidates),
            2,
        )

    def test_missing_information_can_be_created(self):
        missing = MissingInformation(
            name="travel_date",
            description="The travel date is unknown.",
        )

        self.assertEqual(
            missing.name,
            "travel_date",
        )

    def test_uncertainty_accepts_string_level(self):
        uncertainty = ReasoningUncertainty(
            level="high",
            reasons=(
                "required information is missing",
            ),
        )

        self.assertEqual(
            uncertainty.level,
            UncertaintyLevel.HIGH,
        )

    def test_reasoning_result_can_be_created(self):
        candidate = IntentCandidate(
            goal="generate_report",
        )

        result = ReasoningResult(
            interpretation="The user wants a report.",
            intent_candidates=(candidate,),
        )

        self.assertEqual(
            result.interpretation,
            "The user wants a report.",
        )

        self.assertEqual(
            len(result.intent_candidates),
            1,
        )

    def test_empty_reasoning_result_is_allowed(self):
        result = ReasoningResult()

        self.assertEqual(
            result.interpretation,
            "",
        )

        self.assertEqual(
            result.observations,
            (),
        )

        self.assertEqual(
            result.intent_candidates,
            (),
        )

    def test_result_supports_multiple_candidates(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(
                    goal="sales_report",
                ),
                IntentCandidate(
                    goal="financial_report",
                ),
            ),
        )

        self.assertEqual(
            len(result.intent_candidates),
            2,
        )

    def test_nested_candidate_data_is_immutable(self):
        candidate = IntentCandidate(
            goal="report",
            parameters={
                "options": {
                    "format": "pdf",
                },
                "tags": [
                    "daily",
                ],
            },
        )

        with self.assertRaises(TypeError):
            candidate.parameters["options"]["format"] = "csv"

        with self.assertRaises(AttributeError):
            candidate.parameters["tags"].append("sales")

    def test_observation_value_is_immutable(self):
        observation = ReasoningObservation(
            value={
                "details": {
                    "source": "user",
                }
            },
            source=ContextSource.USER,
        )

        with self.assertRaises(TypeError):
            observation.value["details"]["source"] = "system"

    def test_result_is_immutable(self):
        result = ReasoningResult()

        with self.assertRaises(AttributeError):
            result.interpretation = "changed"

    def test_ambiguity_is_immutable(self):
        ambiguity = Ambiguity(
            description="unclear",
        )

        with self.assertRaises(AttributeError):
            ambiguity.description = "changed"

    def test_missing_information_is_immutable(self):
        missing = MissingInformation(
            name="date",
        )

        with self.assertRaises(AttributeError):
            missing.name = "other"

    def test_uncertainty_is_immutable(self):
        uncertainty = ReasoningUncertainty(
            level=UncertaintyLevel.MEDIUM,
        )

        with self.assertRaises(AttributeError):
            uncertainty.level = UncertaintyLevel.HIGH

    def test_metadata_is_immutable(self):
        result = ReasoningResult(
            metadata={
                "source": "test",
            },
        )

        with self.assertRaises(TypeError):
            result.metadata["source"] = "other"

    def test_invalid_candidate_goal_rejected(self):
        with self.assertRaises(ValueError):
            IntentCandidate(
                goal="",
            )

    def test_invalid_candidate_goal_type_rejected(self):
        with self.assertRaises(TypeError):
            IntentCandidate(
                goal=123,
            )

    def test_invalid_observation_source_rejected(self):
        with self.assertRaises(ValueError):
            ReasoningObservation(
                value="test",
                source="invalid",
            )

    def test_invalid_ambiguity_description_rejected(self):
        with self.assertRaises(ValueError):
            Ambiguity(
                description="",
            )

    def test_invalid_missing_information_name_rejected(self):
        with self.assertRaises(ValueError):
            MissingInformation(
                name="",
            )

    def test_invalid_uncertainty_level_rejected(self):
        with self.assertRaises(ValueError):
            ReasoningUncertainty(
                level="invalid",
            )

    def test_invalid_reasoning_result_observation_rejected(self):
        with self.assertRaises(TypeError):
            ReasoningResult(
                observations=("invalid",),
            )

    def test_invalid_reasoning_result_candidate_rejected(self):
        with self.assertRaises(TypeError):
            ReasoningResult(
                intent_candidates=("invalid",),
            )

    def test_invalid_uncertainty_object_rejected(self):
        with self.assertRaises(TypeError):
            ReasoningResult(
                uncertainty="high",
            )

    def test_result_has_no_execution_members(self):
        result = ReasoningResult()

        self.assertFalse(
            hasattr(result, "execute")
        )

        self.assertFalse(
            hasattr(result, "run")
        )

        self.assertFalse(
            hasattr(result, "execution_plan")
        )

    def test_candidate_has_no_runtime_members(self):
        candidate = IntentCandidate(
            goal="report",
        )

        self.assertFalse(
            hasattr(candidate, "runtime")
        )

        self.assertFalse(
            hasattr(candidate, "scheduler")
        )

        self.assertFalse(
            hasattr(candidate, "task_executor")
        )

    def test_candidate_has_no_authorization(self):
        candidate = IntentCandidate(
            goal="delete_data",
        )

        self.assertFalse(
            hasattr(candidate, "authorized")
        )

        self.assertFalse(
            hasattr(candidate, "permission")
        )

    def test_observation_is_not_authorization(self):
        observation = ReasoningObservation(
            value="user is allowed",
            source=ContextSource.MEMORY,
        )

        self.assertFalse(
            hasattr(observation, "authorized")
        )

        self.assertFalse(
            hasattr(observation, "permission")
        )

    def test_reasoning_result_does_not_create_intent(self):
        result = ReasoningResult(
            intent_candidates=(
                IntentCandidate(
                    goal="report",
                ),
            ),
        )

        self.assertFalse(
            hasattr(result, "intent_id")
        )

        self.assertFalse(
            hasattr(result, "decision_id")
        )

    def test_candidate_has_no_workflow_reference(self):
        candidate = IntentCandidate(
            goal="report",
        )

        self.assertFalse(
            hasattr(candidate, "workflow_id")
        )

    def test_no_numeric_confidence_is_required(self):
        result = ReasoningResult()

        self.assertIsNone(
            result.uncertainty,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)