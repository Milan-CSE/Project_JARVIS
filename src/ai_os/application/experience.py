from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable
from .core import ApplicationResponse
@dataclass(frozen=True, slots=True)
class AssistantProfile:
    name: str = 'JARVIS'
    greeting: str = 'How may I assist you?'
    style: str = 'professional'
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        for n in ('name','greeting','style'):
            v=getattr(self,n)
            if not isinstance(v,str) or not v.strip(): raise ValueError(f'{n} must be non-empty')
        if not isinstance(self.metadata, Mapping): raise TypeError('metadata must be a mapping')
        object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@runtime_checkable
class AssistantExperience(Protocol):
    @property
    def profile(self) -> AssistantProfile: ...
    def present(self, response: ApplicationResponse) -> str: ...
class DefaultAssistantExperience:
    def __init__(self, profile: AssistantProfile | None = None): self._profile=profile or AssistantProfile()
    @property
    def profile(self): return self._profile
    def present(self, response):
        if not isinstance(response, ApplicationResponse): raise TypeError('response must be ApplicationResponse')
        return response.message
