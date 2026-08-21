from __future__ import annotations
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Any,Mapping,Protocol,runtime_checkable
class TenantError(RuntimeError): pass
class TenantConflictError(TenantError): pass
@dataclass(frozen=True,slots=True)
class Workspace:
    workspace_id:str; organization_id:str; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.workspace_id.strip() or not self.organization_id.strip(): raise ValueError('ids required')
        object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@dataclass(frozen=True,slots=True)
class TenantContext:
    tenant_id:str; workspace_id:str|None=None; user_id:str|None=None
    def __post_init__(self):
        if not self.tenant_id.strip(): raise ValueError('tenant_id required')
@runtime_checkable
class TenantIsolation(Protocol):
    def authorize_scope(self,context:TenantContext,tenant_id:str,workspace_id:str|None=None)->bool: ...
class DefaultTenantIsolation:
    def authorize_scope(self,context,tenant_id,workspace_id=None):
        if not isinstance(context,TenantContext): raise TypeError('context')
        return context.tenant_id==tenant_id and (workspace_id is None or context.workspace_id==workspace_id)
class TenantRegistry:
    def __init__(self): self._workspaces={}
    def register_workspace(self,w):
        if not isinstance(w,Workspace): raise TypeError('workspace')
        if w.workspace_id in self._workspaces: raise TenantConflictError(w.workspace_id)
        self._workspaces[w.workspace_id]=w
    def get(self,wid): return self._workspaces.get(wid)
