from __future__ import annotations
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Any,Mapping,Protocol,runtime_checkable
class PackageError(RuntimeError): pass
class DuplicatePackageError(PackageError): pass
class PackageFrozenError(PackageError): pass
class CapabilityConflictError(PackageError): pass
@dataclass(frozen=True,slots=True)
class CapabilityDescriptor:
    capability_id:str; version:str; permissions:tuple[str,...]=(); dependencies:tuple[str,...]=(); metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.capability_id.strip() or not self.version.strip(): raise ValueError('capability_id/version required')
        object.__setattr__(self,'permissions',tuple(self.permissions)); object.__setattr__(self,'dependencies',tuple(self.dependencies)); object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@dataclass(frozen=True,slots=True)
class PlatformPackage:
    package_id:str; version:str; capabilities:tuple[CapabilityDescriptor,...]=(); metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.package_id.strip() or not self.version.strip(): raise ValueError('package_id/version required')
        object.__setattr__(self,'capabilities',tuple(self.capabilities)); object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@runtime_checkable
class PackageRegistry(Protocol):
    def register(self,package:PlatformPackage)->None: ...
    def resolve_capability(self,capability_id:str)->CapabilityDescriptor|None: ...
    def freeze(self)->None: ...
class DefaultPackageRegistry:
    def __init__(self): self._packages={}; self._caps={}; self._frozen=False
    def register(self,p):
        if self._frozen: raise PackageFrozenError('registry frozen')
        if not isinstance(p,PlatformPackage): raise TypeError('package')
        if p.package_id in self._packages: raise DuplicatePackageError(p.package_id)
        for c in p.capabilities:
            if c.capability_id in self._caps: raise CapabilityConflictError(c.capability_id)
        self._packages[p.package_id]=p
        for c in p.capabilities:self._caps[c.capability_id]=c
    def resolve_capability(self,cid): return self._caps.get(cid)
    def freeze(self): self._frozen=True
    @property
    def frozen(self): return self._frozen
