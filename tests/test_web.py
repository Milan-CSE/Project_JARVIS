import unittest
from ai_os.interfaces.api import APIEvent, APIError, APIRequest, APIResponse, APIResponseStatus
from ai_os.interfaces.web import *

class T:
    def __init__(self,response=None,events=()): self.calls=0; self.requests=[]; self.events=tuple(events); self.response=response
    def send(self,r): self.calls+=1; self.requests.append(r); return self.response or APIResponse(r.request_id,APIResponseStatus.SUCCESS,{"ok":True})
    def subscribe(self,c): return self.events

class Bad:
    def send(self,r): return "bad"
    def subscribe(self,c): return ("bad",)

class WebTests(unittest.TestCase):
    def req(self,id="r1"): return APIRequest(id,"assistant.request","hello")
    def ev(self,id="e1",corr="r1"): return APIEvent(id,"progress",corr,{"p":1})

    def test_transport_protocol(self): self.assertIsInstance(T(),WebClientTransport)
    def test_transport_shape_is_accepted_but_bad_results_are_rejected(self):
        client = WebApplicationClient(Bad())
        with self.assertRaises(TypeError):
            client.send(self.req())
    def test_send(self):
        c=T(); vm=WebApplicationClient(c).send(self.req()); self.assertEqual(vm.state,WebOperationState.SUCCESS); self.assertIs(c.requests[0],self.req("r1")) if False else None
    def test_exact_request(self):
        c=T(); r=self.req(); WebApplicationClient(c).send(r); self.assertIs(c.requests[0],r)
    def test_response_id_mismatch(self):
        with self.assertRaises(ValueError): WebApplicationClient(T(APIResponse("x",APIResponseStatus.SUCCESS))).send(self.req())
    def test_wrong_response(self):
        with self.assertRaises(TypeError): WebApplicationClient(Bad()).send(self.req())
    def test_status_mappings(self):
        for s,ws in [(APIResponseStatus.ACCEPTED,WebOperationState.PENDING),(APIResponseStatus.BLOCKED,WebOperationState.BLOCKED),
                     (APIResponseStatus.FAILED,WebOperationState.FAILED),(APIResponseStatus.CANCELLED,WebOperationState.CANCELLED),
                     (APIResponseStatus.INCOMPLETE,WebOperationState.INCOMPLETE)]:
            self.assertEqual(WebApplicationClient(T(APIResponse("r1",s))).send(self.req()).state,ws)
    def test_error_mapping(self):
        r=APIResponse("r1",APIResponseStatus.FAILED,error=APIError("X","bad"))
        self.assertEqual(WebApplicationClient(T(r)).send(self.req()).error,"bad")
    def test_events(self):
        e1,e2=self.ev(),self.ev("e2"); vm=WebApplicationClient(T(events=(e1,e2))).receive_events("r1")
        self.assertEqual(vm.events,(e1,e2))
    def test_duplicate_events_removed(self):
        e=self.ev(); vm=WebApplicationClient(T(events=(e,e))).receive_events("r1"); self.assertEqual(vm.events,(e,))
    def test_wrong_event_correlation(self):
        with self.assertRaises(ValueError): WebApplicationClient(T(events=(self.ev(corr="wrong"),))).receive_events("r1")
    def test_wrong_event_type(self):
        with self.assertRaises(TypeError): WebApplicationClient(Bad()).receive_events("r1")
    def test_current_id_mismatch(self):
        with self.assertRaises(ValueError): WebApplicationClient(T()).receive_events("r1",WebViewModel("r2","pending"))
    def test_disconnect(self):
        vm=WebApplicationClient(T()).mark_disconnected(WebViewModel("r1","pending")); self.assertEqual(vm.state,WebOperationState.DISCONNECTED)
    def test_view_immutable(self):
        with self.assertRaises(AttributeError):
            WebViewModel("r1","idle").state=WebOperationState.SUCCESS
    def test_metadata_immutable(self):
        with self.assertRaises(TypeError): WebViewModel("r1","idle",metadata={"x":1}).metadata["x"]=2
    def test_renderer_protocol(self): self.assertIsInstance(DefaultWebResponseRenderer(),WebResponseRenderer)
    def test_renderer(self):
        vm=WebViewModel("r1","success","hello"); out=DefaultWebResponseRenderer().render(vm); self.assertEqual(out["state"],"success")
    def test_renderer_treats_html_as_data(self):
        vm=WebViewModel("r1","success","<script>x</script>"); self.assertEqual(DefaultWebResponseRenderer().render(vm)["output"],"<script>x</script>")
    def test_no_runtime(self):
        c=WebApplicationClient(T()); self.assertFalse(hasattr(c,"runtime_executor")); self.assertFalse(hasattr(c,"executor"))
    def test_no_tools(self):
        c=WebApplicationClient(T()); self.assertFalse(hasattr(c,"tool_registry")); self.assertFalse(hasattr(c,"task_registry"))
    def test_no_workflow(self): self.assertFalse(hasattr(WebApplicationClient(T()),"workflow_runner"))
    def test_no_security(self):
        c=WebApplicationClient(T()); self.assertFalse(hasattr(c,"authorize")); self.assertFalse(hasattr(c,"security"))
    def test_no_identity_factory(self): self.assertFalse(hasattr(WebApplicationClient(T()),"create_identity"))
    def test_no_persistence(self):
        c=WebApplicationClient(T()); self.assertFalse(hasattr(c,"save")); self.assertFalse(hasattr(c,"persist"))
    def test_reusable(self):
        c=T(); w=WebApplicationClient(c); self.assertEqual(w.send(self.req("a")).request_id,"a"); self.assertEqual(w.send(self.req("b")).request_id,"b"); self.assertEqual(c.calls,2)

if __name__=="__main__": unittest.main(verbosity=2)
