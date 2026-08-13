from collections import defaultdict
from collections.abc import Callable

from ai_os.foundation.events.event import Event
from ai_os.foundation.logging.logger import get_logger


logger = get_logger(__name__)


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Event], None]]] = (
            defaultdict(list)
        )

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None],
    ) -> None:
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None],
    ) -> None:
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def publish(self, event: Event) -> None:
        for handler in list(self._subscribers[event.event_type]):
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Event handler failed: %s",
                    event.event_type,
                )