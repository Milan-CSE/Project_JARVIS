from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from ai_os.interfaces.api import APIEvent, APIResponse, APIResponseStatus

class WebOperationState(str, Enum):
    IDLE="idle"; PENDING="pending"; SUCCESS="success"; BLOCKED="blocked"
    FAILED="failed"; CANCELLED="cancelled"; INCOMPLETE="incomplete"; DISCONNECTED="disconnected"

@dataclass(frozen=True, slots=True)
class WebViewModel:
    request_id: str
    state: WebOperationState
    output: Any = None
    events: tuple[APIEvent, ...] = ()
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.request_id,str): raise TypeError("request_id must be a string")
        if not self.request_id.strip(): raise ValueError("request_id must not be empty")
        if not isinstance(self.state,WebOperationState): object.__setattr__(self,"state",WebOperationState(self.state))
        if not isinstance(self.events,tuple): object.__setattr__(self,"events",tuple(self.events))
        if not all(isinstance(e,APIEvent) for e in self.events): raise TypeError("events must contain only APIEvent instances")
        if self.error is not None and not isinstance(self.error,str): raise TypeError("error must be a string or None")
        if not isinstance(self.metadata,Mapping): raise TypeError("metadata must be a mapping")
        object.__setattr__(self,"metadata",MappingProxyType(dict(self.metadata)))
    @classmethod
    def from_response(cls,response):
        if not isinstance(response,APIResponse): raise TypeError("response must be an APIResponse")
        m={APIResponseStatus.SUCCESS:WebOperationState.SUCCESS,APIResponseStatus.ACCEPTED:WebOperationState.PENDING,
           APIResponseStatus.BLOCKED:WebOperationState.BLOCKED,APIResponseStatus.FAILED:WebOperationState.FAILED,
           APIResponseStatus.CANCELLED:WebOperationState.CANCELLED,APIResponseStatus.INCOMPLETE:WebOperationState.INCOMPLETE}
        return cls(response.request_id,m[response.status],response.output,error=response.error.message if response.error else None,metadata=response.metadata)
    def with_event(self,event):
        if not isinstance(event,APIEvent): raise TypeError("event must be an APIEvent")
        if event.correlation_id!=self.request_id: raise ValueError("event correlation_id must match request_id")
        if any(e.event_id==event.event_id for e in self.events): return self
        return WebViewModel(self.request_id,WebOperationState.PENDING,self.output,self.events+(event,),self.error,self.metadata)
    def disconnected(self):
        return WebViewModel(self.request_id,WebOperationState.DISCONNECTED,self.output,self.events,self.error,self.metadata)
