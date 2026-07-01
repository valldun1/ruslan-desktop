"""VoiceManager — оркестратор голосового ввода.

Управляет полным циклом голосового взаимодействия:
- Запускает WakeWordDetector (фоновое прослушивание wake word)
- При обнаружении wake word запускает STT (SpeechRecognizer)
- Полученный текст отправляет в brain.process_request()
- Обновляет статус через коллбэк (для UI-оверлея)

Статусы:
- 'listening' — ожидание wake word (🎤)
- 'thinking' — обработка команды brain (💭)
- 'speaking' — озвучивание ответа (💬)
- 'idle' — бездействие (🌐)
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from loguru import logger

from core.config import settings
from voice.stt import WakeWordDetector


class VoiceManager:
    """Оркестратор голосового ввода.

    Принимает brain (HermesGateway) и опциональный коллбэк для обновления статуса.
    """

    def __init__(
        self,
        brain: Any,
        on_status_change: Callable[[str], None] | None = None,
    ) -> None:
        """
        Параметры
        ---------
        brain : HermesGateway
            Экземпляр brain для обработки распознанных команд.
        on_status_change : Callable[[str], None] | None
            Коллбэк, вызываемый при смене статуса:
            'listening', 'thinking', 'speaking', 'idle'.
        """
        self.brain = brain
        self._on_status_change = on_status_change
        self._detector: WakeWordDetector | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Запустить детекцию wake word + STT."""
        if not settings.voice_enabled:
            logger.info("Голосовой ввод отключён (voice_enabled=False)")
            return

        self._detector = WakeWordDetector(
            wake_word=settings.wake_word,
            model_path="models/vosk-model-small-ru-0.22",
            listen_duration=5,
            on_command=self._on_command,
        )
        self._detector.start()
        self._set_status("listening")
        logger.info(
            "VoiceManager запущен — слушаю '{}'",
            settings.wake_word,
        )

    def stop(self) -> None:
        """Остановить детекцию wake word."""
        if self._detector is not None:
            self._detector.stop()
            self._detector = None
        self._set_status("idle")
        logger.info("VoiceManager остановлен")

    # ------------------------------------------------------------------
    # Internal: обработка команд
    # ------------------------------------------------------------------

    def _on_command(self, text: str) -> None:
        """Обработать голосовую команду.

        Вызывается из фонового потока WakeWordDetector:
        - Меняет статус на 'thinking'
        - Отправляет текст в brain.process_request() (async в новом event loop)
        - После ответа меняет статус на 'speaking', затем 'listening'
        """
        logger.info("🎤 Голосовая команда: {}", text)
        self._set_status("thinking")

        # WakeWordDetector вызывает нас из фонового потока → свой event loop
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._process(text))
        except Exception as exc:
            logger.error("Ошибка обработки голосовой команды: {}", exc)
        finally:
            loop.close()

    async def _process(self, text: str) -> None:
        """Отправить текст в brain и получить ответ."""
        if self.brain is None:
            logger.warning("VoiceManager: brain не задан — команда пропущена")
            self._set_status("listening")
            return

        try:
            response = await self.brain.process_request(text)
            if response and getattr(response, "response_text", None):
                logger.info("🤖 Ответ: {}", response.response_text[:100])
                self._set_status("speaking")
                # TTS будет воспроизведён voice/engine.py отдельно
            else:
                logger.info("🤖 Ответ без текста")
        except Exception as exc:
            logger.error("VoiceManager: brain.process_request error: {}", exc)
        finally:
            # Возвращаемся в режим прослушивания (детектор уже активен)
            self._set_status("listening")

    # ------------------------------------------------------------------
    # Internal: управление статусом
    # ------------------------------------------------------------------

    def _set_status(self, status: str) -> None:
        """Обновить статус и уведомить коллбэк."""
        if self._on_status_change is not None:
            try:
                self._on_status_change(status)
            except Exception as exc:
                logger.error("VoiceManager: статус-коллбэк error: {}", exc)
