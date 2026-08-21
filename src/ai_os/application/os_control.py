from __future__ import annotations
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Any,Mapping,Protocol,runtime_checkable
@dataclass(frozen=True,slots=True)
class OSCapabilityRequest:
    request_id:str; capability:str; target:str|None=None; parameters:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.request_id.strip() or not self.capability.strip(): raise ValueError('request_id/capability required')
        if self.target is not None and (not isinstance(self.target,str) or not self.target.strip()): raise ValueError('target must be non-empty or None')
        if not isinstance(self.parameters,Mapping): raise TypeError('parameters must be a mapping')
        object.__setattr__(self,'parameters',MappingProxyType(dict(self.parameters)))
@dataclass(frozen=True,slots=True)
class OSCapabilityReceipt:
    request_id:str; accepted:bool; message:str; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.request_id.strip() or not isinstance(self.accepted,bool): raise ValueError('invalid receipt')
        if not isinstance(self.message,str) or not self.message.strip(): raise ValueError('message required')
        if not isinstance(self.metadata,Mapping): raise TypeError('metadata must be a mapping')
        object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@runtime_checkable
class OSCapabilityGateway(Protocol):
    def submit(self,request:OSCapabilityRequest)->OSCapabilityReceipt: ...
class ControlledOSApplication:
    def __init__(self,gateway:OSCapabilityGateway):
        if not isinstance(gateway,OSCapabilityGateway): raise TypeError('gateway must implement OSCapabilityGateway')
        self._gateway=gateway
    def request(self,request:OSCapabilityRequest)->OSCapabilityReceipt:
        if not isinstance(request,OSCapabilityRequest): raise TypeError('request must be OSCapabilityRequest')
        receipt=self._gateway.submit(request)
        if not isinstance(receipt,OSCapabilityReceipt): raise TypeError('gateway must return OSCapabilityReceipt')
        if receipt.request_id!=request.request_id: raise ValueError('request_id mismatch')
        return receipt
