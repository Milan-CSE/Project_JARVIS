from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
from types import MappingProxyType
from typing import Any,Mapping,Protocol,runtime_checkable

def _m(v):
    if not isinstance(v,Mapping): raise TypeError('metadata must be a mapping')
    return MappingProxyType(dict(v))
@dataclass(frozen=True,slots=True)
class TraceContext:
    trace_id:str; span_id:str
@dataclass(frozen=True,slots=True)
class AuditRecord:
    action:str; actor:str; outcome:str; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self): object.__setattr__(self,'metadata',_m(self.metadata))
@dataclass(frozen=True,slots=True)
class DiagnosticRecord:
    code:str; message:str; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self): object.__setattr__(self,'metadata',_m(self.metadata))
@dataclass(frozen=True,slots=True)
class MetricSample:
    name:str; value:float; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self): object.__setattr__(self,'metadata',_m(self.metadata))
@dataclass(frozen=True,slots=True)
class ObservabilityEvent:
    event_type:str; timestamp:datetime=field(default_factory=lambda:datetime.now(timezone.utc)); metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self): object.__setattr__(self,'metadata',_m(self.metadata))
@runtime_checkable
class Observability(Protocol):
    def record_event(self,event:ObservabilityEvent)->None: ...
    def record_metric(self,sample:MetricSample)->None: ...
    def record_audit(self,record:AuditRecord)->None: ...
    def record_diagnostic(self,record:DiagnosticRecord)->None: ...
class InMemoryObservability:
    def __init__(self): self.events=[]; self.metrics=[]; self.audits=[]; self.diagnostics=[]
    def record_event(self,e):
        if not isinstance(e,ObservabilityEvent): raise TypeError('event')
        self.events.append(e)
    def record_metric(self,s):
        if not isinstance(s,MetricSample): raise TypeError('sample')
        self.metrics.append(s)
    def record_audit(self,r):
        if not isinstance(r,AuditRecord): raise TypeError('record')
        self.audits.append(r)
    def record_diagnostic(self,r):
        if not isinstance(r,DiagnosticRecord): raise TypeError('record')
        self.diagnostics.append(r)
