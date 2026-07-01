"""Wake-word detector — 'Руслан' через Vosk.

WakeWordDetector запускает фоновый поток, слушает микрофон через
sounddevice.InputStream, передаёт аудио в Vosk ASR и при обнаружении
слова 'руслан' (регистронезависимо) вызывает callback().
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from queue import Queue

import numpy as np
import sounddevice as sd
from loguru import logger
from vosk import KaldiRecognizer, Model

SAMPLE_RATE = 16000  # Vosk ожидает 16 kHz
BLOCK_SIZE = 8000    # 0.5 с при 16 kHz
SILENCE_AFTER_WAKE = 3.0  # секунд блокировки после срабатывания


class WakeWordDetector:
    """Детектор wake-word 'Руслан' на базе Vosk.

    Использование:
        detector = WakeWordDetector(callback=my_callback)
        detector.start()
        ...
        detector.stop()
    """

    def __init__(
        self,
        callback: callable,
        model_path: str = "models/vosk-model-small-ru-0.22",
    ) -> None:
        self.callback = callback
        self._model_path = Path(model_path)

        # Потоковые флаги
        self._running = threading.Event()
        self._stream: sd.InputStream | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        # Анти-спам: время последнего срабатывания
        self._last_trigger: float = 0.0

        # Инициализация Vosk (делаем лениво — в start)
        self._model: Model | None = None
        self._recognizer: KaldiRecognizer | None = None

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Запустить детекцию в фоновом потоке."""
        if self._running.is_set():
            logger.warning("WakeWordDetector уже запущен")
            return

        self._load_model()

        self._running.set()
        self._thread = threading.Thread(
            target=self._run,
            name="wake-word-detector",
            daemon=True,
        )
        self._thread.start()
        logger.info("WakeWordDetector запущен (слушаю 'Руслан')")

    def stop(self) -> None:
        """Остановить детекцию."""
        self._running.clear()

        with self._lock:
            if self._stream is not None:
                try:
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        logger.info("WakeWordDetector остановлен")

    @property
    def is_running(self) -> bool:
        return self._running.is_set()

    # ------------------------------------------------------------------
    # Внутренняя реализация
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """Загрузить Vosk-модель (вызывается один раз при start)."""
        model_path = str(self._model_path.resolve())
        if not self._model_path.exists():
            logger.error(
                "Vosk-модель не найдена: {}. "
                "Скачайте и распакуйте в {}",
                model_path,
                self._model_path,
            )
            raise FileNotFoundError(f"Vosk model not found: {model_path}")

        self._model = Model(model_path)
        self._recognizer = KaldiRecognizer(self._model, SAMPLE_RATE)
        # Частичные результаты (промежуточные гипотезы)
        self._recognizer.SetWords(False)
        logger.info("Vosk-модель загружена: {}", model_path)

    def _run(self) -> None:
        """Основной цикл: захват аудио → Vosk → поиск 'руслан'."""
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=BLOCK_SIZE,
                callback=self._audio_callback,
            ):
                # Держим поток живым пока running
                self._running.wait()
        except Exception:
            logger.exception("Ошибка в аудиопотоке")
        finally:
            self._running.clear()

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info,
        status: sd.CallbackFlags,
    ) -> None:
        """Callback sounddevice — передаёт данные в Vosk recognizer."""
        if not self._running.is_set():
            return

        if status:
            logger.debug("Audio status: {}", status)

        if self._recognizer is None:
            return

        # int16 → bytes для Vosk
        data = indata.tobytes()
        if self._recognizer.AcceptWaveform(data):
            # Финальный результат (законченная фраза)
            result = json.loads(self._recognizer.Result())
            text = result.get("text", "")
            if text and self._is_wake_word(text):
                self._on_wake()
        else:
            # Частичный результат (промежуточная гипотеза)
            partial = json.loads(self._recognizer.PartialResult())
            partial_text = partial.get("partial", "")
            if partial_text and self._is_wake_word(partial_text):
                self._on_wake()

    def _is_wake_word(self, text: str) -> bool:
        """Проверить, содержит ли текст слово 'руслан'."""
        return "руслан" in text.lower()

    def _on_wake(self) -> None:
        """Обработать срабатывание: анти-спам + callback."""
        now = time.monotonic()
        if now - self._last_trigger < SILENCE_AFTER_WAKE:
            return  # защита от повторных быстрых срабатываний

        self._last_trigger = now
        logger.info("🔥 Wake word detected!")
        try:
            self.callback()
        except Exception:
            logger.exception("Ошибка в wake-word callback")
