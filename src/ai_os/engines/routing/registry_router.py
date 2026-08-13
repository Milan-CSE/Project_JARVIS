from __future__ import annotations

from ai_os.engines.registry import EngineRegistry
from ai_os.engines.request import EngineRequest
from ai_os.engines.result import EngineResult
from ai_os.engines.types import EngineStatus


class RegistryEngineRouter:
    """Routes requests to Engines registered in an EngineRegistry."""

    def __init__(
        self,
        registry: EngineRegistry,
    ) -> None:
        if not isinstance(registry, EngineRegistry):
            raise TypeError(
                "registry must be an EngineRegistry"
            )

        self._registry = registry

    def route(
        self,
        request: EngineRequest,
    ) -> EngineResult:
        if not isinstance(request, EngineRequest):
            raise TypeError(
                "request must be an EngineRequest"
            )

        engine_id = request.metadata.get(
            "engine_id"
        )

        if not isinstance(engine_id, str):
            raise ValueError(
                "request metadata must contain a valid "
                "'engine_id'"
            )

        engine = self._registry.get(engine_id)

        return engine.execute(request)