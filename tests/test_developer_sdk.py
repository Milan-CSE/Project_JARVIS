import unittest
from ai_os.platform.sdk import *
from ai_os.runtime.tasks.task import Task
from ai_os.engines.engine import Engine
class K:
 @property
 def capability(self): return 'x'
 def execute(self,step): return None
class E:
 @property
 def engine_id(self): return 'e'
 @property
 def engine_type(self):
  from ai_os.engines.types import EngineType
  return EngineType.CHAT
 def execute(self,request): return None
class T(unittest.TestCase):
 def test_tool(self):
  d=DeveloperSDK().create_tool(tool_id='t',name='T',version='1',description='d',capability='x'); self.assertIsInstance(d.tool,Tool)
 def test_task(self): self.assertIsInstance(DeveloperSDK().create_task(K()).task,Task)
 def test_engine(self): self.assertIsInstance(DeveloperSDK().create_engine(E()).engine,Engine)
 def test_invalid_task(self):
  with self.assertRaises(TypeError): DeveloperSDK().create_task(object())
 def test_invalid_engine(self):
  with self.assertRaises(TypeError): DeveloperSDK().create_engine(object())
 def test_no_runtime(self):
  s=DeveloperSDK(); self.assertFalse(hasattr(s,'execute')); self.assertFalse(hasattr(s,'register_runtime'))
if __name__=='__main__': unittest.main()
