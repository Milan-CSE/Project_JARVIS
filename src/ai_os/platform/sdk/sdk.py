from __future__ import annotations
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Any,Mapping
from ai_os.tools import Tool,DefaultTool
from ai_os.runtime.tasks.task import Task
from ai_os.engines.engine import Engine
@dataclass(frozen=True,slots=True)
class SDKToolDefinition:
    tool:Tool
@dataclass(frozen=True,slots=True)
class SDKTaskDefinition:
    task:Task
@dataclass(frozen=True,slots=True)
class SDKEngineDefinition:
    engine:Engine
class DeveloperSDK:
    def create_tool(self,**kwargs)->SDKToolDefinition:
        return SDKToolDefinition(DefaultTool(**kwargs))
    def create_task(self,task:Task)->SDKTaskDefinition:
        if not isinstance(task,Task): raise TypeError('task must implement Task')
        return SDKTaskDefinition(task)
    def create_engine(self,engine:Engine)->SDKEngineDefinition:
        if not isinstance(engine,Engine): raise TypeError('engine must implement Engine')
        return SDKEngineDefinition(engine)
