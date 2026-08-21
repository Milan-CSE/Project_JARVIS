import unittest
from ai_os.platform.deployment import *
class A:
 def __init__(self): self.descriptor=DeploymentDescriptor(DeploymentMode.LOCAL,'dev'); self.calls=[]
 def start(self): self.calls.append('start')
 def stop(self): self.calls.append('stop')
class T(unittest.TestCase):
 def test_protocol(self): self.assertIsInstance(A(),DeploymentAdapter)
 def test_lifecycle(self):
  a=A(); m=DeploymentManager(a); m.start(); self.assertTrue(m.running); m.stop(); self.assertFalse(m.running); self.assertEqual(a.calls,['start','stop'])
 def test_modes(self): self.assertEqual({x.value for x in DeploymentMode},{'local','server','cloud','hybrid','edge'})
 def test_immutable_descriptor(self):
  d=DeploymentDescriptor('cloud','x',{'a':1})
  with self.assertRaises(AttributeError): d.name='y'
  with self.assertRaises(TypeError): d.metadata['a']=2
 def test_invalid_adapter(self):
  with self.assertRaises(TypeError): DeploymentManager(object())
 def test_no_runtime_override(self):
  m=DeploymentManager(A()); self.assertFalse(hasattr(m,'execute')); self.assertFalse(hasattr(m,'change_runtime_contract'))
if __name__=='__main__': unittest.main()
