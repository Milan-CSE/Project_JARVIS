from __future__ import annotations
import unittest
from ai_os.tools import DefaultTool, DefaultToolSecurityPolicy, SecurityDecision, ToolSecurity, ToolSecurityPolicy
from ai_os.identity import Identity, IdentityType
from ai_os.foundation.security.security import SecurityContext

class WrongPolicy:
    def authorize(self, identity, tool, security_context):
        return "invalid"

class RaisingPolicy:
    def authorize(self, identity, tool, security_context):
        raise RuntimeError("policy failure")

class MismatchPolicy:
    def authorize(self, identity, tool, security_context):
        return SecurityDecision(True, "wrong", tool.tool_id, tool.capability, tuple(tool.required_permissions), (), "authorized")

class BadDecisionPolicy:
    def authorize(self, identity, tool, security_context):
        return SecurityDecision(False, identity.identity_id, tool.tool_id, tool.capability, tuple(tool.required_permissions), tuple(tool.required_permissions), "denied")

class ToolSecurityTests(unittest.TestCase):
    def tool(self, permissions=()):
        return DefaultTool("tool.test", "Test", "1.0", "Test tool", "test.action", required_permissions=permissions)
    def identity(self, principal="user:1"):
        return Identity("identity:1", principal, IdentityType.USER)
    def context(self, principal="user:1", authenticated=True):
        return SecurityContext(principal=principal, authenticated=authenticated)
    def test_policy_matches_contract(self):
        self.assertIsInstance(DefaultToolSecurityPolicy({}), ToolSecurityPolicy)
    def test_invalid_policy_rejected(self):
        with self.assertRaises(TypeError): ToolSecurity(object())
    def test_authenticated_with_all_permissions_allowed(self):
        d = ToolSecurity(DefaultToolSecurityPolicy({"user:1": {"test.read", "test.write"}})).authorize(self.identity(), self.tool(("test.read", "test.write")), self.context())
        self.assertTrue(d.allowed); self.assertEqual(d.missing_permissions, ())
    def test_missing_one_permission_denied(self):
        d = ToolSecurity(DefaultToolSecurityPolicy({"user:1": {"test.read"}})).authorize(self.identity(), self.tool(("test.read", "test.write")), self.context())
        self.assertFalse(d.allowed); self.assertEqual(d.missing_permissions, ("test.write",))
    def test_missing_all_permissions_denied(self):
        d = ToolSecurity(DefaultToolSecurityPolicy({})).authorize(self.identity(), self.tool(("test.read", "test.write")), self.context())
        self.assertFalse(d.allowed); self.assertEqual(set(d.missing_permissions), {"test.read", "test.write"})
    def test_no_required_permissions_allowed_when_authenticated(self):
        d = ToolSecurity(DefaultToolSecurityPolicy({})).authorize(self.identity(), self.tool(()), self.context())
        self.assertTrue(d.allowed)
    def test_unauthenticated_denied(self):
        d = ToolSecurity(DefaultToolSecurityPolicy({"user:1": {"test.read"}})).authorize(self.identity(), self.tool(("test.read",)), self.context(authenticated=False))
        self.assertFalse(d.allowed)
    def test_principal_mismatch_denied(self):
        d = ToolSecurity(DefaultToolSecurityPolicy({"user:1": {"test.read"}})).authorize(self.identity("user:1"), self.tool(("test.read",)), self.context("user:2", True))
        self.assertFalse(d.allowed)
    def test_unknown_principal_denied(self):
        d = ToolSecurity(DefaultToolSecurityPolicy({})).authorize(self.identity("user:unknown"), self.tool(("test.read",)), self.context("user:unknown", True))
        self.assertFalse(d.allowed)
    def test_exact_match_only(self):
        d = ToolSecurity(DefaultToolSecurityPolicy({"user:1": {"test.read.extra"}})).authorize(self.identity(), self.tool(("test.read",)), self.context())
        self.assertFalse(d.allowed)
    def test_no_wildcard_semantics(self):
        d = ToolSecurity(DefaultToolSecurityPolicy({"user:1": {"test.*"}})).authorize(self.identity(), self.tool(("test.read",)), self.context())
        self.assertFalse(d.allowed)
    def test_capability_does_not_grant_permission(self):
        d = ToolSecurity(DefaultToolSecurityPolicy({"user:1": {"test.action"}})).authorize(self.identity(), self.tool(("test.action",)), self.context())
        self.assertTrue(d.allowed)
        d2 = ToolSecurity(DefaultToolSecurityPolicy({"user:1": {}})).authorize(self.identity(), self.tool(("test.action",)), self.context())
        self.assertFalse(d2.allowed)
    def test_identity_tool_capability_preserved(self):
        t = self.tool(("test.read",)); i = self.identity()
        d = ToolSecurity(DefaultToolSecurityPolicy({"user:1": {"test.read"}})).authorize(i, t, self.context())
        self.assertEqual((d.identity_id,d.tool_id,d.capability),(i.identity_id,t.tool_id,t.capability))
    def test_decision_is_immutable(self):
        d = ToolSecurity(DefaultToolSecurityPolicy({})).authorize(self.identity(), self.tool(()), self.context())
        with self.assertRaises(AttributeError): d.allowed = False
    def test_decision_metadata_immutable(self):
        d = SecurityDecision(True,"i","t","c",(),(),"authorized",{"x":1})
        with self.assertRaises(TypeError): d.metadata["x"] = 2
    def test_invalid_identity_rejected(self):
        with self.assertRaises(TypeError): ToolSecurity(DefaultToolSecurityPolicy({})).authorize(object(), self.tool(), self.context())
    def test_invalid_tool_rejected(self):
        with self.assertRaises(TypeError): ToolSecurity(DefaultToolSecurityPolicy({})).authorize(self.identity(), object(), self.context())
    def test_invalid_security_context_rejected(self):
        with self.assertRaises(TypeError): ToolSecurity(DefaultToolSecurityPolicy({})).authorize(self.identity(), self.tool(), object())
    def test_wrong_policy_result_rejected(self):
        with self.assertRaises(TypeError): ToolSecurity(WrongPolicy()).authorize(self.identity(), self.tool(), self.context())
    def test_policy_exception_propagates(self):
        with self.assertRaises(RuntimeError): ToolSecurity(RaisingPolicy()).authorize(self.identity(), self.tool(), self.context())
    def test_policy_decision_identity_mismatch_rejected(self):
        with self.assertRaises(ValueError): ToolSecurity(MismatchPolicy()).authorize(self.identity(), self.tool(), self.context())
    def test_policy_missing_permission_decision_is_accepted(self):
        d = ToolSecurity(BadDecisionPolicy()).authorize(self.identity(), self.tool(("p",)), self.context())
        self.assertFalse(d.allowed)
    def test_policy_is_reusable(self):
        s=ToolSecurity(DefaultToolSecurityPolicy({"user:1":{"p"}})); self.assertTrue(s.authorize(self.identity(),self.tool(("p",)),self.context()).allowed); self.assertFalse(s.authorize(self.identity("user:2"),self.tool(("p",)),self.context("user:2",True)).allowed)
    def test_security_object_has_no_execute(self):
        self.assertFalse(hasattr(ToolSecurity(DefaultToolSecurityPolicy({})),"execute"))
    def test_security_object_has_no_task_execution(self):
        s=ToolSecurity(DefaultToolSecurityPolicy({})); self.assertFalse(hasattr(s,"execute_step")); self.assertFalse(hasattr(s,"run_task"))
    def test_security_object_has_no_workflow_runner(self):
        s=ToolSecurity(DefaultToolSecurityPolicy({})); self.assertFalse(hasattr(s,"workflow_runner")); self.assertFalse(hasattr(s,"execute_workflow"))
    def test_security_object_has_no_intelligence_methods(self):
        s=ToolSecurity(DefaultToolSecurityPolicy({})); self.assertFalse(hasattr(s,"reason")); self.assertFalse(hasattr(s,"plan")); self.assertFalse(hasattr(s,"decide")); self.assertFalse(hasattr(s,"replan"))
    def test_security_object_has_no_plugin_lifecycle(self):
        s=ToolSecurity(DefaultToolSecurityPolicy({})); self.assertFalse(hasattr(s,"load")); self.assertFalse(hasattr(s,"initialize")); self.assertFalse(hasattr(s,"unload"))
    def test_security_object_has_no_registry_mutation(self):
        s=ToolSecurity(DefaultToolSecurityPolicy({})); self.assertFalse(hasattr(s,"register")); self.assertFalse(hasattr(s,"freeze"))
    def test_policy_is_stateless_across_calls(self):
        s=ToolSecurity(DefaultToolSecurityPolicy({"user:1":{"p"}})); a=s.authorize(self.identity(),self.tool(("p",)),self.context()); b=s.authorize(self.identity("user:2"),self.tool(("p",)),self.context("user:2",True)); self.assertTrue(a.allowed); self.assertFalse(b.allowed)
    def test_denial_does_not_retry_or_escalate(self):
        s=ToolSecurity(DefaultToolSecurityPolicy({})); d=s.authorize(self.identity(),self.tool(("p",)),self.context()); self.assertFalse(d.allowed); self.assertEqual(d.missing_permissions,("p",))
    def test_required_permissions_are_not_grants(self):
        t=self.tool(("p",)); d=ToolSecurity(DefaultToolSecurityPolicy({})).authorize(self.identity(),t,self.context()); self.assertFalse(d.allowed)
    def test_security_decision_denied_requires_reason(self):
        with self.assertRaises(ValueError): SecurityDecision(False,"i","t","c",(),(),"")
    def test_allowed_decision_cannot_have_missing_permissions(self):
        with self.assertRaises(ValueError): SecurityDecision(True,"i","t","c",("p",),("p",),"authorized")
    def test_missing_permissions_subset_required(self):
        with self.assertRaises(ValueError): SecurityDecision(False,"i","t","c",("p",),("q",),"denied")
    def test_duplicate_required_permissions_rejected(self):
        with self.assertRaises(ValueError): SecurityDecision(True,"i","t","c",("p","p"),(),"authorized")

if __name__ == "__main__": unittest.main(verbosity=2)
