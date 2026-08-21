import unittest
from ai_os.platform.plugins import *
from ai_os.foundation.plugins.manifest import PluginManifest
from ai_os.foundation.plugins.types import PluginType, PluginState
class P:
 def __init__(self): self.manifest=PluginManifest('p','P','1',PluginType.CAPABILITY); self.calls=[]
 def load(self): self.calls.append('load')
 def initialize(self): self.calls.append('init')
 def pause(self): self.calls.append('pause')
 def unload(self): self.calls.append('unload')
class T(unittest.TestCase):
 def test_protocol(self): self.assertIsInstance(DefaultPluginPlatform(),PluginPlatform)
 def test_lifecycle(self):
  p=P(); m=DefaultPluginPlatform(); m.install(p); m.validate('p'); m.load('p'); m.initialize('p'); m.pause('p'); m.unload('p'); self.assertEqual(p.calls,['load','init','pause','unload'])
 def test_remove_requires_unload(self):
  p=P(); m=DefaultPluginPlatform(); m.install(p)
  with self.assertRaises(PluginPlatformError): m.remove('p')
 def test_duplicate_install(self):
  m=DefaultPluginPlatform(); m.install(P())
  with self.assertRaises(PluginAlreadyInstalledError): m.install(P())
 def test_freeze(self):
  m=DefaultPluginPlatform(); m.install(P()); m.freeze()
  with self.assertRaises(PluginPlatformFrozenError): m.install(P())
 def test_contribution_is_data(self):
  m=DefaultPluginPlatform(); m.install(P()); c=PluginContribution('tool1','tool',{'x':1}); m.contribute('p',c)
  with self.assertRaises(PluginContributionError): m.contribute('p',c)
 def test_no_runtime_authority(self):
  m=DefaultPluginPlatform(); self.assertFalse(hasattr(m,'execute')); self.assertFalse(hasattr(m,'runtime_executor'))
if __name__=='__main__': unittest.main()
