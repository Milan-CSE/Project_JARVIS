from __future__ import annotations
from dataclasses import dataclass,field
from enum import Enum
from types import MappingProxyType
from typing import Any,Mapping,Protocol,runtime_checkable
class DeploymentError(RuntimeError): pass
class DeploymentMode(str,Enum): LOCAL='local'; SERVER='server'; CLOUD='cloud'; HYBRID='hybrid'; EDGE='edge'
@dataclass(frozen=True,slots=True)
class DeploymentDescriptor:
    mode:DeploymentMode; name:str; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.mode,DeploymentMode): object.__setattr__(self,'mode',DeploymentMode(self.mode))
        if not self.name.strip(): raise ValueError('name required')
        object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@runtime_checkable
class DeploymentAdapter(Protocol):
    @property
    def descriptor(self)->DeploymentDescriptor: ...
    def start(self)->None: ...
    def stop(self)->None: ...
class DeploymentManager:
    def __init__(self,adapter:DeploymentAdapter):
        if not isinstance(adapter,DeploymentAdapter): raise TypeError('adapter')
        self._adapter=adapter; self._running=False
    @property
    def descriptor(self): return self._adapter.descriptor
    def start(self): self._adapter.start(); self._running=True
    def stop(self): self._adapter.stop(); self._running=False
    @property
    def running(self): return self._running
