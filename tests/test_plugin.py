from ai_os.foundation.plugins.errors import PluginLifecycleError
from ai_os.foundation.plugins.manager import PluginManager
from ai_os.foundation.plugins.manifest import PluginManifest
from ai_os.foundation.plugins.types import PluginType


class BadPlugin:
    manifest = PluginManifest(
        "aios.bad",
        "Bad",
        "1.0.0",
        PluginType.CAPABILITY,
    )

    def load(self):
        raise RuntimeError("load failed")

    def initialize(self):
        pass

    def pause(self):
        pass

    def unload(self):
        pass


manager = PluginManager()
manager.register(BadPlugin())
manager.validate("aios.bad")

try:
    manager.load("aios.bad")
except PluginLifecycleError as exc:
    print(exc)

print(manager.get_state("aios.bad"))