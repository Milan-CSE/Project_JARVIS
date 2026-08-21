from __future__ import annotations
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Any,Callable,Mapping
from ai_os.runtime.cancellation import CancellationToken
@dataclass(frozen=True,slots=True)
class ReliabilityPolicy:
    max_attempts:int=1; retryable_exceptions:tuple[type[Exception],...]=(); metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if isinstance(self.max_attempts,bool) or not isinstance(self.max_attempts,int) or self.max_attempts<1: raise ValueError('max_attempts must be >= 1')
        if not isinstance(self.retryable_exceptions,tuple): object.__setattr__(self,'retryable_exceptions',tuple(self.retryable_exceptions))
        if not all(isinstance(x,type) and issubclass(x,Exception) for x in self.retryable_exceptions): raise TypeError('retryable_exceptions must contain Exception types')
        if not isinstance(self.metadata,Mapping): raise TypeError('metadata must be a mapping')
        object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@dataclass(frozen=True,slots=True)
class ReliabilityResult:
    attempts:int; value:Any=None; error:BaseException|None=None
class ReliabilityGuard:
    """13.9: bounded failure policy; no blind side-effect retries."""
    def __init__(self,policy:ReliabilityPolicy|None=None): self._policy=policy or ReliabilityPolicy()
    def run(self,operation:Callable[[],Any],*,idempotent:bool=False,cancellation_token:CancellationToken|None=None)->ReliabilityResult:
        if not callable(operation): raise TypeError('operation must be callable')
        attempts=0
        while attempts<self._policy.max_attempts:
            attempts+=1
            if cancellation_token is not None and cancellation_token.is_cancelled:
                return ReliabilityResult(attempts,error=RuntimeError('operation cancelled'))
            try: return ReliabilityResult(attempts,value=operation())
            except Exception as exc:
                retry_allowed=idempotent and isinstance(exc,self._policy.retryable_exceptions) and attempts<self._policy.max_attempts
                if not retry_allowed: return ReliabilityResult(attempts,error=exc)
        return ReliabilityResult(attempts,error=RuntimeError('reliability guard exhausted'))
