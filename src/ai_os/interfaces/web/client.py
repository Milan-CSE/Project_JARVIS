from typing import Protocol, runtime_checkable
from ai_os.interfaces.api import APIEvent, APIRequest, APIResponse
from .models import WebViewModel

@runtime_checkable
class WebClientTransport(Protocol):
    def send(self,request:APIRequest)->APIResponse: ...
    def subscribe(self,correlation_id:str)->tuple[APIEvent,...]: ...

class WebApplicationClient:
    def __init__(self,transport):
        if not isinstance(transport,WebClientTransport): raise TypeError("transport must implement WebClientTransport")
        self._transport=transport
    def send(self,request):
        if not isinstance(request,APIRequest): raise TypeError("request must be an APIRequest")
        response=self._transport.send(request)
        if not isinstance(response,APIResponse): raise TypeError("transport.send must return an APIResponse")
        if response.request_id!=request.request_id: raise ValueError("response request_id must match request request_id")
        return WebViewModel.from_response(response)
    def receive_events(self,request_id,current=None):
        if not isinstance(request_id,str): raise TypeError("request_id must be a string")
        if not request_id.strip(): raise ValueError("request_id must not be empty")
        if current is None: current=WebViewModel(request_id, "pending")
        if not isinstance(current,WebViewModel): raise TypeError("current must be a WebViewModel or None")
        if current.request_id!=request_id: raise ValueError("current request_id must match request_id")
        state=current
        for event in self._transport.subscribe(request_id):
            state=state.with_event(event)
        return state
    def mark_disconnected(self,current):
        if not isinstance(current,WebViewModel): raise TypeError("current must be a WebViewModel")
        return current.disconnected()
