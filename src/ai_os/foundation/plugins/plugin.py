from typing import Protocol, runtime_checkable

from ai_os.foundation.plugins.manifest import PluginManifest


@runtime_checkable
class Plugin(Protocol):
    @property
    def manifest(self) -> PluginManifest:
        ...

    def load(self) -> None:
        ...

    def initialize(self) -> None:
        ...

    def pause(self) -> None:
        ...

    def unload(self) -> None:
        ...