import unittest
from ai_os.platform.multitenancy import *
class T(unittest.TestCase):
 def test_isolation_protocol(self): self.assertIsInstance(DefaultTenantIsolation(),TenantIsolation)
 def test_same_tenant(self): self.assertTrue(DefaultTenantIsolation().authorize_scope(TenantContext('t','w','u'),'t','w'))
 def test_cross_tenant_blocked(self): self.assertFalse(DefaultTenantIsolation().authorize_scope(TenantContext('t','w'),'other','w'))
 def test_workspace_blocked(self): self.assertFalse(DefaultTenantIsolation().authorize_scope(TenantContext('t','w'),'t','other'))
 def test_workspace_registry(self):
  r=TenantRegistry(); w=Workspace('w','o'); r.register_workspace(w); self.assertIs(r.get('w'),w)
 def test_duplicate_workspace(self):
  r=TenantRegistry(); w=Workspace('w','o'); r.register_workspace(w)
  with self.assertRaises(TenantConflictError): r.register_workspace(w)
 def test_immutable_context(self):
  c=TenantContext('t','w','u')
  with self.assertRaises(AttributeError): c.tenant_id='x'
 def test_no_identity_creation(self): self.assertFalse(hasattr(DefaultTenantIsolation(),'create_identity'))
if __name__=='__main__': unittest.main()
