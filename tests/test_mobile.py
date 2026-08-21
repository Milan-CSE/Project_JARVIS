from __future__ import annotations

import unittest

from ai_os.interfaces.api import (
    APIEvent,
    APIRequest,
    APIResponse,
    APIResponseStatus,
)
from ai_os.interfaces.mobile import (
    DefaultMobileApplication,
    MobileApplication,
    MobileApplicationClient,
    MobileConnectivityState,
    MobileOperationState,
    MobileTransport,
    MobileViewModel,
)


class FakeTransport:
    def __init__(self, response=None, events=()):
        self.calls = 0
        self.requests = []
        self.subscriptions = []
        self.events = tuple(events)
        self.response = response

    def send(self, request):
        self.calls += 1
        self.requests.append(request)
        return self.response or APIResponse(
            request_id=request.request_id,
            status=APIResponseStatus.SUCCESS,
            output={"ok": True},
        )

    def subscribe(self, correlation_id):
        self.subscriptions.append(correlation_id)
        return self.events


class WrongTransport:
    def send(self, request):
        return "invalid"

    def subscribe(self, correlation_id):
        return ("invalid",)


class MobileTests(unittest.TestCase):
    def request(self, request_id="req:1"):
        return APIRequest(
            request_id=request_id,
            operation="assistant.request",
            input="hello",
        )

    def event(self, event_id="event:1", correlation_id="req:1"):
        return APIEvent(
            event_id=event_id,
            event_type="request.progress",
            correlation_id=correlation_id,
            payload={"progress": 50},
        )

    def client(self, transport=None):
        return MobileApplicationClient(
            transport or FakeTransport()
        )

    # ------------------------------------------------------------
    # Protocols and construction
    # ------------------------------------------------------------

    def test_transport_matches_protocol(self):
        self.assertIsInstance(
            FakeTransport(),
            MobileTransport,
        )

    def test_application_matches_protocol(self):
        app = DefaultMobileApplication(
            self.client()
        )
        self.assertIsInstance(
            app,
            MobileApplication,
        )

    def test_invalid_transport_rejected(self):
        with self.assertRaises(TypeError):
            MobileApplicationClient(object())

    def test_invalid_application_client_rejected(self):
        with self.assertRaises(TypeError):
            DefaultMobileApplication(object())

    # ------------------------------------------------------------
    # Send
    # ------------------------------------------------------------

    def test_send_forwards_exact_request(self):
        transport = FakeTransport()
        request = self.request()
        self.client(transport).send(request)

        self.assertEqual(transport.calls, 1)
        self.assertIs(
            transport.requests[0],
            request,
        )

    def test_send_preserves_request_id(self):
        result = self.client().send(
            self.request("req:123")
        )

        self.assertEqual(
            result.request_id,
            "req:123",
        )

    def test_send_maps_success(self):
        result = self.client().send(
            self.request()
        )

        self.assertEqual(
            result.state,
            MobileOperationState.SUCCESS,
        )

    def test_send_rejects_offline(self):
        transport = FakeTransport()
        with self.assertRaises(ConnectionError):
            self.client(transport).send(
                self.request(),
                connectivity=MobileConnectivityState.OFFLINE,
            )
        self.assertEqual(transport.calls, 0)

    def test_send_rejects_connecting(self):
        transport = FakeTransport()
        with self.assertRaises(ConnectionError):
            self.client(transport).send(
                self.request(),
                connectivity=MobileConnectivityState.CONNECTING,
            )
        self.assertEqual(transport.calls, 0)

    def test_send_rejects_disconnected(self):
        transport = FakeTransport()
        with self.assertRaises(ConnectionError):
            self.client(transport).send(
                self.request(),
                connectivity=MobileConnectivityState.DISCONNECTED,
            )
        self.assertEqual(transport.calls, 0)

    def test_send_rejects_wrong_response_type(self):
        with self.assertRaises(TypeError):
            self.client(WrongTransport()).send(
                self.request()
            )

    def test_send_rejects_response_id_mismatch(self):
        transport = FakeTransport(
            response=APIResponse(
                request_id="different",
                status=APIResponseStatus.SUCCESS,
            )
        )

        with self.assertRaises(ValueError):
            self.client(transport).send(
                self.request()
            )

    def test_status_mapping(self):
        mappings = [
            (
                APIResponseStatus.ACCEPTED,
                MobileOperationState.PENDING,
            ),
            (
                APIResponseStatus.BLOCKED,
                MobileOperationState.BLOCKED,
            ),
            (
                APIResponseStatus.FAILED,
                MobileOperationState.FAILED,
            ),
            (
                APIResponseStatus.CANCELLED,
                MobileOperationState.CANCELLED,
            ),
            (
                APIResponseStatus.INCOMPLETE,
                MobileOperationState.INCOMPLETE,
            ),
        ]

        for api_status, mobile_status in mappings:
            result = self.client(
                FakeTransport(
                    response=APIResponse(
                        request_id="req:1",
                        status=api_status,
                    )
                )
            ).send(self.request())

            self.assertEqual(
                result.state,
                mobile_status,
            )

    # ------------------------------------------------------------
    # Synchronization / events
    # ------------------------------------------------------------

    def test_synchronize_receives_events(self):
        event = self.event()
        transport = FakeTransport(
            events=(event,)
        )

        result = self.client(transport).synchronize(
            "req:1"
        )

        self.assertEqual(
            result.events,
            (event,),
        )
        self.assertEqual(
            transport.subscriptions,
            ["req:1"],
        )

    def test_synchronize_preserves_event_order(self):
        first = self.event("event:1")
        second = self.event("event:2")
        result = self.client(
            FakeTransport(events=(first, second))
        ).synchronize("req:1")

        self.assertEqual(
            tuple(event.event_id for event in result.events),
            ("event:1", "event:2"),
        )

    def test_duplicate_events_do_not_duplicate_ui_state(self):
        event = self.event()
        result = self.client(
            FakeTransport(events=(event, event))
        ).synchronize("req:1")

        self.assertEqual(
            result.events,
            (event,),
        )

    def test_event_correlation_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            self.client(
                FakeTransport(
                    events=(
                        self.event(
                            correlation_id="wrong"
                        ),
                    )
                )
            ).synchronize("req:1")

    def test_wrong_event_type_rejected(self):
        with self.assertRaises(TypeError):
            self.client(
                WrongTransport()
            ).synchronize("req:1")

    def test_current_view_model_id_mismatch_rejected(self):
        current = MobileViewModel(
            request_id="req:2",
            state=MobileOperationState.PENDING,
        )

        with self.assertRaises(ValueError):
            self.client().synchronize(
                "req:1",
                current=current,
            )

    # ------------------------------------------------------------
    # Background / connectivity
    # ------------------------------------------------------------

    def test_background_does_not_cancel_operation(self):
        vm = MobileViewModel(
            request_id="req:1",
            state=MobileOperationState.PENDING,
        )

        result = self.client().mark_background(vm)

        self.assertEqual(
            result.state,
            MobileOperationState.BACKGROUND,
        )

    def test_disconnected_is_ui_state(self):
        vm = MobileViewModel(
            request_id="req:1",
            state=MobileOperationState.PENDING,
        )

        result = self.client().mark_disconnected(vm)

        self.assertEqual(
            result.state,
            MobileOperationState.DISCONNECTED,
        )
        self.assertEqual(
            result.connectivity,
            MobileConnectivityState.DISCONNECTED,
        )

    def test_connectivity_update_is_separate_from_operation_state(self):
        vm = MobileViewModel(
            request_id="req:1",
            state=MobileOperationState.PENDING,
            connectivity=MobileConnectivityState.ONLINE,
        )

        result = self.client().update_connectivity(
            vm,
            MobileConnectivityState.OFFLINE,
        )

        self.assertEqual(
            result.state,
            MobileOperationState.PENDING,
        )
        self.assertEqual(
            result.connectivity,
            MobileConnectivityState.OFFLINE,
        )

    def test_background_does_not_call_transport(self):
        transport = FakeTransport()
        vm = MobileViewModel(
            request_id="req:1",
            state=MobileOperationState.PENDING,
        )

        self.client(transport).mark_background(vm)

        self.assertEqual(transport.calls, 0)

    # ------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------

    def test_view_model_is_immutable(self):
        vm = MobileViewModel(
            request_id="req:1",
            state=MobileOperationState.IDLE,
        )

        with self.assertRaises(AttributeError):
            vm.state = MobileOperationState.SUCCESS

    def test_metadata_is_immutable(self):
        vm = MobileViewModel(
            request_id="req:1",
            state=MobileOperationState.IDLE,
            metadata={"x": 1},
        )

        with self.assertRaises(TypeError):
            vm.metadata["x"] = 2

    # ------------------------------------------------------------
    # Architectural boundary tests
    # ------------------------------------------------------------

    def test_no_runtime_executor(self):
        client = self.client()

        self.assertFalse(
            hasattr(client, "runtime_executor")
        )
        self.assertFalse(
            hasattr(client, "executor")
        )

    def test_no_tool_registry(self):
        self.assertFalse(
            hasattr(
                self.client(),
                "tool_registry",
            )
        )

    def test_no_task_registry(self):
        self.assertFalse(
            hasattr(
                self.client(),
                "task_registry",
            )
        )

    def test_no_workflow_runner(self):
        self.assertFalse(
            hasattr(
                self.client(),
                "workflow_runner",
            )
        )

    def test_no_intelligence_methods(self):
        client = self.client()

        self.assertFalse(hasattr(client, "reason"))
        self.assertFalse(hasattr(client, "plan"))
        self.assertFalse(hasattr(client, "decide"))

    def test_no_security_authorization(self):
        client = self.client()

        self.assertFalse(hasattr(client, "authorize"))
        self.assertFalse(hasattr(client, "security"))

    def test_no_identity_factory(self):
        self.assertFalse(
            hasattr(
                self.client(),
                "create_identity",
            )
        )

    def test_no_persistence_api(self):
        client = self.client()

        self.assertFalse(hasattr(client, "save"))
        self.assertFalse(hasattr(client, "persist"))

    def test_no_retry_api(self):
        self.assertFalse(
            hasattr(
                self.client(),
                "retry",
            )
        )

    # ------------------------------------------------------------
    # Reuse / isolation
    # ------------------------------------------------------------

    def test_client_is_reusable(self):
        transport = FakeTransport()
        client = self.client(transport)

        first = client.send(self.request("req:1"))
        second = client.send(self.request("req:2"))

        self.assertEqual(
            first.request_id,
            "req:1",
        )
        self.assertEqual(
            second.request_id,
            "req:2",
        )
        self.assertEqual(
            transport.calls,
            2,
        )

    def test_requests_do_not_share_state(self):
        transport = FakeTransport()
        client = self.client(transport)

        first = self.request("req:1")
        second = self.request("req:2")

        client.send(first)
        client.send(second)

        self.assertIs(
            transport.requests[0],
            first,
        )
        self.assertIs(
            transport.requests[1],
            second,
        )

    # ------------------------------------------------------------
    # Application composition
    # ------------------------------------------------------------

    def test_default_application_delegates_to_client(self):
        transport = FakeTransport()
        client = MobileApplicationClient(transport)
        app = DefaultMobileApplication(client)

        result = app.send(
            self.request("req:1")
        )

        self.assertEqual(
            result.request_id,
            "req:1",
        )
        self.assertEqual(
            transport.calls,
            1,
        )

    def test_application_update_connectivity(self):
        app = DefaultMobileApplication(
            self.client()
        )

        vm = MobileViewModel(
            request_id="req:1",
            state=MobileOperationState.PENDING,
        )

        result = app.update_connectivity(
            vm,
            MobileConnectivityState.OFFLINE,
        )

        self.assertEqual(
            result.connectivity,
            MobileConnectivityState.OFFLINE,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
