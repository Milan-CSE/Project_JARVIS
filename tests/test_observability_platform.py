import unittest
from ai_os.platform.observability import *
class T(unittest.TestCase):
 def test_protocol(self): self.assertIsInstance(InMemoryObservability(),Observability)
 def test_records(self):
  o=InMemoryObservability(); o.record_event(ObservabilityEvent('x')); o.record_metric(MetricSample('m',1)); o.record_audit(AuditRecord('a','u','ok')); o.record_diagnostic(DiagnosticRecord('c','bad')); self.assertEqual(len(o.events),1); self.assertEqual(len(o.metrics),1); self.assertEqual(len(o.audits),1); self.assertEqual(len(o.diagnostics),1)
 def test_immutable(self):
  r=AuditRecord('a','u','ok',{'x':1})
  with self.assertRaises(AttributeError): r.action='b'
  with self.assertRaises(TypeError): r.metadata['x']=2
 def test_wrong_type_rejected(self):
  o=InMemoryObservability()
  with self.assertRaises(TypeError): o.record_event(object())
  with self.assertRaises(TypeError): o.record_metric(object())
  with self.assertRaises(TypeError): o.record_audit(object())
  with self.assertRaises(TypeError): o.record_diagnostic(object())
 def test_no_execution(self):
  o=InMemoryObservability(); self.assertFalse(hasattr(o,'execute')); self.assertFalse(hasattr(o,'authorize'))
if __name__=='__main__': unittest.main()
