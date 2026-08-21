from typing import Any, Mapping, Protocol, runtime_checkable
from .models import WebViewModel
@runtime_checkable
class WebResponseRenderer(Protocol):
    def render(self,view_model:WebViewModel)->Mapping[str,Any]: ...
class DefaultWebResponseRenderer:
    def render(self,view_model):
        if not isinstance(view_model,WebViewModel): raise TypeError("view_model must be a WebViewModel")
        return {"request_id":view_model.request_id,"state":view_model.state.value,"output":view_model.output,
                "events":tuple({"event_id":e.event_id,"event_type":e.event_type,"correlation_id":e.correlation_id,
                                "payload":dict(e.payload),"metadata":dict(e.metadata)} for e in view_model.events),
                "error":view_model.error,"metadata":dict(view_model.metadata)}
