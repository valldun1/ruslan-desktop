"""Ruslan Desktop Agent — точка входа.

Запускает:
1. API сервер (для плагинов, WebSocket)
2. UI оверлей (PyQt5, замена Godot)
3. Brain + Action Engine
"""

from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path

from loguru import logger

from core.config import settings
from core.event_bus import event_bus


def setup_logging() -> None:
    """Настроить loguru."""
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<level>{level: <8}</level> | {message}",
    )
    logger.add(
        log_path,
        level="DEBUG",
        rotation="10 MB",
        retention=3,
    )
    logger.info(f"Ruslan v0.2.0 — log: {log_path}")


def main() -> None:
    """Главная точка входа: ruslan."""
    setup_logging()
    logger.info("Ruslan Desktop Agent запуск...")

    # Регистрация действий
    from actions.engine import action_engine
    action_engine.register_all()
    logger.info(f"Action Engine: {len(action_engine._registry)} действий")

    # Brain (Hermes + Ollama fallback)
    from brain.gateway import gateway

    # Voice Engine
    from voice.engine import voice_engine
    _ = voice_engine  # инициализация

    # Запуск API (опционально, для плагинов)
    api_task = None
    if settings.api_port:
        try:
            import uvicorn
            from api.main import app

            def run_api() -> None:
                uvicorn.run(
                    app,
                    host=settings.api_host,
                    port=settings.api_port,
                    log_level=settings.log_level.lower(),
                )

            import threading
            api_thread = threading.Thread(target=run_api, daemon=True)
            api_thread.start()
            logger.info(f"API запущен: http://{settings.api_host}:{settings.api_port}")
        except Exception as e:
            logger.warning(f"API не запущен: {e}")

    # Запуск UI оверлея
    if settings.ui_enabled:
        try:
            from ui.overlay import RuslanOverlay

            # Оверлей — PyQt5, блокирует основной поток
            RuslanOverlay.launch(brain=gateway)
        except ImportError as e:
            logger.warning(f"UI не запущен: {e}. Установи PyQt5: pip install ruslan[ui]")
            # Без UI — просто ждём
            try:
                import anyio
                anyio.run(asyncio.Event().wait)
            except KeyboardInterrupt:
                pass
        except Exception as e:
            logger.error(f"UI ошибка: {e}")
    else:
        # Без UI — консольный режим
        logger.info("UI отключён — консольный режим")
        try:
            import anyio
            anyio.run(asyncio.Event().wait)
        except KeyboardInterrupt:
            pass

    logger.info("Ruslan завершён")


if __name__ == "__main__":
    main()
