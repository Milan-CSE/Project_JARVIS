from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from ai_os.intelligence.context import ContextSource
from ai_os.intelligence.reasoning.result import (
    Ambiguity,
    IntentCandidate,
    MissingInformation,
    ReasoningObservation,
    ReasoningResult,
    ReasoningUncertainty,
    UncertaintyLevel,
)


class ReasoningOutputError(ValueError):
    """Raised when provider output cannot become ReasoningResult."""


@runtime_checkable
class ReasoningOutputParserProtocol(Protocol):
    """Contract for converting provider output into ReasoningResult."""

    def parse(
        self,
        output: Any,
    ) -> ReasoningResult:
        ...

class ReasoningOutputParser:
    """Parses untrusted provider output into ReasoningResult."""

    _ALLOWED_FIELDS = {
        "interpretation",
        "observations",
        "ambiguities",
        "missing_information",
        "intent_candidates",
        "uncertainty",
        "metadata",
    }

    def parse(
        self,
        output: Any,
    ) -> ReasoningResult:
        if not isinstance(output, Mapping):
            raise ReasoningOutputError(
                "provider output must be a mapping"
            )

        data = {
            key: value
            for key, value in output.items()
            if key in self._ALLOWED_FIELDS
        }

        try:
            interpretation = data.get(
                "interpretation",
                "",
            )

            observations = tuple(
                self._parse_observation(item)
                for item in data.get(
                    "observations",
                    (),
                )
            )

            ambiguities = tuple(
                self._parse_ambiguity(item)
                for item in data.get(
                    "ambiguities",
                    (),
                )
            )

            missing_information = tuple(
                self._parse_missing_information(item)
                for item in data.get(
                    "missing_information",
                    (),
                )
            )

            candidates = tuple(
                self._parse_candidate(item)
                for item in data.get(
                    "intent_candidates",
                    (),
                )
            )

            uncertainty = self._parse_uncertainty(
                data.get("uncertainty")
            )

            metadata = data.get(
                "metadata",
                {},
            )

            # Provider metadata remains model-derived metadata.
            metadata = dict(metadata)
            metadata["derived_by"] = "reasoning_provider"

            return ReasoningResult(
                interpretation=interpretation,
                observations=observations,
                ambiguities=ambiguities,
                missing_information=missing_information,
                intent_candidates=candidates,
                uncertainty=uncertainty,
                metadata=metadata,
            )

        except (TypeError, ValueError, KeyError) as exc:
            raise ReasoningOutputError(
                "provider output has invalid reasoning structure"
            ) from exc

    def _parse_observation(
        self,
        value: Any,
    ) -> ReasoningObservation:
        if not isinstance(value, Mapping):
            raise TypeError(
                "observation must be a mapping"
            )

        # Never trust model-declared provenance.
        return ReasoningObservation(
            value=value.get("value"),
            source=ContextSource.EXTERNAL,
            metadata={
                "declared_source": value.get("source"),
                "derived_by": "reasoning_provider",
            },
        )

    def _parse_ambiguity(
        self,
        value: Any,
    ) -> Ambiguity:
        if not isinstance(value, Mapping):
            raise TypeError(
                "ambiguity must be a mapping"
            )

        candidates = value.get(
            "candidates",
            (),
        )

        if not isinstance(
            candidates,
            (list, tuple),
        ):
            raise TypeError(
                "ambiguity candidates must be a sequence"
            )

        return Ambiguity(
            description=value.get(
                "description",
                "",
            ),
            candidates=tuple(candidates),
            metadata=value.get(
                "metadata",
                {},
            ),
        )

    def _parse_missing_information(
        self,
        value: Any,
    ) -> MissingInformation:
        if not isinstance(value, Mapping):
            raise TypeError(
                "missing information must be a mapping"
            )

        return MissingInformation(
            name=value.get(
                "name",
                "",
            ),
            description=value.get(
                "description"
            ),
            metadata=value.get(
                "metadata",
                {},
            ),
        )

    def _parse_candidate(
        self,
        value: Any,
    ) -> IntentCandidate:
        if not isinstance(value, Mapping):
            raise TypeError(
                "intent candidate must be a mapping"
            )

        return IntentCandidate(
            goal=value.get(
                "goal",
                "",
            ),
            parameters=value.get(
                "parameters",
                {},
            ),
            constraints=value.get(
                "constraints",
                {},
            ),
            metadata=value.get(
                "metadata",
                {},
            ),
        )

    def _parse_uncertainty(
        self,
        value: Any,
    ) -> ReasoningUncertainty | None:
        if value is None:
            return None

        if not isinstance(value, Mapping):
            raise TypeError(
                "uncertainty must be a mapping"
            )

        return ReasoningUncertainty(
            level=value.get(
                "level",
                "",
            ),
            reasons=tuple(
                value.get(
                    "reasons",
                    (),
                )
            ),
            metadata=value.get(
                "metadata",
                {},
            ),
        )