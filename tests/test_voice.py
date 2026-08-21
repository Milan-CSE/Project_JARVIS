from __future__ import annotations

import unittest

from ai_os.interfaces.api import (
    APIEvent,
    APIRequest,
    APIResponse,
    APIResponseStatus,
)
from ai_os.interfaces.voice import (
    DefaultSpeechRecognizer,
    DefaultTextToSpeech,
    DefaultVoiceApplication,
    SpeechAudio,
    SpeechRecognitionResult,
    SpeechRecognizer,
    TextToSpeech,
    VoiceApplication,
    VoiceApplicationCore,
    VoiceRequest,
    VoiceResponse,
    VoiceSession,
    VoiceSessionState,
)


class FakeCore:
    def __init__(self):
        self.calls = 0
        self.requests = []

    def handle(self, request):
        self.calls += 1
        self.requests.append(request)
        return APIResponse(
            request_id=request.request_id,
            status=APIResponseStatus.SUCCESS,
            output="safe response",
        )


class FakeRecognizer:
    def __init__(self, result):
        self.calls = 0
        self.audio = []
        self.result = result

    def recognize(self, audio):
        self.calls += 1
        self.audio.append(audio)
        return self.result


class FakeTTS:
    def __init__(self):
        self.calls = 0
        self.texts = []

    def synthesize(self, text):
        self.calls += 1
        self.texts.append(text)
        return SpeechAudio(
            audio=b"audio",
            format="wav",
            sample_rate=16000,
        )


class BadCore:
    def handle(self, request):
        return "invalid"


class MismatchedCore:
    def handle(self, request):
        return APIResponse(
            request_id="different",
            status=APIResponseStatus.SUCCESS,
        )


