class PluginError(Exception):
    """Base exception for plugin-related failures."""


class PluginValidationError(PluginError):
    """Raised when a plugin fails validation."""


class PluginLifecycleError(PluginError):
    """Raised when a plugin lifecycle operation fails."""