from __future__ import annotations
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Any,Mapping,Protocol,runtime_checkable
class DistributionError(RuntimeError): pass
class DuplicateWorkerError(DistributionError): pass
class WorkerNotFoundError(DistributionError): pass
@dataclass(frozen=True,slots=True)
class WorkerDescriptor:
    worker_id:str; version:str; capabilities:tuple[str,...]=(); metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.worker_id.strip() or not self.version.strip(): raise ValueError('ids required')
        object.__setattr__(self,'capabilities',tuple(self.capabilities)); object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@runtime_checkable
class Worker(Protocol):
    @property
    def descriptor(self)->WorkerDescriptor: ...
    def accept(self,execution_plan:Any)->Any: ...
@runtime_checkable
class WorkerRegistry(Protocol):
    def register(self,worker:Worker)->None: ...
    def resolve(self,worker_id:str)->Worker: ...
class InMemoryWorkerRegistry:
    def __init__(self): self._workers={}
    def register(self,worker):
        if not isinstance(worker,Worker): raise TypeError('worker')
        wid=worker.descriptor.worker_id
        if wid in self._workers: raise DuplicateWorkerError(wid)
        self._workers[wid]=worker
    def resolve(self,wid):
        if wid not in self._workers: raise WorkerNotFoundError(wid)
        return self._workers[wid]
class DistributedRuntimeCoordinator:
    def __init__(self,registry:WorkerRegistry): self._registry=registry
    def dispatch(self,worker_id,execution_plan): return self._registry.resolve(worker_id).accept(execution_plan)
