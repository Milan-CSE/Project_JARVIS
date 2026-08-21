import unittest
from ai_os.platform.distributed import *
class W:
 def __init__(self): self.descriptor=WorkerDescriptor('w','1',('execute',)); self.plans=[]
 def accept(self,p): self.plans.append(p); return 'accepted'
class T(unittest.TestCase):
 def test_protocols(self): self.assertIsInstance(W(),Worker); self.assertIsInstance(InMemoryWorkerRegistry(),WorkerRegistry)
 def test_register_dispatch(self):
  w=W(); r=InMemoryWorkerRegistry(); r.register(w); self.assertEqual(DistributedRuntimeCoordinator(r).dispatch('w','plan'),'accepted'); self.assertEqual(w.plans,['plan'])
 def test_duplicate(self):
  r=InMemoryWorkerRegistry(); r.register(W())
  with self.assertRaises(DuplicateWorkerError): r.register(W())
 def test_missing(self):
  with self.assertRaises(WorkerNotFoundError): InMemoryWorkerRegistry().resolve('x')
 def test_descriptor_immutable(self):
  d=WorkerDescriptor('w','1',metadata={'x':1})
  with self.assertRaises(AttributeError): d.worker_id='x'
 def test_no_intelligence(self):
  r=InMemoryWorkerRegistry(); c=DistributedRuntimeCoordinator(r); self.assertFalse(hasattr(c,'reason')); self.assertFalse(hasattr(c,'plan'))
 def test_no_tool_execution_api(self):
  r=InMemoryWorkerRegistry(); self.assertFalse(hasattr(r,'execute_tool'))
if __name__=='__main__': unittest.main()
