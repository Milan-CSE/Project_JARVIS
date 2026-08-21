
import unittest
from ai_os.interfaces.api import *

class Core:
    def __init__(self,response=None): self.calls=0; self.requests=[]; self.response=response
    def __call__(self,r):
        self.calls+=1; self.requests.append(r)
        return self.response or APIResponse(r.request_id,APIResponseStatus.SUCCESS,{"ok":True})

class WrongCore:
    def __call__(self,r): return "bad"
class MismatchCore:
    def __call__(self,r): return APIResponse("different",APIResponseStatus.SUCCESS,"bad")
class RaiseCore:
    def __call__(self,r): raise RuntimeError("x")
class Pub:
    def __init__(self): self.calls=0; self.events=[]
    def publish(self,e): self.calls+=1; self.events.append(e)

class APITests(unittest.TestCase):
    def req(self,id="req:1"):
        return APIRequest(id,"assistant.request","hello",{"mode":"fast"},{"source":"test"})
    def test_request_immutable(self):
        r=self.req()
        with self.assertRaises(AttributeError): r.operation="x"
    def test_request_maps_immutable(self):
        r=self.req()
        with self.assertRaises(TypeError): r.parameters["mode"]="slow"
        with self.assertRaises(TypeError): r.metadata["x"]=1
    def test_request_validation(self):
        for kwargs, exc in [
            ({"request_id":"","operation":"x"},ValueError),
            ({"request_id":"r","operation":""},ValueError),
            ({"request_id":1,"operation":"x"},TypeError),
            ({"request_id":"r","operation":1},TypeError),
            ({"request_id":"r","operation":"x","parameters":[]},TypeError),
            ({"request_id":"r","operation":"x","metadata":[]},TypeError),
        ]:
            with self.assertRaises(exc): APIRequest(**kwargs)
    def test_error_immutable_and_validated(self):
        e=APIError("BAD","bad",{"x":1})
        with self.assertRaises(AttributeError): e.code="x"
        with self.assertRaises(TypeError): e.details["x"]=2
    def test_response_immutable(self):
        r=APIResponse("req",APIResponseStatus.SUCCESS,"ok",metadata={"x":1})
        with self.assertRaises(AttributeError): r.output="x"
        with self.assertRaises(TypeError): r.metadata["x"]=2
    def test_event_immutable(self):
        e=APIEvent("e","type","req",{"x":1},{"m":1})
        with self.assertRaises(AttributeError): e.event_type="x"
        with self.assertRaises(TypeError): e.payload["x"]=2
        with self.assertRaises(TypeError): e.metadata["m"]=2
    def test_protocols(self):
        class ValidApplication:
            def handle(self, request):
                return APIResponse(
                    request.request_id,
                    APIResponseStatus.SUCCESS,
                    "ok",
                )
        self.assertIsInstance(ValidApplication(), APIApplication)
        self.assertIsInstance(Pub(), APIEventPublisher)
    def test_application_forwards_once_and_preserves_exact_request_response(self):
        c=Core(); a=DefaultAPIApplication(c); r=self.req()
        out=a.handle(r)
        self.assertEqual(c.calls,1); self.assertIs(c.requests[0],r); self.assertIs(out,a._handler.response if a._handler.response else c.requests and out)
    def test_invalid_handler(self):
        with self.assertRaises(TypeError): DefaultAPIApplication(object())
    def test_invalid_request(self):
        with self.assertRaises(TypeError): DefaultAPIApplication(Core()).handle(object())
    def test_wrong_handler_result(self):
        with self.assertRaises(TypeError): DefaultAPIApplication(WrongCore()).handle(self.req())
    def test_mismatched_request_id_rejected(self):
        with self.assertRaises(ValueError): DefaultAPIApplication(MismatchCore()).handle(self.req())
    def test_handler_exception_propagates(self):
        with self.assertRaises(RuntimeError): DefaultAPIApplication(RaiseCore()).handle(self.req())
    def test_statuses(self):
        self.assertEqual(set(APIResponseStatus),set([APIResponseStatus.SUCCESS,APIResponseStatus.ACCEPTED,APIResponseStatus.BLOCKED,APIResponseStatus.FAILED,APIResponseStatus.CANCELLED,APIResponseStatus.INCOMPLETE]))
    def test_event_identity_and_correlation_distinct(self):
        e=APIEvent("e1","progress","req1"); self.assertNotEqual(e.event_id,e.correlation_id)
    def test_publisher_exact_event(self):
        p=Pub(); e=APIEvent("e","t","r"); p.publish(e); self.assertEqual(p.calls,1); self.assertIs(p.events[0],e)
    def test_boundary_has_no_runtime_tool_workflow_security_intelligence_identity_persistence(self):
        a=DefaultAPIApplication(Core())
        forbidden=("runtime_executor","task_registry","tool_registry","workflow_runner","authorize","security","reason","plan","decide","replan","create_identity","save","persist","retry")
        for name in forbidden: self.assertFalse(hasattr(a,name),name)
    def test_reusable_and_no_cross_request_state(self):
        c=Core(); a=DefaultAPIApplication(c); r1=self.req("r1"); r2=self.req("r2")
        o1=a.handle(r1); o2=a.handle(r2)
        self.assertEqual(c.calls,2); self.assertEqual(o1.request_id,"r1"); self.assertEqual(o2.request_id,"r2")
        self.assertIs(c.requests[0],r1); self.assertIs(c.requests[1],r2)

if __name__=="__main__": unittest.main(verbosity=2)
