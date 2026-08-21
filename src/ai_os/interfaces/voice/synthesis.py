from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import SpeechAudio


@runtime_checkable
class TextToSpeech(Protocol):
    def synthesize(
        self,
        text: str,
    ) -> SpeechAudio:
        ...


class DefaultTextToSpeech:
    """
    Contract-only placeholder.

    Concrete TTS providers belong in later provider/device adapters.
    """

    def synthesize(
        self,
        text: str,
    ) -> SpeechAudio:
        raise NotImplementedError(
            "No concrete text-to-speech provider configured"
        )
