from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import SpeechRecognitionResult


@runtime_checkable
class SpeechRecognizer(Protocol):
    def recognize(
        self,
        audio: bytes,
    ) -> SpeechRecognitionResult:
        ...


class DefaultSpeechRecognizer:
    """
    Contract-only placeholder.

    Concrete STT providers belong in later provider/device adapters.
    """

    def recognize(
        self,
        audio: bytes,
    ) -> SpeechRecognitionResult:
        raise NotImplementedError(
            "No concrete speech-recognition provider configured"
        )
