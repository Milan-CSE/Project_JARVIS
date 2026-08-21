from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable
from ai_os.identity import Identity
from ai_os.runtime.cancellation import CancellationToken
from ai_os.intelligence.context import IntelligenceContext, ContextItem
from ai_os.intelligence.context.source import ContextSource
from ai_os.intelligence.full_integration import FullIntelligenceIntegration, FullIntelligenceResult, FullIntelligenceStatus

@dataclass(frozen=True, slots=True)
class ApplicationRequest:
    request_id: str
    input: str
    identity_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.request_id, str) or not self.request_id.strip(): raise ValueError('request_id must be non-empty')
        if not isinstance(self.input, str) or not self.input.strip(): raise ValueError('input must be non-empty')
        if self.identity_id is not None and (not isinstance(self.identity_id, str) or not self.identity_id.strip()): raise ValueError('identity_id must be non-empty or None')
        if not isinstance(self.metadata, Mapping): raise TypeError('metadata must be a mapping')
        object.__setattr__(self, 'metadata', MappingProxyType(dict(self.metadata)))

@dataclass(frozen=True, slots=True)
class ApplicationResponse:
    request_id: str
    status: str
    message: str
    intelligence: FullIntelligenceResult
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.request_id, str) or not self.request_id.strip(): raise ValueError('request_id must be non-empty')
        if not isinstance(self.status, str) or not self.status.strip(): raise ValueError('status must be non-empty')
        if not isinstance(self.message, str) or not self.message.strip(): raise ValueError('message must be non-empty')
        if not isinstance(self.intelligence, FullIntelligenceResult): raise TypeError('intelligence must be FullIntelligenceResult')
        if not isinstance(self.metadata, Mapping): raise TypeError('metadata must be a mapping')
        object.__setattr__(self, 'metadata', MappingProxyType(dict(self.metadata)))

@runtime_checkable
class ApplicationContextProvider(Protocol):
    def build(self, request: ApplicationRequest, identity: Identity | None) -> IntelligenceContext: ...

@runtime_checkable
class IdentityLookup(Protocol):
    def resolve(self, identity_id: str) -> Identity | None: ...

class DefaultApplicationContextProvider:
    def build(self, request, identity):
        return IntelligenceContext(input=request.input, identity=identity, metadata=request.metadata)

class JARVISApplication:
    """13.1: application-level coordinator; owns no lower-layer semantics."""
    def __init__(self, intelligence: FullIntelligenceIntegration, context_provider: ApplicationContextProvider | None = None, identity_lookup: IdentityLookup | None = None):
        if not isinstance(intelligence, FullIntelligenceIntegration): raise TypeError('intelligence must be FullIntelligenceIntegration')
        if context_provider is None: context_provider = DefaultApplicationContextProvider()
        if not isinstance(context_provider, ApplicationContextProvider): raise TypeError('context_provider must implement ApplicationContextProvider')
        if identity_lookup is not None and not isinstance(identity_lookup, IdentityLookup): raise TypeError('identity_lookup must implement IdentityLookup')
        self._intelligence = intelligence; self._context_provider = context_provider; self._identity_lookup = identity_lookup
    def handle(self, request: ApplicationRequest, cancellation_token: CancellationToken | None = None) -> ApplicationResponse:
        if not isinstance(request, ApplicationRequest): raise TypeError('request must be ApplicationRequest')
        identity = None
        if request.identity_id is not None:
            if self._identity_lookup is None: raise ValueError('identity lookup is required when identity_id is supplied')
            identity = self._identity_lookup.resolve(request.identity_id)
            if identity is None: raise LookupError('identity not found')
        context = self._context_provider.build(request, identity)
        if not isinstance(context, IntelligenceContext): raise TypeError('context_provider must return IntelligenceContext')
        result = self._intelligence.run(context, cancellation_token=cancellation_token)
        if not isinstance(result, FullIntelligenceResult): raise TypeError('intelligence must return FullIntelligenceResult')
        message = result.response.response.content if result.response is not None else self._fallback_message(result.status)
        return ApplicationResponse(request_id=request.request_id, status=result.status.value, message=message, intelligence=result, metadata={'stage':'jarvis_application'})
    @staticmethod
    def _fallback_message(status):
        return {
            FullIntelligenceStatus.WAITING_FOR_EXECUTION: 'Request is prepared and waiting for execution.',
            FullIntelligenceStatus.CANCELLED: 'Request was cancelled.',
            FullIntelligenceStatus.BLOCKED: 'Request was blocked.',
            FullIntelligenceStatus.FAILED: 'Request failed.',
            FullIntelligenceStatus.EXECUTION_INCOMPLETE: 'Execution is incomplete.',
            FullIntelligenceStatus.AGENT_REJECTED: 'The execution request was rejected.',
            FullIntelligenceStatus.COMPLETED: 'Request completed.',
        }[status]
