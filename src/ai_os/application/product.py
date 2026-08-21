from __future__ import annotations
from dataclasses import dataclass,field
from enum import Enum
from types import MappingProxyType
from typing import Any,Mapping,Protocol,runtime_checkable
class ProductState(str,Enum): STOPPED='stopped'; STARTING='starting'; READY='ready'; RUNNING='running'; STOPPING='stopping'; FAILED='failed'
@dataclass(frozen=True,slots=True)
class ProductManifest:
    product_id:str='jarvis'; name:str='JARVIS'; version:str='0.1.0'; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        for n in ('product_id','name','version'):
            if not isinstance(getattr(self,n),str) or not getattr(self,n).strip(): raise ValueError(f'{n} required')
        if not isinstance(self.metadata,Mapping): raise TypeError('metadata must be a mapping')
        object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@runtime_checkable
class ProductApplication(Protocol):
    def start(self)->None: ...
    def stop(self)->None: ...
class JARVISProduct:
    def __init__(self,application:ProductApplication,manifest:ProductManifest|None=None):
        if not isinstance(application,ProductApplication): raise TypeError('application must implement ProductApplication')
        self._application=application; self._manifest=manifest or ProductManifest(); self._state=ProductState.STOPPED
    @property
    def state(self): return self._state
    @property
    def manifest(self): return self._manifest
    def start(self):
        if self._state is not ProductState.STOPPED: raise RuntimeError('product is not stopped')
        self._state=ProductState.STARTING
        try: self._application.start()
        except Exception:
            self._state=ProductState.FAILED; raise
        self._state=ProductState.READY
    def run(self):
        if self._state is not ProductState.READY: raise RuntimeError('product must be ready to run')
        self._state=ProductState.RUNNING
    def stop(self):
        if self._state not in {ProductState.READY,ProductState.RUNNING,ProductState.FAILED}: raise RuntimeError('invalid stop transition')
        self._state=ProductState.STOPPING
        try: self._application.stop()
        except Exception:
            self._state=ProductState.FAILED; raise
        self._state=ProductState.STOPPED