class VoiceTests(unittest.TestCase):
    def final_result(self, transcript="open browser"):
        return SpeechRecognitionResult(
            transcript=transcript,
            confidence=0.98,
            language="en-IN",
            is_final=True,
        )

    def app(self, final=True):
        result = self.final_result() if final else SpeechRecognitionResult(
            transcript="partial command",
            confidence=0.5,
            language="en-IN",
            is_final=False,
        )
        core = FakeCore()
        recognizer = FakeRecognizer(result)
        tts = FakeTTS()
        app = DefaultVoiceApplication(
            core=core,
            recognizer=recognizer,
            text_to_speech=tts,
        )
        return app, core, recognizer, tts

    # ------------------------------------------------------------
    # Protocols
    # ------------------------------------------------------------

    def test_recognizer_protocol(self):
        self.assertIsInstance(
            FakeRecognizer(self.final_result()),
            SpeechRecognizer,
        )

    def test_tts_protocol(self):
        self.assertIsInstance(
            FakeTTS(),
            TextToSpeech,
        )

    def test_core_protocol(self):
        self.assertIsInstance(FakeCore(), VoiceApplicationCore)

    def test_application_protocol(self):
        app, _, _, _ = self.app()
        self.assertIsInstance(app, VoiceApplication)

    def test_invalid_dependencies_rejected(self):
        with self.assertRaises(TypeError):
            DefaultVoiceApplication(
                object(),
                FakeRecognizer(self.final_result()),
                FakeTTS(),
            )

        with self.assertRaises(TypeError):
            DefaultVoiceApplication(
                FakeCore(),
                object(),
                FakeTTS(),
            )

        with self.assertRaises(TypeError):
            DefaultVoiceApplication(
                FakeCore(),
                FakeRecognizer(self.final_result()),
                object(),
            )

    # ------------------------------------------------------------
    # Recognition
    # ------------------------------------------------------------

    def test_recognize_forwards_exact_audio(self):
        app, _, recognizer, _ = self.app()
        audio = b"\x00\x01"
        result = app.recognize(audio)

        self.assertIs(result, recognizer.result)
        self.assertEqual(recognizer.calls, 1)
        self.assertIs(recognizer.audio[0], audio)

    def test_recognize_rejects_non_bytes(self):
        app, _, _, _ = self.app()

        with self.assertRaises(TypeError):
            app.recognize("audio")

    def test_default_recognizer_is_contract_only(self):
        recognizer = DefaultSpeechRecognizer()

        with self.assertRaises(NotImplementedError):
            recognizer.recognize(b"audio")

    # ------------------------------------------------------------
    # Partial/final transcript boundary
    # ------------------------------------------------------------

    def test_partial_transcript_does_not_create_request(self):
        app, core, _, _ = self.app(final=False)

        result = app.submit_recognition(
            SpeechRecognitionResult(
                transcript="send an email to jo",
                confidence=0.5,
                is_final=False,
            ),
            "req:1",
        )

        self.assertIsNone(result)
        self.assertEqual(core.calls, 0)

    def test_final_transcript_creates_voice_request(self):
        app, core, _, _ = self.app()

        result = app.submit_recognition(
            self.final_result(),
            "req:1",
        )

        self.assertIsInstance(result, VoiceRequest)
        self.assertEqual(result.request_id, "req:1")
        self.assertEqual(result.transcript, "open browser")
        self.assertEqual(core.calls, 0)

    def test_empty_final_transcript_does_not_create_request(self):
        app, _, _, _ = self.app()

        result = app.submit_recognition(
            SpeechRecognitionResult(
                transcript=" ",
                is_final=True,
            ),
            "req:1",
        )

        self.assertIsNone(result)

    def test_invalid_recognition_result_rejected(self):
        app, _, _, _ = self.app()

        with self.assertRaises(TypeError):
            app.submit_recognition(
                "invalid",
                "req:1",
            )

    def test_invalid_request_id_rejected(self):
        app, _, _, _ = self.app()

        with self.assertRaises(ValueError):
            app.submit_recognition(
                self.final_result(),
                "",
            )

    # ------------------------------------------------------------
    # VoiceRequest / API boundary
    # ------------------------------------------------------------

    def test_voice_request_is_immutable(self):
        request = VoiceRequest(
            request_id="req:1",
            transcript="hello",
        )

        with self.assertRaises(AttributeError):
            request.transcript = "changed"

    def test_voice_request_metadata_immutable(self):
        request = VoiceRequest(
            request_id="req:1",
            transcript="hello",
            metadata={"x": 1},
        )

        with self.assertRaises(TypeError):
            request.metadata["x"] = 2

    def test_voice_request_converts_to_api_request(self):
        request = VoiceRequest(
            request_id="req:1",
            transcript="hello",
        )
        api_request = request.to_api_request()

        self.assertIsInstance(api_request, APIRequest)
        self.assertEqual(api_request.request_id, "req:1")
        self.assertEqual(api_request.input, "hello")
        self.assertEqual(
            api_request.operation,
            "assistant.request",
        )

    def test_handle_request_calls_core_once(self):
        app, core, _, _ = self.app()

        request = VoiceRequest(
            request_id="req:1",
            transcript="hello",
        )
        result = app.handle_request(request)

        self.assertEqual(core.calls, 1)
        self.assertIsInstance(result, VoiceResponse)

    def test_handle_request_preserves_request_id(self):
        app, _, _, _ = self.app()

        result = app.handle_request(
            VoiceRequest(
                request_id="req:123",
                transcript="hello",
            )
        )

        self.assertEqual(result.request_id, "req:123")
        self.assertEqual(
            result.response.request_id,
            "req:123",
        )

    def test_wrong_core_result_rejected(self):
        app = DefaultVoiceApplication(
            BadCore(),
            FakeRecognizer(self.final_result()),
            FakeTTS(),
        )

        with self.assertRaises(TypeError):
            app.handle_request(
                VoiceRequest(
                    request_id="req:1",
                    transcript="hello",
                )
            )

    def test_mismatched_core_request_id_rejected(self):
        app = DefaultVoiceApplication(
            MismatchedCore(),
            FakeRecognizer(self.final_result()),
            FakeTTS(),
        )

        with self.assertRaises(ValueError):
            app.handle_request(
                VoiceRequest(
                    request_id="req:1",
                    transcript="hello",
                )
            )

    # ------------------------------------------------------------
    # TTS
    # ------------------------------------------------------------

    def test_tts_synthesizes_response_output(self):
        app, _, _, tts = self.app()

        voice_response = app.handle_request(
            VoiceRequest(
                request_id="req:1",
                transcript="hello",
            )
        )

        audio = app.synthesize_response(
            voice_response
        )

        self.assertIsInstance(audio, SpeechAudio)
        self.assertEqual(audio.audio, b"audio")
        self.assertEqual(tts.calls, 1)
        self.assertEqual(
            tts.texts,
            ["safe response"],
        )

    def test_tts_none_output_returns_none(self):
        core = FakeCore()

        class NoneCore:
            def handle(self, request):
                return APIResponse(
                    request_id=request.request_id,
                    status=APIResponseStatus.SUCCESS,
                    output=None,
                )

        app = DefaultVoiceApplication(
            NoneCore(),
            FakeRecognizer(self.final_result()),
            FakeTTS(),
        )

        response = app.handle_request(
            VoiceRequest(
                request_id="req:1",
                transcript="hello",
            )
        )

        self.assertIsNone(
            app.synthesize_response(response)
        )

    def test_tts_contract_only_default(self):
        with self.assertRaises(NotImplementedError):
            DefaultTextToSpeech().synthesize("hello")

    # ------------------------------------------------------------
    # Session and interruption/cancellation
    # ------------------------------------------------------------

    def test_voice_session_is_immutable(self):
        session = VoiceSession(
            request_id="req:1",
            state=VoiceSessionState.LISTENING,
        )

        with self.assertRaises(AttributeError):
            session.state = VoiceSessionState.SPEAKING

    def test_stop_output_is_distinct_from_cancel(self):
        app, _, _, _ = self.app()
        session = VoiceSession(
            request_id="req:1",
            state=VoiceSessionState.SPEAKING,
        )

        interrupted = app.stop_output(session)
        cancelled = app.cancel_request(session)

        self.assertEqual(
            interrupted.state,
            VoiceSessionState.INTERRUPTED,
        )
        self.assertEqual(
            cancelled.state,
            VoiceSessionState.CANCELLED,
        )

    def test_stop_output_does_not_call_core(self):
        app, core, _, _ = self.app()

        session = VoiceSession(
            request_id="req:1",
            state=VoiceSessionState.SPEAKING,
        )

        app.stop_output(session)

        self.assertEqual(core.calls, 0)

    def test_cancel_request_does_not_execute_core(self):
        app, core, _, _ = self.app()

        session = VoiceSession(
            request_id="req:1",
            state=VoiceSessionState.PROCESSING,
        )

        app.cancel_request(session)

        self.assertEqual(core.calls, 0)

    def test_event_correlation_mismatch_rejected(self):
        app, _, _, _ = self.app()
        session = VoiceSession(
            request_id="req:1",
            state=VoiceSessionState.PROCESSING,
        )

        with self.assertRaises(ValueError):
            app.apply_event(
                session,
                APIEvent(
                    event_id="event:1",
                    event_type="progress",
                    correlation_id="req:2",
                ),
            )

    def test_event_transitions_to_processing(self):
        app, _, _, _ = self.app()
        session = VoiceSession(
            request_id="req:1",
            state=VoiceSessionState.PROCESSING,
        )

        result = app.apply_event(
            session,
            APIEvent(
                event_id="event:1",
                event_type="progress",
                correlation_id="req:1",
            ),
        )

        self.assertEqual(
            result.state,
            VoiceSessionState.PROCESSING,
        )

    # ------------------------------------------------------------
    # Identity/security/core isolation
    # ------------------------------------------------------------

    def test_no_runtime_executor(self):
        app, _, _, _ = self.app()

        self.assertFalse(
            hasattr(app, "runtime_executor")
        )
        self.assertFalse(
            hasattr(app, "executor")
        )

    def test_no_tool_registry(self):
        app, _, _, _ = self.app()

        self.assertFalse(
            hasattr(app, "tool_registry")
        )

    def test_no_task_registry(self):
        app, _, _, _ = self.app()

        self.assertFalse(
            hasattr(app, "task_registry")
        )

    def test_no_workflow_runner(self):
        app, _, _, _ = self.app()

        self.assertFalse(
            hasattr(app, "workflow_runner")
        )

    def test_no_security_authorization(self):
        app, _, _, _ = self.app()

        self.assertFalse(
            hasattr(app, "authorize")
        )
        self.assertFalse(
            hasattr(app, "security")
        )

    def test_no_identity_factory(self):
        app, _, _, _ = self.app()

        self.assertFalse(
            hasattr(app, "create_identity")
        )

    def test_no_intelligence_methods(self):
        app, _, _, _ = self.app()

        self.assertFalse(hasattr(app, "reason"))
        self.assertFalse(hasattr(app, "plan"))
        self.assertFalse(hasattr(app, "decide"))
        self.assertFalse(hasattr(app, "replan"))

    # ------------------------------------------------------------
    # Reuse / isolation
    # ------------------------------------------------------------

    def test_application_reusable_without_cross_request_state(self):
        app, core, _, _ = self.app()

        first = app.handle_request(
            VoiceRequest("req:1", "first")
        )
        second = app.handle_request(
            VoiceRequest("req:2", "second")
        )

        self.assertEqual(core.calls, 2)
        self.assertEqual(first.request_id, "req:1")
        self.assertEqual(second.request_id, "req:2")
        self.assertEqual(
            core.requests[0].request_id,
            "req:1",
        )
        self.assertEqual(
            core.requests[1].request_id,
            "req:2",
        )

    # ------------------------------------------------------------
    # Model validation
    # ------------------------------------------------------------

    def test_confidence_range(self):
        with self.assertRaises(ValueError):
            SpeechRecognitionResult(
                transcript="hello",
                confidence=1.5,
            )

    def test_speech_audio_validation(self):
        with self.assertRaises(TypeError):
            SpeechAudio(
                audio="bad",
                format="wav",
                sample_rate=16000,
            )

        with self.assertRaises(ValueError):
            SpeechAudio(
                audio=b"audio",
                format="",
                sample_rate=16000,
            )

        with self.assertRaises(ValueError):
            SpeechAudio(
                audio=b"audio",
                format="wav",
                sample_rate=0,
            )

    def test_voice_response_immutable(self):
        response = APIResponse(
            request_id="req:1",
            status=APIResponseStatus.SUCCESS,
            output="ok",
        )

        result = VoiceResponse(
            request_id="req:1",
            response=response,
        )

        with self.assertRaises(AttributeError):
            result.request_id = "changed"

    def test_voice_response_request_id_mismatch_rejected(self):
        response = APIResponse(
            request_id="req:2",
            status=APIResponseStatus.SUCCESS,
        )

        with self.assertRaises(ValueError):
            VoiceResponse(
                request_id="req:1",
                response=response,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
