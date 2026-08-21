from __future__ import annotations
from dataclasses import dataclass,field
from enum import Enum
from types import MappingProxyType
from typing import Any,Mapping,Protocol,runtime_checkable
class Modality(str,Enum): TEXT='text'; VOICE='voice'; VISION='vision'; DOCUMENT='document'; SCREEN='screen'; BROWSER='browser'; DEVICE='device'
@dataclass(frozen=True,slots=True)
class MultimodalInput:
    request_id:str; modality:Modality; content:Any; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.request_id.strip(): raise ValueError('request_id required')
        if not isinstance(self.modality,Modality): object.__setattr__(self,'modality',Modality(self.modality))
        if not isinstance(self.metadata,Mapping): raise TypeError('metadata must be a mapping')
        object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@dataclass(frozen=True,slots=True)
class MultimodalOutput:
    request_id:str; modality:Modality; content:Any; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.request_id.strip(): raise ValueError('request_id required')
        if not isinstance(self.modality,Modality): object.__setattr__(self,'modality',Modality(self.modality))
        if not isinstance(self.metadata,Mapping): raise TypeError('metadata must be a mapping')
        object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@runtime_checkable
class ModalityNormalizer(Protocol):
    def normalize(self,input:MultimodalInput)->Any: ...
class DefaultModalityNormalizer:
    def normalize(self,input):
        if not isinstance(input,MultimodalInput): raise TypeError('input must be MultimodalInput')
        return input.content
class MultimodalRouter:
    def __init__(self, normalizers:Mapping[Modality,ModalityNormalizer]|None=None): self._normalizers=dict(normalizers or {}); self._default=DefaultModalityNormalizer()
    def normalize(self,input:MultimodalInput)->Any:
        if input.modality in self._normalizers: return self._normalizers[input.modality].normalize(input)
        return self._default.normalize(input)
