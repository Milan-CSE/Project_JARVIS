import unittest
from ai_os.platform.persistence import *
class T(unittest.TestCase):
 def test_protocol(self): self.assertIsInstance(InMemoryPersistenceStore(),PersistenceStore)
 def test_save_load(self):
  s=InMemoryPersistenceStore(); r=PersistenceRecord('x','a',{'v':1}); s.save(r); self.assertIs(s.load('x','a'),r)
 def test_duplicate(self):
  s=InMemoryPersistenceStore(); r=PersistenceRecord('x','a',1); s.save(r)
  with self.assertRaises(DuplicateRecordError): s.save(r)
 def test_overwrite(self):
  s=InMemoryPersistenceStore(); s.save(PersistenceRecord('x','a',1)); s.save(PersistenceRecord('x','a',2),overwrite=True); self.assertEqual(s.load('x','a').value,2)
 def test_missing(self):
  with self.assertRaises(RecordNotFoundError): InMemoryPersistenceStore().load('x','a')
 def test_immutable(self):
  r=PersistenceRecord('x','a',1,{'x':1})
  with self.assertRaises(AttributeError): r.key='b'
  with self.assertRaises(TypeError): r.metadata['x']=2
 def test_namespace_isolation(self):
  s=InMemoryPersistenceStore(); s.save(PersistenceRecord('a','x',1)); s.save(PersistenceRecord('b','x',2)); self.assertEqual(s.list_keys('a'),('x',))
 def test_no_execution(self):
  s=InMemoryPersistenceStore(); self.assertFalse(hasattr(s,'execute')); self.assertFalse(hasattr(s,'run'))
if __name__=='__main__': unittest.main()
