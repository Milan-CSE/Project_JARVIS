from enum import Enum


class PluginType(Enum):
    PERSONALITY = "personality"
    CAPABILITY = "capability"
    PROVIDER = "provider"
    INTERACTION = "interaction"
    WORKFLOW = "workflow"


class PluginState(Enum):
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    PAUSED = "paused"
    UNLOADED = "unloaded"
    FAILED = "failed"