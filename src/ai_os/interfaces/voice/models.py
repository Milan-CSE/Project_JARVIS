from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from ai_os.interfaces.api import APIEvent, APIRequest, APIResponse


class VoiceSessionState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class SpeechRecognitionResult:
    transcript: str
    confidence: float | None = None
    language: str | None = None
    is_final: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.transcript, str):
            raise TypeError("transcript must be a string")

        if self.confidence is not None:
            if isinstance(self.confidence, bool) or not isinstance(
                self.confidence, (int, float)
            ):
                raise TypeError(
                    "confidence must be a number or None"
                )
            if not 0.0 <= float(self.confidence) <= 1.0:
                raise ValueError(
                    "confidence must be between 0 and 1"
                )

        if self.language is not None and not isinstance(
            self.language,
            str,
        ):
            raise TypeError("language must be a string or None")

        if not isinstance(self.is_final, bool):
            raise TypeError("is_final must be a bool")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@dataclass(frozen=True, slots=True)
class SpeechAudio:
    audio: bytes
    format: str
    sample_rate: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.audio, bytes):
            raise TypeError("audio must be bytes")

        if not isinstance(self.format, str):
            raise TypeError("format must be a string")
        if not self.format.strip():
            raise ValueError("format must not be empty")

        if isinstance(self.sample_rate, bool) or not isinstance(
            self.sample_rate,
            int,
        ):
            raise TypeError("sample_rate must be an int")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be > 0")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@dataclass(frozen=True, slots=True)
class VoiceRequest:
    request_id: str
    transcript: str
    language: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str):
            raise TypeError("request_id must be a string")
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")

        if not isinstance(self.transcript, str):
            raise TypeError("transcript must be a string")
        if not self.transcript.strip():
            raise ValueError("transcript must not be empty")

        if self.language is not None and not isinstance(
            self.language,
            str,
        ):
            raise TypeError("language must be a string or None")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    def to_api_request(self) -> APIRequest:
        return APIRequest(
            request_id=self.request_id,
            operation="assistant.request",
            input=self.transcript,
            metadata=self.metadata,
        )


@dataclass(frozen=True, slots=True)
class VoiceResponse:
    request_id: str
    response: APIResponse
    events: tuple[APIEvent, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str):
            raise TypeError("request_id must be a string")
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")

        if not isinstance(self.response, APIResponse):
            raise TypeError("response must be an APIResponse")

        if self.response.request_id != self.request_id:
            raise ValueError(
                "response request_id must match request_id"
            )

        if not isinstance(self.events, tuple):
            object.__setattr__(
                self,
                "events",
                tuple(self.events),
            )

        if not all(
            isinstance(event, APIEvent)
            for event in self.events
        ):
            raise TypeError(
                "events must contain only APIEvent instances"
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


@dataclass(frozen=True, slots=True)
class VoiceSession:
    request_id: str
    state: VoiceSessionState
    transcript: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str):
            raise TypeError("request_id must be a string")
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")

        if not isinstance(self.state, VoiceSessionState):
            object.__setattr__(
                self,
                "state",
                VoiceSessionState(self.state),
            )

        if self.transcript is not None and not isinstance(
            self.transcript,
            str,
        ):
            raise TypeError(
                "transcript must be a string or None"
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )
