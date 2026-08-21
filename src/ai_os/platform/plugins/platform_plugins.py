from __future__ import annotations
from dataclasses import dataclass,field
from enum import Enum
from types import MappingProxyType
from typing import Any,Mapping,Protocol,runtime_checkable
from ai_os.foundation.plugins.plugin import Plugin
from ai_os.foundation.plugins.manifest import PluginManifest
from ai_os.foundation.plugins.types import PluginType, PluginState
class PluginPlatformError(RuntimeError): pass
class PluginAlreadyInstalledError(PluginPlatformError): pass
class PluginNotFoundError(PluginPlatformError): pass
class PluginPlatformFrozenError(PluginPlatformError): pass
class PluginContributionError(PluginPlatformError): pass
@dataclass(frozen=True,slots=True)
class PluginContribution:
    contribution_id:str; kind:str; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.contribution_id.strip() or not self.kind.strip(): raise ValueError('contribution_id/kind required')
        object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@runtime_checkable
class PluginPlatform(Protocol):
    def install(self,plugin:Plugin)->None: ...
    def validate(self,plugin_id:str)->None: ...
    def load(self,plugin_id:str)->None: ...
    def initialize(self,plugin_id:str)->None: ...
    def pause(self,plugin_id:str)->None: ...
    def unload(self,plugin_id:str)->None: ...
    def remove(self,plugin_id:str)->None: ...
    def freeze(self)->None: ...
class DefaultPluginPlatform:
    def __init__(self): self._plugins={}; self._states={}; self._contrib={}; self._frozen=False
    @property
    def frozen(self): return self._frozen
    def install(self,plugin):
        if self._frozen: raise PluginPlatformFrozenError('plugin platform frozen')
        if not isinstance(plugin,Plugin): raise TypeError('plugin must implement Plugin')
        pid=plugin.manifest.plugin_id
        if pid in self._plugins: raise PluginAlreadyInstalledError(pid)
        self._plugins[pid]=plugin; self._states[pid]=PluginState.DISCOVERED
    def _get(self,pid):
        p=self._plugins.get(pid)
        if p is None: raise PluginNotFoundError(pid)
        return p
    def validate(self,pid):
        self._get(pid)
        if not isinstance(self._get(pid),Plugin): raise PluginPlatformError('invalid plugin')
        if self._states[pid] is not PluginState.DISCOVERED: raise PluginPlatformError('invalid transition')
        self._states[pid]=PluginState.VALIDATED
    def load(self,pid):
        p=self._get(pid); self._transition(pid,PluginState.LOADED,{PluginState.VALIDATED})
        try:p.load()
        except Exception as e:self._states[pid]=PluginState.FAILED; raise PluginPlatformError('plugin load failed') from e
    def initialize(self,pid):
        p=self._get(pid); self._transition(pid,PluginState.INITIALIZED,{PluginState.LOADED})
        try:p.initialize()
        except Exception as e:self._states[pid]=PluginState.FAILED; raise PluginPlatformError('plugin initialize failed') from e
    def pause(self,pid):
        p=self._get(pid); self._transition(pid,PluginState.PAUSED,{PluginState.INITIALIZED})
        try:p.pause()
        except Exception as e:self._states[pid]=PluginState.FAILED; raise PluginPlatformError('plugin pause failed') from e
    def unload(self,pid):
        p=self._get(pid); self._transition(pid,PluginState.UNLOADED,{PluginState.INITIALIZED,PluginState.PAUSED})
        try:p.unload()
        except Exception as e:self._states[pid]=PluginState.FAILED; raise PluginPlatformError('plugin unload failed') from e
    def remove(self,pid):
        if self._frozen: raise PluginPlatformFrozenError('plugin platform frozen')
        self._get(pid)
        if self._states[pid] not in {PluginState.UNLOADED,PluginState.FAILED}: raise PluginPlatformError('plugin must be unloaded before removal')
        self._plugins.pop(pid); self._states.pop(pid); self._contrib.pop(pid,None)
    def contribute(self,pid,contribution):
        if self._frozen: raise PluginPlatformFrozenError('plugin platform frozen')
        self._get(pid)
        if not isinstance(contribution,PluginContribution): raise TypeError('contribution')
        bucket=self._contrib.setdefault(pid,{})
        if contribution.contribution_id in bucket: raise PluginContributionError('duplicate contribution')
        bucket[contribution.contribution_id]=contribution
    def freeze(self): self._frozen=True
    def state(self,pid): return self._get(pid) and self._states[pid]
    def _transition(self,pid,new,allowed):
        if self._states[pid] not in allowed: raise PluginPlatformError('invalid plugin transition')
        self._states[pid]=new
