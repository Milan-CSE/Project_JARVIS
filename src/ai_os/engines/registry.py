from __future__ import annotations

from typing import Dict

from .engine import Engine


class EngineRegistry:
    """Registry of available Engine implementations."""

    def __init__(self) -> None:
        self._engines: Dict[str, Engine] = {}

    def register(self, engine: Engine) -> None:
        if not isinstance(engine, Engine):
            raise TypeError(
                "engine must satisfy the Engine protocol"
            )

        engine_id = engine.engine_id

        if not isinstance(engine_id, str):
            raise TypeError(
                "engine.engine_id must be a string"
            )

        if not engine_id.strip():
            raise ValueError(
                "engine.engine_id must be non-empty"
            )

        if engine_id in self._engines:
            raise ValueError(
                f"Engine already registered: {engine_id}"
            )

        self._engines[engine_id] = engine

    def get(self, engine_id: str) -> Engine:
        if not isinstance(engine_id, str):
            raise TypeError(
                "engine_id must be a string"
            )

        if engine_id not in self._engines:
            raise KeyError(
                f"Unknown engine: {engine_id}"
            )

        return self._engines[engine_id]

    def remove(self, engine_id: str) -> None:
        if not isinstance(engine_id, str):
            raise TypeError(
                "engine_id must be a string"
            )

        if engine_id not in self._engines:
            raise KeyError(
                f"Unknown engine: {engine_id}"
            )

        del self._engines[engine_id]

    def contains(self, engine_id: str) -> bool:
        if not isinstance(engine_id, str):
            raise TypeError(
                "engine_id must be a string"
            )

        return engine_id in self._engines

    def __len__(self) -> int:
        return len(self._engines)