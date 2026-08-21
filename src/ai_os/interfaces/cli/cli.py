from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol, runtime_checkable


class CLIResponseStatus(str, Enum):
    SUCCESS = "success"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"


@dataclass(frozen=True, slots=True)
class CLIRequest:
    input: str
    arguments: tuple[str, ...] = ()
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.input, str):
            raise TypeError("input must be a string")
        if not self.input.strip():
            raise ValueError("input must not be empty or whitespace")
        if not isinstance(self.arguments, tuple):
            object.__setattr__(self, "arguments", tuple(self.arguments))
        if not all(isinstance(value, str) for value in self.arguments):
            raise TypeError("arguments must contain only strings")
        if not isinstance(self.options, Mapping):
            raise TypeError("options must be a mapping")
        object.__setattr__(self, "options", MappingProxyType(dict(self.options)))


@dataclass(frozen=True, slots=True)
class CLIResponse:
    status: CLIResponseStatus
    output: str
    exit_code: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.status, CLIResponseStatus):
            object.__setattr__(self, "status", CLIResponseStatus(self.status))
        if not isinstance(self.output, str):
            raise TypeError("output must be a string")
        if isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int):
            raise TypeError("exit_code must be an int")
        if self.exit_code < 0:
            raise ValueError("exit_code must be >= 0")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@runtime_checkable
class CLIApplication(Protocol):
    def handle(self, request: CLIRequest) -> CLIResponse:
        ...


class CLIHandler(Protocol):
    def __call__(self, request: CLIRequest) -> CLIResponse:
        ...


class DefaultCLIApplication:
    def __init__(self, handler: Callable[[CLIRequest], CLIResponse]) -> None:
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._handler = handler

    def handle(self, request: CLIRequest) -> CLIResponse:
        if not isinstance(request, CLIRequest):
            raise TypeError("request must be a CLIRequest")
        response = self._handler(request)
        if not isinstance(response, CLIResponse):
            raise TypeError("handler must return a CLIResponse")
        return response


class CLIParser:
    def parse(self, argv: tuple[str, ...] | list[str]) -> CLIRequest:
        if not isinstance(argv, (tuple, list)):
            raise TypeError("argv must be a list or tuple of strings")
        if not all(isinstance(value, str) for value in argv):
            raise TypeError("argv must contain only strings")
        if not argv:
            raise ValueError("argv must contain a request")

        positional: list[str] = []
        options: dict[str, Any] = {}

        for token in argv:
            if token.startswith("--"):
                option = token[2:]
                if not option:
                    raise ValueError("option name must not be empty")
                if "=" in option:
                    key, value = option.split("=", 1)
                    if not key.strip():
                        raise ValueError("option name must not be empty")
                    options[key] = value
                else:
                    options[option] = True
            else:
                positional.append(token)

        if not positional:
            raise ValueError("CLI request input is required")

        return CLIRequest(
            input=positional[0],
            arguments=tuple(positional[1:]),
            options=options,
        )


@runtime_checkable
class CLIResponseRenderer(Protocol):
    def render(self, response: CLIResponse) -> str:
        ...


class HumanCLIResponseRenderer:
    def render(self, response: CLIResponse) -> str:
        if not isinstance(response, CLIResponse):
            raise TypeError("response must be a CLIResponse")
        return response.output


class JSONCLIResponseRenderer:
    def render(self, response: CLIResponse) -> str:
        if not isinstance(response, CLIResponse):
            raise TypeError("response must be a CLIResponse")
        return json.dumps(
            {
                "status": response.status.value,
                "output": response.output,
                "exit_code": response.exit_code,
                "metadata": dict(response.metadata),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
