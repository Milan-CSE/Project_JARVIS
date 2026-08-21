from __future__ import annotations
import unittest
from ai_os.tools import (
    DefaultTool, DefaultToolRegistry, DefaultToolLifecycleValidator,
    ToolLifecycleManager, ToolLifecycleState, ToolLifecycleValidator,
    ToolLifecycleTransitionError, ToolLifecycleValidationError,
    ToolNotFoundError,
)

class TrackingValidator:
    def __init__(self, fail=False): self.calls=0; self.tools=[]; self.fail=fail
    def validate(self, tool):
        self.calls += 1; self.tools.append(tool)
        if self.fail: raise ValueError("bad")
class MissingValidate: pass
class BadRegistry: pass
class BadReturnedRegistry:
    def register(self, tool): pass
    def resolve(self, tool_id): return object()
    def resolve_capability(self, capability): return ()
    def contains(self, tool_id): return False
    def list_tools(self): return ()
    def freeze(self): pass
class RaisingValidator:
    def validate(self, tool): raise RuntimeError("crash")

class ToolLifecycleTests(unittest.TestCase):
    def tool(self, tool_id="tool:test", version="1.0"):
        return DefaultTool(tool_id=tool_id,name="Test Tool",version=version,
                           description="Test",capability="test.capability")
    def registry(self,*tools):
        r=DefaultToolRegistry()
        for t in tools:r.register(t)
        return r
    def manager(self,*tools,validator=None):
        return ToolLifecycleManager(self.registry(*tools),validator=validator)

    def test_default_validator_matches_contract(self):
        self.assertIsInstance(DefaultToolLifecycleValidator(),ToolLifecycleValidator)
    def test_missing_validate_does_not_match(self):
        self.assertFalse(isinstance(MissingValidate(),ToolLifecycleValidator))
    def test_invalid_registry_rejected(self):
        with self.assertRaises(TypeError): ToolLifecycleManager(BadRegistry())
    def test_invalid_validator_rejected(self):
        with self.assertRaises(TypeError): ToolLifecycleManager(self.registry(self.tool()),object())

    def test_initial_state_registered(self):
        t=self.tool(); self.assertEqual(self.manager(t).get_state(t.tool_id),ToolLifecycleState.REGISTERED)
    def test_unknown_state_is_none(self): self.assertIsNone(self.manager().get_state("tool:missing"))
    def test_unknown_operations_raise(self):
        m=self.manager()
        for op in (m.validate,m.enable,m.disable,m.deprecate):
            with self.subTest(op=op.__name__):
                with self.assertRaises(ToolNotFoundError): op("tool:missing")
    def test_bad_tool_id(self):
        with self.assertRaises(ValueError): self.manager().get_state(" ")
        with self.assertRaises(ValueError): self.manager().get_state(1)
    def test_registry_owns_registration(self): self.assertFalse(hasattr(self.manager(),"register"))
    def test_registry_owns_discovery(self): self.assertFalse(hasattr(self.manager(),"discover"))

    def test_validate_registered_to_validated(self):
        t=self.tool();m=self.manager(t);m.validate(t.tool_id);self.assertEqual(m.get_state(t.tool_id),ToolLifecycleState.VALIDATED)
    def test_validator_called_once(self):
        t=self.tool();v=TrackingValidator();self.manager(t,validator=v).validate(t.tool_id);self.assertEqual(v.calls,1)
    def test_validator_gets_exact_tool(self):
        t=self.tool();v=TrackingValidator();self.manager(t,validator=v).validate(t.tool_id);self.assertIs(v.tools[0],t)
    def test_validation_failure_sets_failed(self):
        t=self.tool();
        m=self.manager(t,validator=TrackingValidator(True))
        with self.assertRaises(ToolLifecycleValidationError):m.validate(t.tool_id)
        self.assertEqual(m.get_state(t.tool_id),ToolLifecycleState.FAILED)
    def test_validator_exception_normalized(self):
        t=self.tool();m=self.manager(t,validator=RaisingValidator())
        with self.assertRaises(ToolLifecycleValidationError):m.validate(t.tool_id)
        self.assertEqual(m.get_state(t.tool_id),ToolLifecycleState.FAILED)
    def test_failed_cannot_revalidate(self):
        t=self.tool();m=self.manager(t,validator=TrackingValidator(True))
        with self.assertRaises(ToolLifecycleValidationError):m.validate(t.tool_id)
        with self.assertRaises(ToolLifecycleTransitionError):m.validate(t.tool_id)

    def test_registered_cannot_enable(self):
        t=self.tool();
        with self.assertRaises(ToolLifecycleTransitionError): self.manager(t).enable(t.tool_id)
    def test_validated_can_enable(self):
        t=self.tool();m=self.manager(t);m.validate(t.tool_id);m.enable(t.tool_id);self.assertEqual(m.get_state(t.tool_id),ToolLifecycleState.ENABLED)
    def test_validated_can_disable(self):
        t=self.tool();m=self.manager(t);m.validate(t.tool_id);m.disable(t.tool_id);self.assertEqual(m.get_state(t.tool_id),ToolLifecycleState.DISABLED)
    def test_enabled_can_disable(self):
        t=self.tool();m=self.manager(t);m.validate(t.tool_id);m.enable(t.tool_id);m.disable(t.tool_id);self.assertEqual(m.get_state(t.tool_id),ToolLifecycleState.DISABLED)
    def test_disabled_can_enable(self):
        t=self.tool();m=self.manager(t);m.validate(t.tool_id);m.disable(t.tool_id);m.enable(t.tool_id);self.assertEqual(m.get_state(t.tool_id),ToolLifecycleState.ENABLED)
    def test_enabled_cannot_validate(self):
        t=self.tool();m=self.manager(t);m.validate(t.tool_id);m.enable(t.tool_id)
        with self.assertRaises(ToolLifecycleTransitionError):m.validate(t.tool_id)
    def test_registered_cannot_disable(self):
        t=self.tool();
        with self.assertRaises(ToolLifecycleTransitionError):self.manager(t).disable(t.tool_id)

    def test_validated_can_deprecate(self):
        t=self.tool();m=self.manager(t);m.validate(t.tool_id);m.deprecate(t.tool_id);self.assertEqual(m.get_state(t.tool_id),ToolLifecycleState.DEPRECATED)
    def test_enabled_can_deprecate(self):
        t=self.tool();m=self.manager(t);m.validate(t.tool_id);m.enable(t.tool_id);m.deprecate(t.tool_id);self.assertEqual(m.get_state(t.tool_id),ToolLifecycleState.DEPRECATED)
    def test_disabled_can_deprecate(self):
        t=self.tool();m=self.manager(t);m.validate(t.tool_id);m.disable(t.tool_id);m.deprecate(t.tool_id);self.assertEqual(m.get_state(t.tool_id),ToolLifecycleState.DEPRECATED)
    def test_registered_cannot_deprecate(self):
        t=self.tool();
        with self.assertRaises(ToolLifecycleTransitionError):self.manager(t).deprecate(t.tool_id)
    def test_deprecated_terminal(self):
        t=self.tool();m=self.manager(t);m.validate(t.tool_id);m.enable(t.tool_id);m.deprecate(t.tool_id)
        for op in (m.validate,m.enable,m.disable,m.deprecate):
            with self.subTest(op=op.__name__):
                with self.assertRaises(ToolLifecycleTransitionError):op(t.tool_id)

    def test_failed_cannot_enable_disable_deprecate(self):
        t=self.tool();m=self.manager(t,validator=TrackingValidator(True))
        with self.assertRaises(ToolLifecycleValidationError):m.validate(t.tool_id)
        for op in (m.enable,m.disable,m.deprecate):
            with self.subTest(op=op.__name__):
                with self.assertRaises(ToolLifecycleTransitionError):op(t.tool_id)

    def test_version_not_mutated(self):
        t=self.tool(version="2.5");m=self.manager(t);m.validate(t.tool_id);m.enable(t.tool_id);m.disable(t.tool_id);m.deprecate(t.tool_id);self.assertEqual(t.version,"2.5")
    def test_no_upgrade_or_set_version(self):
        m=self.manager(self.tool());self.assertFalse(hasattr(m,"upgrade"));self.assertFalse(hasattr(m,"set_version"))
    def test_versions_independent(self):
        a=self.tool("tool:v1","1.0");b=self.tool("tool:v2","2.0");m=self.manager(a,b);m.validate(a.tool_id);m.enable(a.tool_id);self.assertEqual(m.get_state(a.tool_id),ToolLifecycleState.ENABLED);self.assertEqual(m.get_state(b.tool_id),ToolLifecycleState.REGISTERED)

    def test_list_states_initial(self):
        a=self.tool("tool:a");b=self.tool("tool:b");m=self.manager(a,b);s=m.list_states();self.assertEqual(s["tool:a"],ToolLifecycleState.REGISTERED);self.assertEqual(s["tool:b"],ToolLifecycleState.REGISTERED)
    def test_list_states_immutable(self):
        t=self.tool();s=self.manager(t).list_states()
        with self.assertRaises(TypeError):s[t.tool_id]=ToolLifecycleState.ENABLED
    def test_state_snapshot_is_copy(self):
        t=self.tool();m=self.manager(t);s=m.list_states();m.validate(t.tool_id);self.assertEqual(s[t.tool_id],ToolLifecycleState.REGISTERED);self.assertEqual(m.get_state(t.tool_id),ToolLifecycleState.VALIDATED)
    def test_new_registry_tool_visible(self):
        a=self.tool("tool:a");r=self.registry(a);m=ToolLifecycleManager(r);b=self.tool("tool:b");r.register(b);self.assertEqual(m.get_state(b.tool_id),ToolLifecycleState.REGISTERED)
    def test_invalid_tool_from_registry_rejected(self):
        with self.assertRaises(TypeError):ToolLifecycleManager(BadReturnedRegistry()).get_state("tool:test")

    def test_tool_not_mutated(self):
        t=self.tool();before=(t.tool_id,t.name,t.version,t.description,t.capability,t.required_permissions,t.metadata);m=self.manager(t);m.validate(t.tool_id);m.enable(t.tool_id);m.disable(t.tool_id);m.deprecate(t.tool_id);after=(t.tool_id,t.name,t.version,t.description,t.capability,t.required_permissions,t.metadata);self.assertEqual(before,after)
    def test_no_execution_api(self):
        m=self.manager(self.tool());self.assertFalse(hasattr(m,"execute"));self.assertFalse(hasattr(m,"execute_tool"))
    def test_no_scheduling_api(self):
        m=self.manager(self.tool());self.assertFalse(hasattr(m,"schedule"));self.assertFalse(hasattr(m,"scheduler"))
    def test_no_workflow_api(self):
        m=self.manager(self.tool());self.assertFalse(hasattr(m,"build_steps"));self.assertFalse(hasattr(m,"run_workflow"))
    def test_no_task_api(self):
        m=self.manager(self.tool());self.assertFalse(hasattr(m,"register_task"));self.assertFalse(hasattr(m,"task_registry"))
    def test_no_security_api(self):
        m=self.manager(self.tool());self.assertFalse(hasattr(m,"authorize"));self.assertFalse(hasattr(m,"security_context"))
    def test_no_identity_api(self):
        m=self.manager(self.tool());self.assertFalse(hasattr(m,"identity"));self.assertFalse(hasattr(m,"current_identity"))
    def test_no_intelligence_api(self):
        m=self.manager(self.tool())
        for name in ("reason","plan","decide","replan"):self.assertFalse(hasattr(m,name))
    def test_no_plugin_lifecycle_api(self):
        m=self.manager(self.tool())
        for name in ("load_plugin","initialize_plugin","pause_plugin","unload_plugin"):self.assertFalse(hasattr(m,name))

    def test_manager_reusable(self):
        a=self.tool("tool:a");b=self.tool("tool:b");m=self.manager(a,b);m.validate(a.tool_id);m.enable(a.tool_id);m.validate(b.tool_id);m.disable(b.tool_id);self.assertEqual(m.get_state(a.tool_id),ToolLifecycleState.ENABLED);self.assertEqual(m.get_state(b.tool_id),ToolLifecycleState.DISABLED)
    def test_states_do_not_leak_between_managers(self):
        t=self.tool();r=self.registry(t);a=ToolLifecycleManager(r);b=ToolLifecycleManager(r);a.validate(t.tool_id);a.enable(t.tool_id);self.assertEqual(a.get_state(t.tool_id),ToolLifecycleState.ENABLED);self.assertEqual(b.get_state(t.tool_id),ToolLifecycleState.REGISTERED)
    def test_default_validator_does_not_authorize_or_execute(self):
        v=DefaultToolLifecycleValidator();self.assertFalse(hasattr(v,"authorize"));self.assertFalse(hasattr(v,"execute"));self.assertFalse(hasattr(v,"run"))

if __name__ == "__main__": unittest.main(verbosity=2)
