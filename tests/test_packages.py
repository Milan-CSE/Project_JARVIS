import unittest
from ai_os.platform.packages import *
class T(unittest.TestCase):
 def test_protocol(self): self.assertIsInstance(DefaultPackageRegistry(),PackageRegistry)
 def test_register_resolve(self):
  r=DefaultPackageRegistry(); c=CapabilityDescriptor('x','1',('read',),('dep',)); r.register(PlatformPackage('p','1',(c,))); self.assertIs(r.resolve_capability('x'),c)
 def test_duplicate_package(self):
  r=DefaultPackageRegistry(); p=PlatformPackage('p','1'); r.register(p)
  with self.assertRaises(DuplicatePackageError): r.register(p)
 def test_capability_conflict(self):
  r=DefaultPackageRegistry(); c=CapabilityDescriptor('x','1'); r.register(PlatformPackage('p1','1',(c,)))
  with self.assertRaises(CapabilityConflictError): r.register(PlatformPackage('p2','1',(CapabilityDescriptor('x','2'),)))
 def test_freeze(self):
  r=DefaultPackageRegistry(); r.freeze()
  with self.assertRaises(PackageFrozenError): r.register(PlatformPackage('p','1'))
 def test_immutable(self):
  c=CapabilityDescriptor('x','1',metadata={'a':1})
  with self.assertRaises(AttributeError): c.version='2'
  with self.assertRaises(TypeError): c.metadata['a']=2
 def test_no_execution(self):
  r=DefaultPackageRegistry(); self.assertFalse(hasattr(r,'execute')); self.assertFalse(hasattr(r,'run'))
if __name__=='__main__': unittest.main()
