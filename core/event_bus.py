"""Event Bus — async pub/sub for inter-module communication.

All modules communicate through events, not direct calls.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Callable, Coroutine

from loguru import logger

EventHandler = Callable[..., Coroutine[Any, Any, None]]


class EventBus:
    """Simple async publish-subscribe bus."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event: str, handler: EventHandler) -> None:
        self._subscribers[event].append(handler)
        logger.debug(f"Subscribed handler for event: {event}")

    def unsubscribe(self, event: str, handler: EventHandler) -> None:
        if handler in self._subscribers[event]:
            self._subscribers[event].remove(handler)

    async def emit(self, event: str, **data: Any) -> None:
        """Emit event to all subscribers. Runs handlers concurrently."""
        handlers = self._subscribers.get(event, [])
        if not handlers:
            logger.debug(f"Event '{event}' emitted — no subscribers")
            return
        logger.debug(f"Event '{event}' → {len(handlers)} handlers")
        await asyncio.gather(
            *(handler(event=event, **data) for handler in handlers),
            return_exceptions=True,
        )


# Global singleton
event_bus = EventBus()
