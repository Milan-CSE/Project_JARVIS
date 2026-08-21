from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, TypeVar, runtime_checkable
T = TypeVar('T')
class DependencyContainerError(RuntimeError): pass
class DuplicateServiceError(DependencyContainerError): pass
class MissingServiceError(DependencyContainerError): pass
class CircularDependencyError(DependencyContainerError): pass
class InvalidProviderError(DependencyContainerError): pass
class InvalidServiceError(DependencyContainerError): pass
class ContainerFrozenError(DependencyContainerError): pass
class ServiceLifetime(str, Enum):
    TRANSIENT='transient'; SINGLETON='singleton'
@runtime_checkable
class ServiceResolver(Protocol):
    def resolve(self, contract: type[T]) -> T: ...
@runtime_checkable
class ServiceProvider(Protocol):
    @property
    def dependencies(self) -> tuple[type[Any], ...]: ...
    def provide(self, resolver: ServiceResolver) -> object: ...
@runtime_checkable
class DependencyContainer(Protocol):
    def register(self, contract: type[T], provider: ServiceProvider, lifetime: ServiceLifetime=ServiceLifetime.TRANSIENT) -> None: ...
    def resolve(self, contract: type[T]) -> T: ...
    def freeze(self) -> None: ...
    @property
    def frozen(self) -> bool: ...
@dataclass(frozen=True, slots=True)
class _Registration:
    contract: type[Any]
    provider: ServiceProvider
    lifetime: ServiceLifetime
class DefaultDependencyContainer:
    def __init__(self) -> None:
        self._registrations={}; self._singletons={}; self._resolution_stack=[]; self._frozen=False
    @property
    def frozen(self): return self._frozen
    def register(self, contract, provider, lifetime=ServiceLifetime.TRANSIENT):
        self._ensure_open(); self._validate_contract(contract); self._validate_provider(provider)
        if not isinstance(lifetime, ServiceLifetime):
            try: lifetime=ServiceLifetime(lifetime)
            except (TypeError,ValueError) as e: raise ValueError('lifetime must be a valid ServiceLifetime') from e
        if contract in self._registrations: raise DuplicateServiceError(f'service already registered: {contract.__name__}')
        deps=self._provider_dependencies(provider)
        if contract in deps: raise CircularDependencyError(f"service '{contract.__name__}' depends on itself")
        self._registrations[contract]=_Registration(contract,provider,lifetime)
    def resolve(self, contract):
        self._validate_contract(contract); reg=self._registrations.get(contract)
        if reg is None: raise MissingServiceError(f'service not registered: {contract.__name__}')
        if reg.lifetime is ServiceLifetime.SINGLETON and contract in self._singletons:
            return self._validate_instance(contract,self._singletons[contract])
        if contract in self._resolution_stack: raise CircularDependencyError('circular dependency detected: ' + self._format_cycle(contract))
        self._resolution_stack.append(contract)
        try:
            for dep in self._provider_dependencies(reg.provider):
                if dep not in self._registrations:
                    raise MissingServiceError(f'missing dependency: {dep.__name__} required by {contract.__name__}{self._format_dependency_chain(dep)}')
                self.resolve(dep)
            try: instance=reg.provider.provide(self)
            except DependencyContainerError: raise
            except Exception as e: raise DependencyContainerError(f'failed to construct service: {contract.__name__}') from e
            instance=self._validate_instance(contract,instance)
            if reg.lifetime is ServiceLifetime.SINGLETON: self._singletons[contract]=instance
            return instance
        finally: self._resolution_stack.pop()
    def freeze(self):
        if self._frozen: return
        for contract,reg in self._registrations.items():
            for dep in self._provider_dependencies(reg.provider):
                if dep not in self._registrations: raise MissingServiceError(f'missing dependency: {dep.__name__} required by {contract.__name__}')
        self._validate_all_cycles(); self._frozen=True
    def _validate_all_cycles(self):
        visiting=set(); visited=set()
        def visit(c,path):
            if c in visiting:
                raise CircularDependencyError('circular dependency detected: ' + ' -> '.join(x.__name__ for x in (*path,c)))
            if c in visited: return
            visiting.add(c); reg=self._registrations.get(c)
            if reg is None: raise MissingServiceError(f'service not registered: {c.__name__}')
            for dep in self._provider_dependencies(reg.provider): visit(dep,(*path,c))
            visiting.remove(c); visited.add(c)
        for c in tuple(self._registrations): visit(c,())
    @staticmethod
    def _validate_contract(contract):
        if not isinstance(contract,type): raise TypeError('service contract must be a type')
    @staticmethod
    def _validate_provider(provider):
        if not isinstance(provider,ServiceProvider): raise InvalidProviderError('provider must implement ServiceProvider')
        deps=getattr(provider,'dependencies',None)
        if not isinstance(deps,tuple): raise InvalidProviderError('provider.dependencies must be a tuple')
        if not all(isinstance(d,type) for d in deps): raise InvalidProviderError('provider.dependencies must contain only types')
        if not callable(getattr(provider,'provide',None)): raise InvalidProviderError('provider must define provide()')
    @staticmethod
    def _provider_dependencies(provider):
        deps=provider.dependencies
        if len(set(deps)) != len(deps): raise InvalidProviderError('provider.dependencies must not contain duplicates')
        return deps
    @staticmethod
    def _validate_instance(contract,instance):
        if not isinstance(instance,contract): raise InvalidServiceError(f'provider returned invalid implementation for {contract.__name__}')
        return instance
    def _ensure_open(self):
        if self._frozen: raise ContainerFrozenError('dependency container is frozen')
    def _format_cycle(self,repeated):
        i=self._resolution_stack.index(repeated) if repeated in self._resolution_stack else 0
        return ' -> '.join(x.__name__ for x in (self._resolution_stack[i:]+[repeated]))
    def _format_dependency_chain(self,missing):
        if not self._resolution_stack: return ''
        return ' (dependency chain: ' + ' -> '.join(x.__name__ for x in (*self._resolution_stack,missing)) + ')'
