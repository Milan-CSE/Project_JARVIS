from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable
class PersistenceError(RuntimeError): pass
class RecordNotFoundError(PersistenceError): pass
class DuplicateRecordError(PersistenceError): pass
@dataclass(frozen=True,slots=True)
class PersistenceRecord:
    namespace:str; key:str; value:Any; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not all(isinstance(x,str) and x.strip() for x in (self.namespace,self.key)): raise ValueError('namespace/key must be non-empty strings')
        object.__setattr__(self,'metadata',MappingProxyType(dict(self.metadata)))
@runtime_checkable
class PersistenceStore(Protocol):
    def save(self,record:PersistenceRecord,*,overwrite:bool=False)->None: ...
    def load(self,namespace:str,key:str)->PersistenceRecord: ...
    def delete(self,namespace:str,key:str)->None: ...
    def exists(self,namespace:str,key:str)->bool: ...
    def list_keys(self,namespace:str)->tuple[str,...]: ...
class InMemoryPersistenceStore:
    def __init__(self): self._records={}; self._frozen=False
    def save(self,record,*,overwrite=False):
        if not isinstance(record,PersistenceRecord): raise TypeError('record must be PersistenceRecord')
        k=(record.namespace,record.key)
        if k in self._records and not overwrite: raise DuplicateRecordError(record.key)
        self._records[k]=record
    def load(self,namespace,key):
        r=self._records.get((namespace,key))
        if r is None: raise RecordNotFoundError(key)
        return r
    def delete(self,namespace,key):
        if (namespace,key) not in self._records: raise RecordNotFoundError(key)
        del self._records[(namespace,key)]
    def exists(self,namespace,key): return (namespace,key) in self._records
    def list_keys(self,namespace): return tuple(k for (ns,k) in self._records if ns==namespace)
