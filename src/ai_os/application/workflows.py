from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from ai_os.runtime.workflows import WorkflowRunner, Workflow
from ai_os.runtime.contracts import ExecutionResult
from ai_os.runtime.cancellation import CancellationToken
class WorkflowJobStatus(str,Enum): REGISTERED='registered'; RUNNING='running'; COMPLETED='completed'; FAILED='failed'; CANCELLED='cancelled'
@dataclass(frozen=True,slots=True)
class WorkflowJob:
    job_id:str; workflow:Workflow; parameters:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.job_id,str) or not self.job_id.strip(): raise ValueError('job_id required')
        if not isinstance(self.workflow,Workflow): raise TypeError('workflow must implement Workflow')
        if not isinstance(self.parameters,Mapping): raise TypeError('parameters must be a mapping')
        object.__setattr__(self,'parameters',MappingProxyType(dict(self.parameters)))
@dataclass(frozen=True,slots=True)
class WorkflowRun:
    job_id:str; status:WorkflowJobStatus; results:tuple[ExecutionResult,...]=(); metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.results,tuple): object.__setattr__(self,'results',tuple(self.results))
        if not all(isinstance(r,ExecutionResult) for r in self.results): raise TypeError('results must contain ExecutionResult instances')
        if not isinstance(self.metadata,Mapping): raise TypeError('metadata must be a mapping')
        object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
class LongRunningWorkflowManager:
    def __init__(self, runner: WorkflowRunner):
        if not isinstance(runner,WorkflowRunner): raise TypeError('runner must implement WorkflowRunner')
        self._runner=runner; self._jobs={}
    def register(self, job:WorkflowJob):
        if not isinstance(job,WorkflowJob): raise TypeError('job must be WorkflowJob')
        if job.job_id in self._jobs: raise ValueError(f'job already registered: {job.job_id}')
        self._jobs[job.job_id]=job
    def run(self, job_id:str, cancellation_token:CancellationToken|None=None)->WorkflowRun:
        job=self._jobs.get(job_id)
        if job is None: raise KeyError(job_id)
        if cancellation_token is not None and cancellation_token.is_cancelled: return WorkflowRun(job_id,WorkflowJobStatus.CANCELLED)
        try:
            results=self._runner.execute(job.workflow, job.parameters, cancellation_token)
            status=WorkflowJobStatus.CANCELLED if cancellation_token is not None and cancellation_token.is_cancelled else (WorkflowJobStatus.FAILED if any(r.status.value=='failed' for r in results) else WorkflowJobStatus.COMPLETED)
            return WorkflowRun(job_id,status,results,{'stage':'long_running_workflow'})
        except Exception:
            return WorkflowRun(job_id,WorkflowJobStatus.FAILED,metadata={'stage':'long_running_workflow'})
