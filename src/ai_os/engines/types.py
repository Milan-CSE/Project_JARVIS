from enum import Enum


class EngineType(Enum):
    PLANNING = "planning"
    DECISION = "decision"
    ROUTING = "routing"
    POLICY = "policy"
    WORKFLOW = "workflow"


class EngineStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"