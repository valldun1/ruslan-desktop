"""Ruslan — main entry point.

Launches all services:
1. Logger
2. Memory DB
3. API server (FastAPI + WebSocket)
4. Optional: Voice engine, Godot character
"""

from __future__ import annotations

import asyncio
import signal
import sys

from loguru import logger

from core.config import settings
from core.logger import setup_logging
from core.event_bus import event_bus
from core.task_queue import task_queue


async def shutdown(sig: signal.Signals) -> None:
    logger.info(f"Received {sig.name}, shutting down...")
    await event_bus.emit("system:shutdown")
    sys.exit(0)


def main() -> None:
    setup_logging()
    logger.info("=" * 60)
    logger.info("Ruslan Desktop Agent v0.1.0")
    logger.info("=" * 60)

    # Init memory
    from memory.store import memory
    memory.connect()

    # Register actions
    import actions  # noqa: F401
    from actions.engine import action_engine
    caps = action_engine.get_capabilities()
    logger.info(f"Registered {len(caps)} capabilities")

    # Load plugins
    from plugins.manager import plugin_manager
    plugin_actions = plugin_manager.load_all()
    for action_cls in plugin_actions:
        action_engine.register(action_cls)

    # Start task queue processor
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(task_queue.process_loop())

    # Handle signals
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))
        except (ValueError, NotImplementedError):
            pass  # Windows doesn't support add_signal_handler

    # Start API
    from api.main import app
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
