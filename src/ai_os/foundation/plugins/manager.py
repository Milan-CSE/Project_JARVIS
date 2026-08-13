from ai_os.foundation.plugins.errors import (
    PluginLifecycleError,
    PluginValidationError,
)
from ai_os.foundation.plugins.plugin import Plugin
from ai_os.foundation.plugins.types import PluginState


class PluginManager:
    def __init__(self):
        self._plugins: dict[str, Plugin] = {}
        self._states: dict[str, PluginState] = {}

    def register(self, plugin: Plugin) -> None:
        plugin_id = plugin.manifest.plugin_id

        if not plugin_id:
            raise PluginValidationError("Plugin ID cannot be empty.")

        if plugin_id in self._plugins:
            raise PluginValidationError(
                f"Plugin already registered: {plugin_id}"
            )

        self._plugins[plugin_id] = plugin
        self._states[plugin_id] = PluginState.DISCOVERED

    def get(self, plugin_id: str) -> Plugin | None:
        return self._plugins.get(plugin_id)

    def get_state(self, plugin_id: str) -> PluginState | None:
        return self._states.get(plugin_id)

    def validate(self, plugin_id: str) -> None:
        plugin = self._require_plugin(plugin_id)

        if not isinstance(plugin, Plugin):
            self._states[plugin_id] = PluginState.FAILED
            raise PluginValidationError(
                f"Plugin does not satisfy the required contract: {plugin_id}"
            )

        self._transition(
            plugin_id,
            PluginState.VALIDATED,
            {PluginState.DISCOVERED},
        )

    def load(self, plugin_id: str) -> None:
        plugin = self._require_plugin(plugin_id)

        self._transition(
            plugin_id,
            PluginState.LOADED,
            {PluginState.VALIDATED},
        )

        try:
            plugin.load()
        except Exception as exc:
            self._states[plugin_id] = PluginState.FAILED
            raise PluginLifecycleError(
                f"Failed to load plugin: {plugin_id}"
            ) from exc

    def initialize(self, plugin_id: str) -> None:
        plugin = self._require_plugin(plugin_id)

        self._transition(
            plugin_id,
            PluginState.INITIALIZED,
            {PluginState.LOADED},
        )

        try:
            plugin.initialize()
        except Exception as exc:
            self._states[plugin_id] = PluginState.FAILED
            raise PluginLifecycleError(
                f"Failed to initialize plugin: {plugin_id}"
            ) from exc

    def pause(self, plugin_id: str) -> None:
        plugin = self._require_plugin(plugin_id)

        self._transition(
            plugin_id,
            PluginState.PAUSED,
            {PluginState.INITIALIZED},
        )

        try:
            plugin.pause()
        except Exception as exc:
            self._states[plugin_id] = PluginState.FAILED
            raise PluginLifecycleError(
                f"Failed to pause plugin: {plugin_id}"
            ) from exc

    def unload(self, plugin_id: str) -> None:
        plugin = self._require_plugin(plugin_id)

        self._transition(
            plugin_id,
            PluginState.UNLOADED,
            {PluginState.INITIALIZED, PluginState.PAUSED},
        )

        try:
            plugin.unload()
        except Exception as exc:
            self._states[plugin_id] = PluginState.FAILED
            raise PluginLifecycleError(
                f"Failed to unload plugin: {plugin_id}"
            ) from exc

    def _require_plugin(self, plugin_id: str) -> Plugin:
        plugin = self._plugins.get(plugin_id)

        if plugin is None:
            raise PluginValidationError(
                f"Plugin not registered: {plugin_id}"
            )

        return plugin

    def _transition(
        self,
        plugin_id: str,
        new_state: PluginState,
        allowed_states: set[PluginState],
    ) -> None:
        current_state = self._states[plugin_id]

        if current_state not in allowed_states:
            raise PluginLifecycleError(
                f"Invalid plugin lifecycle transition: "
                f"{current_state.value} -> {new_state.value}"
            )

        self._states[plugin_id] = new_state