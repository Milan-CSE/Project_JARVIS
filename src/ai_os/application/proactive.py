from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable
@dataclass(frozen=True,slots=True)
class ProactiveEvent:
    event_id:str; event_type:str; payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.event_id.strip() or not self.event_type.strip(): raise ValueError('event_id/event_type required')
        if not isinstance(self.payload,Mapping): raise TypeError('payload must be a mapping')
        object.__setattr__(self,'payload',MappingProxyType(dict(self.payload)))
@dataclass(frozen=True,slots=True)
class ProactiveDecision:
    should_notify:bool; should_trigger:bool=False; reason:str=''; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.should_notify,bool) or not isinstance(self.should_trigger,bool): raise TypeError('flags must be bool')
        if not isinstance(self.reason,str): raise TypeError('reason must be string')
        if not isinstance(self.metadata,Mapping): raise TypeError('metadata must be a mapping')
        object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@runtime_checkable
class ProactivePolicy(Protocol):
    def evaluate(self,event:ProactiveEvent)->ProactiveDecision: ...
@runtime_checkable
class ProactiveNotifier(Protocol):
    def notify(self,event:ProactiveEvent,decision:ProactiveDecision)->None: ...
@runtime_checkable
class ProactiveTriggerChannel(Protocol):
    def trigger(self,event:ProactiveEvent,decision:ProactiveDecision)->None: ...
class ProactiveManager:
    def __init__(self,policy:ProactivePolicy,notifier:ProactiveNotifier|None=None,trigger:ProactiveTriggerChannel|None=None):
        if not isinstance(policy,ProactivePolicy): raise TypeError('policy must implement ProactivePolicy')
        if notifier is not None and not isinstance(notifier,ProactiveNotifier): raise TypeError('notifier must implement ProactiveNotifier')
        if trigger is not None and not isinstance(trigger,ProactiveTriggerChannel): raise TypeError('trigger must implement ProactiveTriggerChannel')
        self._policy=policy; self._notifier=notifier; self._trigger=trigger
    def process(self,event:ProactiveEvent)->ProactiveDecision:
        if not isinstance(event,ProactiveEvent): raise TypeError('event must be ProactiveEvent')
        decision=self._policy.evaluate(event)
        if decision.should_notify:
            if self._notifier is None: raise RuntimeError('notification requested but no notifier is configured')
            self._notifier.notify(event,decision)
        if decision.should_trigger:
            if self._trigger is None: raise RuntimeError('trigger requested but no trigger channel is configured')
            self._trigger.trigger(event,decision)
        return decision
