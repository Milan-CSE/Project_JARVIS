import unittest
from ai_os.foundation.dependencies import *
class A: pass
class B:
    def __init__(self,a): self.a=a
class C:
    def __init__(self,b): self.b=b
class D:
    def __init__(self,b,c): self.b=b; self.c=c
class P:
    def __init__(self,deps=(),factory=None): self._d=tuple(deps); self.factory=factory; self.calls=0
    @property
    def dependencies(self): return self._d
    def provide(self,r): self.calls+=1; return self.factory(r) if self.factory else object()
class AP:
    @property
    def dependencies(self): return ()
    def provide(self,r): return A()
class BP:
    @property
    def dependencies(self): return (A,)
    def provide(self,r): return B(r.resolve(A))
class CP:
    @property
    def dependencies(self): return (B,)
    def provide(self,r): return C(r.resolve(B))
class DP:
    @property
    def dependencies(self): return (B,C)
    def provide(self,r): return D(r.resolve(B),r.resolve(C))
class Wrong:
    @property
    def dependencies(self): return ()
    def provide(self,r): return object()
class SelfP:
    @property
    def dependencies(self): return (A,)
    def provide(self,r): return A()
class ABP:
    @property
    def dependencies(self): return (B,)
    def provide(self,r): return A()
class BAP:
    @property
    def dependencies(self): return (A,)
    def provide(self,r): return B(r.resolve(A))
class BadP: pass
class BadDeps:
    @property
    def dependencies(self): return [A]
    def provide(self,r): return A()
class DupDeps:
    @property
    def dependencies(self): return (A,A)
    def provide(self,r): return A()
class Tests(unittest.TestCase):
    def c(self): return DefaultDependencyContainer()
    def test_protocols(self):
        self.assertIsInstance(self.c(),DependencyContainer); self.assertIsInstance(AP(),ServiceProvider); self.assertIsInstance(self.c(),ServiceResolver)
    def test_transient(self):
        c=self.c(); c.register(A,AP()); self.assertIsInstance(c.resolve(A),A); self.assertIsNot(c.resolve(A),c.resolve(A))
    def test_singleton(self):
        c=self.c(); p=P(factory=lambda r:A()); c.register(A,p,ServiceLifetime.SINGLETON); x=c.resolve(A); y=c.resolve(A); self.assertIs(x,y); self.assertEqual(p.calls,1)
    def test_duplicate(self):
        c=self.c(); c.register(A,AP());
        with self.assertRaises(DuplicateServiceError): c.register(A,AP())
    def test_invalid_contract(self):
        with self.assertRaises(TypeError): self.c().register('x',AP())
    def test_invalid_provider(self):
        with self.assertRaises(InvalidProviderError): self.c().register(A,BadP())
    def test_invalid_lifetime(self):
        with self.assertRaises(ValueError): self.c().register(A,AP(),'x')
    def test_duplicate_deps(self):
        with self.assertRaises(InvalidProviderError): self.c().register(A,DupDeps())
    def test_bad_deps(self):
        with self.assertRaises(InvalidProviderError): self.c().register(A,BadDeps())
    def test_missing_service(self):
        with self.assertRaises(MissingServiceError): self.c().resolve(A)
    def test_missing_dep_resolve(self):
        c=self.c(); c.register(B,BP());
        with self.assertRaises(MissingServiceError): c.resolve(B)
    def test_missing_dep_freeze(self):
        c=self.c(); c.register(B,BP());
        with self.assertRaises(MissingServiceError): c.freeze()
        self.assertFalse(c.frozen)
    def test_chain(self):
        c=self.c(); c.register(A,AP,ServiceLifetime.SINGLETON) if False else c.register(A,AP(),ServiceLifetime.SINGLETON); c.register(B,BP()); c.register(C,CP()); c.freeze(); x=c.resolve(C); self.assertIsInstance(x, C); self.assertIsInstance(x.b.a,A)
    def test_diamond_singletons(self):
        c=self.c(); c.register(A,AP(),ServiceLifetime.SINGLETON); c.register(B,BP(),ServiceLifetime.SINGLETON); c.register(C,CP()); c.register(D,DP()); c.freeze(); x=c.resolve(D); self.assertIs(x.b.a,x.c.b.a)
    def test_self_cycle(self):
        with self.assertRaises(CircularDependencyError): self.c().register(A,SelfP())
    def test_two_cycle_freeze(self):
        c=self.c(); c.register(A,ABP()); c.register(B,BAP());
        with self.assertRaises(CircularDependencyError): c.freeze()
    def test_two_cycle_resolve(self):
        c=self.c(); c.register(A,ABP()); c.register(B,BAP());
        with self.assertRaises(CircularDependencyError): c.resolve(A)
    def test_freeze(self):
        c=self.c(); c.register(A,AP()); c.freeze(); self.assertTrue(c.frozen)
    def test_freeze_idempotent(self):
        c=self.c(); c.freeze(); c.freeze(); self.assertTrue(c.frozen)
    def test_register_after_freeze(self):
        c=self.c(); c.freeze();
        with self.assertRaises(ContainerFrozenError): c.register(A,AP())
    def test_failed_freeze_open(self):
        c=self.c(); c.register(B,BP());
        with self.assertRaises(MissingServiceError): c.freeze()
        c.register(A,AP()); c.freeze(); self.assertTrue(c.frozen)
    def test_wrong_instance(self):
        c=self.c(); c.register(A,Wrong());
        with self.assertRaises(InvalidServiceError): c.resolve(A)
    def test_provider_exception(self):
        class E:
            @property
            def dependencies(self): return ()
            def provide(self,r): raise ValueError('x')
        c=self.c(); c.register(A,E());
        with self.assertRaises(DependencyContainerError) as cm: c.resolve(A)
        self.assertIsNotNone(cm.exception.__cause__)
    def test_singleton_per_container(self):
        x=self.c(); y=self.c(); x.register(A,AP(),ServiceLifetime.SINGLETON); y.register(A,AP(),ServiceLifetime.SINGLETON); self.assertIsNot(x.resolve(A),y.resolve(A))
    def test_no_domain_authority(self):
        c=self.c();
        for name in ('execute','execute_tool','run_workflow','reason','plan','decide','authorize','security','create_identity','load_plugin','initialize_plugin'):
            self.assertFalse(hasattr(c,name))
    def test_reusable(self):
        c=self.c(); c.register(A,AP()); self.assertIsInstance(c.resolve(A),A); self.assertIsInstance(c.resolve(A),A)
    def test_empty_freeze(self): self.assertTrue(self.c().freeze() is None)
if __name__=='__main__': unittest.main(verbosity=2)
