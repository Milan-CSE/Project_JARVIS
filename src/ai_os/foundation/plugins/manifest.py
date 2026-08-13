from dataclasses import dataclass, field

from ai_os.foundation.plugins.types import PluginType


@dataclass(frozen=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    plugin_type: PluginType
    permissions: tuple[str, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    configuration: tuple[str, ...] = field(default_factory=tuple)