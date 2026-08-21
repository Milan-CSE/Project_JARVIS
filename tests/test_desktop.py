from __future__ import annotations

import unittest

from ai_os.interfaces.desktop import (
    DefaultDesktopApplication,
    DefaultDesktopController,
    DefaultDesktopObserver,
    DesktopActionRequest,
    DesktopActionResult,
    DesktopApplication,
    DesktopController,
    DesktopObserver,
    DesktopSession,
    DesktopSessionState,
    DesktopSnapshot,
    DisplayInfo,
    WindowInfo,
)


class FakeObserver:
    def __init__(self, snapshot=None):
        self.calls = 0
        self.snapshot_value = snapshot or DesktopSnapshot(
            snapshot_id="snapshot:1",
        )

    def snapshot(self):
        self.calls += 1
        return self.snapshot_value


class FakeController:
    def __init__(self, result=None):
        self.calls = 0
        self.requests = []
        self.result = result

    def request_action(self, request):
        self.calls += 1
        self.requests.append(request)
        return self.result or DesktopActionResult(
            request_id=request.request_id,
            accepted=True,
            status="accepted",
        )


class BadObserver:
    def snapshot(self):
        return "invalid"


class BadController:
    def request_action(self, request):
        return "invalid"


class MismatchedController:
    def request_action(self, request):
        return DesktopActionResult(
            request_id="different",
            accepted=True,
            status="accepted",
        )


