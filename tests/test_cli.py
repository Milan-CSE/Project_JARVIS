from __future__ import annotations

import unittest

from ai_os.interfaces.cli import (
    CLIApplication,
    CLIParser,
    CLIRequest,
    CLIResponse,
    CLIResponseRenderer,
    CLIResponseStatus,
    DefaultCLIApplication,
    HumanCLIResponseRenderer,
    JSONCLIResponseRenderer,
)


class TrackingCore:
    def __init__(self, response: CLIResponse | None = None):
        self.calls = 0
        self.requests = []
        self.response = response or CLIResponse(
            status=CLIResponseStatus.SUCCESS,
            output="ok",
            exit_code=0,
        )

    def __call__(self, request: CLIRequest) -> CLIResponse:
        self.calls += 1
        self.requests.append(request)
        return self.response


class WrongCore:
    def __call__(self, request: CLIRequest):
        return "invalid"


class RaisingCore:
    def __call__(self, request: CLIRequest):
        raise RuntimeError("core failure")


class CLIApplicationTests(unittest.TestCase):

    def request(self):
        return CLIRequest(
            input="open browser",
            arguments=("browser",),
            options={"format": "human"},
        )

    def test_valid_application_matches_protocol(self):
        app = DefaultCLIApplication(TrackingCore())
        self.assertIsInstance(app, CLIApplication)

    def test_invalid_handler_rejected(self):
        with self.assertRaises(TypeError):
            DefaultCLIApplication(object())

    def test_application_rejects_invalid_request(self):
        app = DefaultCLIApplication(TrackingCore())
        with self.assertRaises(TypeError):
            app.handle(object())

    def test_handler_called_once(self):
        core = TrackingCore()
        DefaultCLIApplication(core).handle(self.request())
        self.assertEqual(core.calls, 1)

    def test_exact_request_forwarded(self):
        core = TrackingCore()
        request = self.request()
        DefaultCLIApplication(core).handle(request)
        self.assertIs(core.requests[0], request)

    def test_handler_result_preserved(self):
        response = CLIResponse(
            status=CLIResponseStatus.SUCCESS,
            output="hello",
            exit_code=0,
        )
        result = DefaultCLIApplication(
            TrackingCore(response)
        ).handle(self.request())
        self.assertIs(result, response)

    def test_wrong_handler_result_rejected(self):
        with self.assertRaises(TypeError):
            DefaultCLIApplication(WrongCore()).handle(self.request())

    def test_handler_exception_propagates(self):
        with self.assertRaises(RuntimeError):
            DefaultCLIApplication(RaisingCore()).handle(self.request())

    def test_request_is_immutable(self):
        request = self.request()
        with self.assertRaises(AttributeError):
            request.input = "changed"

    def test_request_options_are_immutable(self):
        request = self.request()
        with self.assertRaises(TypeError):
            request.options["x"] = 1

    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError):
            CLIRequest(input="   ")

    def test_invalid_input_type_rejected(self):
        with self.assertRaises(TypeError):
            CLIRequest(input=123)

    def test_invalid_argument_type_rejected(self):
        with self.assertRaises(TypeError):
            CLIRequest(input="hello", arguments=("ok", 1))

    def test_response_is_immutable(self):
        response = CLIResponse(
            status=CLIResponseStatus.SUCCESS,
            output="ok",
            exit_code=0,
        )
        with self.assertRaises(AttributeError):
            response.output = "changed"

    def test_response_metadata_is_immutable(self):
        response = CLIResponse(
            status=CLIResponseStatus.SUCCESS,
            output="ok",
            exit_code=0,
            metadata={"x": 1},
        )
        with self.assertRaises(TypeError):
            response.metadata["x"] = 2

    def test_negative_exit_code_rejected(self):
        with self.assertRaises(ValueError):
            CLIResponse(
                status=CLIResponseStatus.SUCCESS,
                output="ok",
                exit_code=-1,
            )

    def test_boolean_exit_code_rejected(self):
        with self.assertRaises(TypeError):
            CLIResponse(
                status=CLIResponseStatus.SUCCESS,
                output="ok",
                exit_code=True,
            )

    def test_parser_creates_request(self):
        request = CLIParser().parse(
            ("open-browser", "example.com", "--format=json")
        )
        self.assertEqual(request.input, "open-browser")
        self.assertEqual(request.arguments, ("example.com",))
        self.assertEqual(request.options["format"], "json")

    def test_parser_supports_boolean_option(self):
        request = CLIParser().parse(("test", "--debug"))
        self.assertTrue(request.options["debug"])

    def test_parser_rejects_empty_argv(self):
        with self.assertRaises(ValueError):
            CLIParser().parse(())

    def test_parser_rejects_non_strings(self):
        with self.assertRaises(TypeError):
            CLIParser().parse(("test", 1))

    def test_parser_rejects_empty_option(self):
        with self.assertRaises(ValueError):
            CLIParser().parse(("test", "--"))

    def test_parser_does_not_select_tool(self):
        request = CLIParser().parse(("browser.search", "AI"))
        self.assertEqual(request.input, "browser.search")

    def test_human_renderer_returns_output_only(self):
        response = CLIResponse(
            status=CLIResponseStatus.SUCCESS,
            output="hello",
            exit_code=0,
            metadata={"secret": "not rendered"},
        )
        self.assertEqual(
            HumanCLIResponseRenderer().render(response),
            "hello",
        )

    def test_json_renderer_is_deterministic(self):
        response = CLIResponse(
            status=CLIResponseStatus.SUCCESS,
            output="hello",
            exit_code=0,
            metadata={"b": 2, "a": 1},
        )
        renderer = JSONCLIResponseRenderer()
        self.assertEqual(renderer.render(response), renderer.render(response))

    def test_json_renderer_returns_string(self):
        response = CLIResponse(
            status=CLIResponseStatus.SUCCESS,
            output="hello",
            exit_code=0,
        )
        rendered = JSONCLIResponseRenderer().render(response)
        self.assertIsInstance(rendered, str)
        self.assertIn('"status":"success"', rendered)

    def test_human_renderer_matches_protocol(self):
        self.assertIsInstance(
            HumanCLIResponseRenderer(),
            CLIResponseRenderer,
        )

    def test_json_renderer_matches_protocol(self):
        self.assertIsInstance(
            JSONCLIResponseRenderer(),
            CLIResponseRenderer,
        )

    def test_cli_has_no_runtime_executor(self):
        app = DefaultCLIApplication(TrackingCore())
        self.assertFalse(hasattr(app, "runtime_executor"))
        self.assertFalse(hasattr(app, "executor"))

    def test_cli_has_no_task_registry(self):
        app = DefaultCLIApplication(TrackingCore())
        self.assertFalse(hasattr(app, "task_registry"))

    def test_cli_has_no_tool_registry(self):
        app = DefaultCLIApplication(TrackingCore())
        self.assertFalse(hasattr(app, "tool_registry"))

    def test_cli_has_no_workflow_runner(self):
        app = DefaultCLIApplication(TrackingCore())
        self.assertFalse(hasattr(app, "workflow_runner"))

    def test_cli_has_no_security_manager(self):
        app = DefaultCLIApplication(TrackingCore())
        self.assertFalse(hasattr(app, "security"))
        self.assertFalse(hasattr(app, "authorize"))

    def test_cli_has_no_intelligence_methods(self):
        app = DefaultCLIApplication(TrackingCore())
        self.assertFalse(hasattr(app, "reason"))
        self.assertFalse(hasattr(app, "plan"))
        self.assertFalse(hasattr(app, "decide"))

    def test_cli_has_no_identity_factory(self):
        app = DefaultCLIApplication(TrackingCore())
        self.assertFalse(hasattr(app, "create_identity"))

    def test_cli_does_not_call_sys_exit(self):
        response = CLIResponse(
            status=CLIResponseStatus.FAILED,
            output="failed",
            exit_code=1,
        )
        result = DefaultCLIApplication(
            TrackingCore(response)
        ).handle(self.request())
        self.assertEqual(result.exit_code, 1)

    def test_all_statuses_exist(self):
        self.assertEqual(
            set(CLIResponseStatus),
            {
                CLIResponseStatus.SUCCESS,
                CLIResponseStatus.BLOCKED,
                CLIResponseStatus.FAILED,
                CLIResponseStatus.CANCELLED,
                CLIResponseStatus.WAITING,
            },
        )

    def test_application_is_reusable(self):
        core = TrackingCore()
        app = DefaultCLIApplication(core)
        first = app.handle(CLIRequest("first"))
        second = app.handle(CLIRequest("second"))
        self.assertEqual(core.calls, 2)
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)

    def test_no_cross_request_state(self):
        core = TrackingCore()
        app = DefaultCLIApplication(core)
        first = CLIRequest("first")
        second = CLIRequest("second")
        app.handle(first)
        app.handle(second)
        self.assertIs(core.requests[0], first)
        self.assertIs(core.requests[1], second)


if __name__ == "__main__":
    unittest.main(verbosity=2)
