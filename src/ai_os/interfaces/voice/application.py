from __future__ import annotations

from dataclasses import replace
from typing import Protocol, runtime_checkable

from ai_os.interfaces.api import (
    APIEvent,
    APIRequest,
    APIResponse,
)

from .models import (
    SpeechRecognitionResult,
    VoiceRequest,
    VoiceResponse,
    VoiceSession,
    VoiceSessionState,
)
from .recognition import SpeechRecognizer
from .synthesis import TextToSpeech


@runtime_checkable
class VoiceApplicationCore(Protocol):
    def handle(
        self,
        request: APIRequest,
    ) -> APIResponse:
        ...


@runtime_checkable
class VoiceApplication(Protocol):
    def submit_recognition(
        self,
        result: SpeechRecognitionResult,
        request_id: str,
    ) -> VoiceRequest | None:
        ...

    def handle_request(
        self,
        request: VoiceRequest,
    ) -> VoiceResponse:
        ...

    def stop_output(
        self,
        session: VoiceSession,
    ) -> VoiceSession:
        ...

    def cancel_request(
        self,
        session: VoiceSession,
    ) -> VoiceSession:
        ...


class DefaultVoiceApplication:
    """
    Thin Voice interface over the frozen 11.2 API boundary.

    Partial transcripts never become API requests. Final transcripts do.
    Stopping speech output is distinct from cancelling a core request.
    """

    def __init__(
        self,
        core: VoiceApplicationCore,
        recognizer: SpeechRecognizer,
        text_to_speech: TextToSpeech,
    ) -> None:
        if not isinstance(core, VoiceApplicationCore):
            raise TypeError(
                "core must implement VoiceApplicationCore"
            )
        if not isinstance(recognizer, SpeechRecognizer):
            raise TypeError(
                "recognizer must implement SpeechRecognizer"
            )
        if not isinstance(text_to_speech, TextToSpeech):
            raise TypeError(
                "text_to_speech must implement TextToSpeech"
            )

        self._core = core
        self._recognizer = recognizer
        self._text_to_speech = text_to_speech

    def recognize(
        self,
        audio: bytes,
    ) -> SpeechRecognitionResult:
        if not isinstance(audio, bytes):
            raise TypeError("audio must be bytes")

        return self._recognizer.recognize(audio)

    def submit_recognition(
        self,
        result: SpeechRecognitionResult,
        request_id: str,
    ) -> VoiceRequest | None:
        if not isinstance(
            result,
            SpeechRecognitionResult,
        ):
            raise TypeError(
                "result must be a SpeechRecognitionResult"
            )

        if not isinstance(request_id, str):
            raise TypeError("request_id must be a string")
        if not request_id.strip():
            raise ValueError("request_id must not be empty")

        # Critical safety rule: partial STT is presentation-only.
        if not result.is_final:
            return None

        if not result.transcript.strip():
            return None

        return VoiceRequest(
            request_id=request_id,
            transcript=result.transcript,
            language=result.language,
            metadata=result.metadata,
        )

    def handle_request(
        self,
        request: VoiceRequest,
    ) -> VoiceResponse:
        if not isinstance(request, VoiceRequest):
            raise TypeError(
                "request must be a VoiceRequest"
            )

        api_request = request.to_api_request()

        api_response = self._core.handle(
            api_request
        )

        if not isinstance(
            api_response,
            APIResponse,
        ):
            raise TypeError(
                "core must return an APIResponse"
            )

        if api_response.request_id != request.request_id:
            raise ValueError(
                "response request_id must match request"
            )

        return VoiceResponse(
            request_id=request.request_id,
            response=api_response,
        )

    def synthesize_response(
        self,
        response: VoiceResponse,
    ):
        if not isinstance(
            response,
            VoiceResponse,
        ):
            raise TypeError(
                "response must be a VoiceResponse"
            )

        text = response.response.output

        if text is None:
            return None

        if not isinstance(text, str):
            text = str(text)

        return self._text_to_speech.synthesize(
            text
        )

    def stop_output(
        self,
        session: VoiceSession,
    ) -> VoiceSession:
        if not isinstance(
            session,
            VoiceSession,
        ):
            raise TypeError(
                "session must be a VoiceSession"
            )

        return replace(
            session,
            state=VoiceSessionState.INTERRUPTED,
        )

    def cancel_request(
        self,
        session: VoiceSession,
    ) -> VoiceSession:
        if not isinstance(
            session,
            VoiceSession,
        ):
            raise TypeError(
                "session must be a VoiceSession"
            )

        return replace(
            session,
            state=VoiceSessionState.CANCELLED,
        )

    def apply_event(
        self,
        session: VoiceSession,
        event: APIEvent,
    ) -> VoiceSession:
        if not isinstance(
            session,
            VoiceSession,
        ):
            raise TypeError(
                "session must be a VoiceSession"
            )

        if not isinstance(
            event,
            APIEvent,
        ):
            raise TypeError(
                "event must be an APIEvent"
            )

        if event.correlation_id != session.request_id:
            raise ValueError(
                "event correlation_id must match session request_id"
            )

        return replace(
            session,
            state=VoiceSessionState.PROCESSING,
        )