class DesktopTests(unittest.TestCase):
    def request(self, request_id="req:1"):
        return DesktopActionRequest(
            request_id=request_id,
            action="launch.application",
            target="calculator",
            parameters={"safe": True},
        )

    # ------------------------------------------------------------
    # Protocols
    # ------------------------------------------------------------

    def test_observer_protocol(self):
        self.assertIsInstance(
            FakeObserver(),
            DesktopObserver,
        )

    def test_controller_protocol(self):
        self.assertIsInstance(
            FakeController(),
            DesktopController,
        )

    def test_application_protocol(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            FakeController(),
        )
        self.assertIsInstance(app, DesktopApplication)

    def test_invalid_dependencies_rejected(self):
        with self.assertRaises(TypeError):
            DefaultDesktopApplication(object(), FakeController())

        with self.assertRaises(TypeError):
            DefaultDesktopApplication(FakeObserver(), object())

    # ------------------------------------------------------------
    # Models / immutability
    # ------------------------------------------------------------

    def test_display_info_immutable(self):
        value = DisplayInfo("display:1", 1920, 1080)
        with self.assertRaises(AttributeError):
            value.width = 1280

    def test_window_info_immutable(self):
        value = WindowInfo(
            "window:1",
            "Calculator",
            "calculator",
        )
        with self.assertRaises(AttributeError):
            value.title = "changed"

    def test_snapshot_immutable(self):
        snapshot = DesktopSnapshot(
            "snapshot:1",
            windows=(
                WindowInfo(
                    "window:1",
                    "Calculator",
                    "calculator",
                ),
            ),
        )
        with self.assertRaises(AttributeError):
            snapshot.snapshot_id = "changed"

    def test_snapshot_metadata_immutable(self):
        snapshot = DesktopSnapshot(
            "snapshot:1",
            metadata={"x": 1},
        )
        with self.assertRaises(TypeError):
            snapshot.metadata["x"] = 2

    def test_action_request_immutable(self):
        request = self.request()
        with self.assertRaises(AttributeError):
            request.action = "changed"

    def test_action_request_parameters_immutable(self):
        request = self.request()
        with self.assertRaises(TypeError):
            request.parameters["x"] = 1

    def test_action_result_immutable(self):
        result = DesktopActionResult(
            "req:1",
            True,
            "accepted",
        )
        with self.assertRaises(AttributeError):
            result.accepted = False

    def test_session_immutable(self):
        session = DesktopSession(
            "session:1",
            DesktopSessionState.IDLE,
        )
        with self.assertRaises(AttributeError):
            session.state = DesktopSessionState.OBSERVING

    # ------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------

    def test_empty_snapshot_id_rejected(self):
        with self.assertRaises(ValueError):
            DesktopSnapshot("")

    def test_invalid_display_dimensions_rejected(self):
        with self.assertRaises(ValueError):
            DisplayInfo("display:1", 0, 1080)

    def test_invalid_window_id_rejected(self):
        with self.assertRaises(ValueError):
            WindowInfo("", "title", "app")

    def test_empty_action_rejected(self):
        with self.assertRaises(ValueError):
            DesktopActionRequest("req:1", "")

    def test_empty_session_id_rejected(self):
        with self.assertRaises(ValueError):
            DesktopSession(
                "",
                DesktopSessionState.IDLE,
            )

    # ------------------------------------------------------------
    # Observation
    # ------------------------------------------------------------

    def test_observe_calls_observer_once(self):
        observer = FakeObserver()
        app = DefaultDesktopApplication(
            observer,
            FakeController(),
        )

        result = app.observe()

        self.assertEqual(observer.calls, 1)
        self.assertIs(
            result,
            observer.snapshot_value,
        )

    def test_observe_rejects_invalid_snapshot(self):
        app = DefaultDesktopApplication(
            BadObserver(),
            FakeController(),
        )
        with self.assertRaises(TypeError):
            app.observe()

    def test_default_observer_is_contract_only(self):
        with self.assertRaises(NotImplementedError):
            DefaultDesktopObserver().snapshot()

    # ------------------------------------------------------------
    # Action boundary
    # ------------------------------------------------------------

    def test_request_action_forwards_exact_request(self):
        controller = FakeController()
        app = DefaultDesktopApplication(
            FakeObserver(),
            controller,
        )

        request = self.request()
        app.request_action(request)

        self.assertEqual(controller.calls, 1)
        self.assertIs(
            controller.requests[0],
            request,
        )

    def test_request_action_rejects_invalid_request(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            FakeController(),
        )

        with self.assertRaises(TypeError):
            app.request_action("launch")

    def test_request_action_rejects_invalid_result(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            BadController(),
        )

        with self.assertRaises(TypeError):
            app.request_action(self.request())

    def test_request_action_preserves_request_id(self):
        controller = FakeController()
        app = DefaultDesktopApplication(
            FakeObserver(),
            controller,
        )

        result = app.request_action(
            self.request("req:123")
        )

        self.assertEqual(
            result.request_id,
            "req:123",
        )

    def test_request_id_mismatch_rejected(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            MismatchedController(),
        )

        with self.assertRaises(ValueError):
            app.request_action(self.request())

    # ------------------------------------------------------------
    # Session boundary
    # ------------------------------------------------------------

    def test_disconnect_is_interface_state_only(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            FakeController(),
        )
        session = DesktopSession(
            "session:1",
            DesktopSessionState.WAITING,
        )

        result = app.mark_disconnected(session)

        self.assertEqual(
            result.state,
            DesktopSessionState.DISCONNECTED,
        )

    def test_interrupt_is_interface_state_only(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            FakeController(),
        )
        session = DesktopSession(
            "session:1",
            DesktopSessionState.REQUESTING,
        )

        result = app.interrupt(session)

        self.assertEqual(
            result.state,
            DesktopSessionState.INTERRUPTED,
        )

    # ------------------------------------------------------------
    # No lower-layer authority
    # ------------------------------------------------------------

    def test_no_runtime_executor(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            FakeController(),
        )
        self.assertFalse(hasattr(app, "runtime_executor"))
        self.assertFalse(hasattr(app, "executor"))

    def test_no_task_registry(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            FakeController(),
        )
        self.assertFalse(hasattr(app, "task_registry"))

    def test_no_tool_registry(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            FakeController(),
        )
        self.assertFalse(hasattr(app, "tool_registry"))

    def test_no_workflow_runner(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            FakeController(),
        )
        self.assertFalse(hasattr(app, "workflow_runner"))

    def test_no_intelligence(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            FakeController(),
        )
        self.assertFalse(hasattr(app, "reason"))
        self.assertFalse(hasattr(app, "plan"))
        self.assertFalse(hasattr(app, "decide"))

    def test_no_security_authorization(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            FakeController(),
        )
        self.assertFalse(hasattr(app, "authorize"))
        self.assertFalse(hasattr(app, "security"))

    def test_no_identity_factory(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            FakeController(),
        )
        self.assertFalse(hasattr(app, "create_identity"))

    def test_no_persistence(self):
        app = DefaultDesktopApplication(
            FakeObserver(),
            FakeController(),
        )
        self.assertFalse(hasattr(app, "save"))
        self.assertFalse(hasattr(app, "persist"))

    def test_controller_default_does_not_execute(self):
        with self.assertRaises(NotImplementedError):
            DefaultDesktopController().request_action(
                self.request()
            )

    # ------------------------------------------------------------
    # Reuse / isolation
    # ------------------------------------------------------------

    def test_application_reusable(self):
        observer = FakeObserver()
        controller = FakeController()
        app = DefaultDesktopApplication(
            observer,
            controller,
        )

        first = app.observe()
        second = app.observe()

        self.assertIs(first, observer.snapshot_value)
        self.assertIs(second, observer.snapshot_value)
        self.assertEqual(observer.calls, 2)

    def test_requests_do_not_share_state(self):
        controller = FakeController()
        app = DefaultDesktopApplication(
            FakeObserver(),
            controller,
        )

        first = self.request("req:1")
        second = self.request("req:2")

        app.request_action(first)
        app.request_action(second)

        self.assertIs(controller.requests[0], first)
        self.assertIs(controller.requests[1], second)

    # ------------------------------------------------------------
    # Display/window collections
    # ------------------------------------------------------------

    def test_multiple_displays_supported(self):
        snapshot = DesktopSnapshot(
            "snapshot:1",
            displays=(
                DisplayInfo("display:1", 1920, 1080),
                DisplayInfo("display:2", 2560, 1440),
            ),
        )
        self.assertEqual(len(snapshot.displays), 2)

    def test_multiple_windows_supported(self):
        snapshot = DesktopSnapshot(
            "snapshot:1",
            windows=(
                WindowInfo(
                    "window:1",
                    "A",
                    "appA",
                ),
                WindowInfo(
                    "window:2",
                    "B",
                    "appB",
                ),
            ),
        )
        self.assertEqual(len(snapshot.windows), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
