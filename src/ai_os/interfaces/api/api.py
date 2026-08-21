from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol, runtime_checkable

class APIResponseStatus(str, Enum):
    SUCCESS="success"; ACCEPTED="accepted"; BLOCKED="blocked"
    FAILED="failed"; CANCELLED="cancelled"; INCOMPLETE="incomplete"

@dataclass(frozen=True, slots=True)
class APIRequest:
    request_id: str
    operation: str
    input: str | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.request_id,str): raise TypeError("request_id must be a string")
        if not self.request_id.strip(): raise ValueError("request_id must not be empty")
        if not isinstance(self.operation,str): raise TypeError("operation must be a string")
        if not self.operation.strip(): raise ValueError("operation must not be empty")
        if self.input is not None and not isinstance(self.input,str):
            raise TypeError("input must be a string or None")
        if not isinstance(self.parameters,Mapping): raise TypeError("parameters must be a mapping")
        if not isinstance(self.metadata,Mapping): raise TypeError("metadata must be a mapping")
        object.__setattr__(self,"parameters",MappingProxyType(dict(self.parameters)))
        object.__setattr__(self,"metadata",MappingProxyType(dict(self.metadata)))

@dataclass(frozen=True, slots=True)
class APIError:
    code: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.code,str): raise TypeError("code must be a string")
        if not self.code.strip(): raise ValueError("code must not be empty")
        if not isinstance(self.message,str): raise TypeError("message must be a string")
        if not self.message.strip(): raise ValueError("message must not be empty")
        if not isinstance(self.details,Mapping): raise TypeError("details must be a mapping")
        object.__setattr__(self,"details",MappingProxyType(dict(self.details)))

@dataclass(frozen=True, slots=True)
class APIResponse:
    request_id: str
    status: APIResponseStatus
    output: Any = None
    error: APIError | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.request_id,str): raise TypeError("request_id must be a string")
        if not self.request_id.strip(): raise ValueError("request_id must not be empty")
        if not isinstance(self.status,APIResponseStatus):
            object.__setattr__(self,"status",APIResponseStatus(self.status))
        if self.error is not None and not isinstance(self.error,APIError):
            raise TypeError("error must be an APIError or None")
        if not isinstance(self.metadata,Mapping): raise TypeError("metadata must be a mapping")
        object.__setattr__(self,"metadata",MappingProxyType(dict(self.metadata)))

@dataclass(frozen=True, slots=True)
class APIEvent:
    event_id: str
    event_type: str
    correlation_id: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        for n in ("event_id","event_type","correlation_id"):
            v=getattr(self,n)
            if not isinstance(v,str): raise TypeError(f"{n} must be a string")
            if not v.strip(): raise ValueError(f"{n} must not be empty")
        if not isinstance(self.payload,Mapping): raise TypeError("payload must be a mapping")
        if not isinstance(self.metadata,Mapping): raise TypeError("metadata must be a mapping")
        object.__setattr__(self,"payload",MappingProxyType(dict(self.payload)))
        object.__setattr__(self,"metadata",MappingProxyType(dict(self.metadata)))

@runtime_checkable
class APIApplication(Protocol):
    def handle(self, request: APIRequest) -> APIResponse: ...

@runtime_checkable
class APIEventPublisher(Protocol):
    def publish(self, event: APIEvent) -> None: ...

class DefaultAPIApplication:
    def __init__(self, handler: Callable[[APIRequest], APIResponse]):
        if not callable(handler): raise TypeError("handler must be callable")
        self._handler=handler
    def handle(self, request: APIRequest) -> APIResponse:
        if not isinstance(request,APIRequest): raise TypeError("request must be an APIRequest")
        response=self._handler(request)
        if not isinstance(response,APIResponse): raise TypeError("handler must return an APIResponse")
        if response.request_id != request.request_id:
            raise ValueError("response request_id must match request request_id")
        return response
