"""Voice/STT — распознавание речи после wake word.

Содержит:
- SpeechRecognizer — запись с микрофона + распознавание (Vosk → Google fallback)
- WakeWordDetector — фоновое прослушивание микрофона, детекция wake word,
  запуск SpeechRecognizer для распознавания команды

Оба класса thread-safe и не блокируют tkinter mainloop:
  • Внутренние блокировки (threading.Lock) защищают общий доступ к Vosk model.
  • Асинхронный режим recognize(callback=...) запускает распознавание
    в фоновом daemon-потоке и вызывает callback по завершении.
  • WakeWordDetector работает в своём фоновом потоке.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Callable

import numpy as np
import sounddevice as sd
from loguru import logger


# ---------------------------------------------------------------------------
# SpeechRecognizer
# ---------------------------------------------------------------------------

class SpeechRecognizer:
    """Распознавание речи с микрофона.

    Использует Vosk (offline, модель small-ru) с fallback на Google Web Speech API
    при низкой confidence (< 0.5) или отсутствии результата.

    Потокобезопасен: threading.Lock защищает Vosk model.
    Не блокирует tkinter mainloop при использовании callback-режима.
    """

    def __init__(self, model_path: str = "models/vosk-model-small-ru-0.22"):
        self._model_path = Path(model_path)
        self._model = None
        self._lock = threading.Lock()
        self._load_model()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recognize(
        self,
        duration: int = 5,
        *,
        callback: Callable[[str | None], None] | None = None,
    ) -> str | None | threading.Thread:
        """Записать N секунд с микрофона и распознать речь.

        Два режима работы:

        **Асинхронный (callback)** — рекомендуется для tkinter::

            def on_result(text):
                if text:
                    print(f"Распознано: {text}")

            recognizer.recognize(duration=5, callback=on_result)

        **Синхронный (без callback)** — блокирует текущий поток::

            text = recognizer.recognize(duration=5)

        Параметры
        ---------
        duration : int
            Длительность записи в секундах.
        callback : Callable[[str | None], None] | None
            Функция, вызываемая с результатом (str или None) после распознавания.
            Если передана — метод не блокирует вызывающий поток.

        Возвращает
        ----------
        str | None
            Распознанный текст (при синхронном вызове).
        threading.Thread
            Ссылка на фоновый поток (при асинхронном вызове).
        """
        if callback is not None:
            t = threading.Thread(
                target=self._run_and_callback,
                args=(duration, callback),
                daemon=True,
            )
            t.start()
            return t

        # Синхронный режим — блокирует текущий поток
        return self._recognize_sync(duration)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """Загрузить Vosk модель (вызывается один раз при __init__)."""
        try:
            from vosk import Model

            if not self._model_path.exists():
                logger.warning(
                    "Vosk model not found at '%s' — Vosk will be unavailable. "
                    "Download from: https://alphacephei.com/vosk/models",
                    self._model_path,
                )
                return
            self._model = Model(str(self._model_path))
            logger.info("Vosk model loaded from '{}'", self._model_path)
        except Exception as exc:
            logger.error("Failed to load Vosk model: {}", exc)

    def _run_and_callback(
        self,
        duration: int,
        callback: Callable[[str | None], None],
    ) -> None:
        """Обёртка: распознать → вызвать callback (всегда)."""
        try:
            text = self._recognize_sync(duration)
        except Exception as exc:
            logger.error("Recognition failed: {}", exc)
            text = None
        finally:
            try:
                callback(text)
            except Exception as exc:
                logger.error("Recognition callback error: {}", exc)

    def _recognize_sync(self, duration: int) -> str | None:
        """Синхронное распознавание — вызывается из рабочего потока."""
        sample_rate = 16000

        # --- Запись с микрофона ---
        logger.debug("Recording {} s @ {} Hz ...", duration, sample_rate)
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        logger.debug("Recording finished ({} samples).", len(audio))

        # --- Vosk ---
        with self._lock:
            if self._model is None:
                logger.warning("Vosk model not loaded — skip Vosk, try Google fallback")
                return self._google_fallback(audio, sample_rate)

            from vosk import KaldiRecognizer

            rec = KaldiRecognizer(self._model, sample_rate)
            rec.AcceptWaveform(audio.tobytes())
            raw = rec.FinalResult()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Invalid Vosk JSON: {}", raw)
            result = {}

        text = result.get("text", "").strip()
        confidence = result.get("confidence", 0.0)

        if text and confidence >= 0.5:
            logger.info("Vosk OK  conf={:.2f}  text={}", confidence, text)
            return text

        # --- Fallback: Google Web Speech API ---
        logger.info(
            "Vosk weak  conf={:.2f}  text={!r} — fallback to Google",
            confidence,
            text,
        )
        return self._google_fallback(audio, sample_rate)

    def _google_fallback(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
    ) -> str | None:
        """Распознать через Google Web Speech API (требуется интернет)."""
        try:
            import speech_recognition as sr

            # numpy int16 → AudioData (sample_width=2 для 16-bit)
            audio = sr.AudioData(audio_data.tobytes(), sample_rate, sample_width=2)

            recognizer = sr.Recognizer()
            text = recognizer.recognize_google(audio, language="ru-RU")
            logger.info("Google OK  text={}", text)
            return text
        except ImportError:
            logger.warning("SpeechRecognition not installed — no Google fallback")
            return None
        except sr.UnknownValueError:
            logger.warning("Google could not understand the audio")
            return None
        except sr.RequestError as exc:
            logger.warning("Google request failed: {}", exc)
            return None
        except Exception as exc:
            logger.error("Google fallback error: {}", exc)
            return None


# ---------------------------------------------------------------------------
# WakeWordDetector
# ---------------------------------------------------------------------------

class WakeWordDetector:
    """Фоновое прослушивание микрофона и детекция wake word.

    При обнаружении wake word запускает SpeechRecognizer.recognize()
    в асинхронном режиме и передаёт распознанный текст в `on_command`.

    Потокобезопасен, не блокирует tkinter mainloop.
    """

    def __init__(
        self,
        wake_word: str = "руслан",
        model_path: str = "models/vosk-model-small-ru-0.22",
        listen_duration: int = 5,
        on_command: Callable[[str], None] | None = None,
    ) -> None:
        """
        Параметры
        ---------
        wake_word : str
            Активирующее слово (регистронезависимо).
        model_path : str
            Путь к Vosk модели (общий с SpeechRecognizer).
        listen_duration : int
            Длительность записи команды после детекции wake word.
        on_command : Callable[[str], None] | None
            Callback, вызываемый с распознанным текстом команды.
        """
        self._wake_word = wake_word.lower().strip()
        self._listen_duration = listen_duration
        self._on_command = on_command
        self._recognizer = SpeechRecognizer(model_path=model_path)

        # Состояние потока
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._pause_event = threading.Event()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Запустить фоновый поток детекции wake word."""
        with self._lock:
            if self._running:
                return
            self._running = True

        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("WakeWordDetector started  wake_word='{}'", self._wake_word)

    def stop(self) -> None:
        """Остановить детекцию wake word."""
        with self._lock:
            self._running = False
        self._pause_event.set()  # разблокировать, если в ожидании
        logger.info("WakeWordDetector stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Internal: фоновый цикл
    # ------------------------------------------------------------------

    def _listen_loop(self) -> None:
        """Фоновый цикл: слушает микрофон, ищет wake word."""
        sample_rate = 16000
        chunk_sec = 0.8  # сэмплируем по 0.8 сек для быстрой реакции

        # Инициализируем Vosk KaldiRecognizer для потокового детекта
        try:
            from vosk import KaldiRecognizer

            with self._recognizer._lock:
                if self._recognizer._model is None:
                    logger.error(
                        "WakeWordDetector: Vosk model not loaded — cannot detect"
                    )
                    return
                rec = KaldiRecognizer(self._recognizer._model, sample_rate)
                rec.SetWords(False)
        except Exception as exc:
            logger.error("WakeWordDetector init failed: {}", exc)
            return

        logger.info("Listening for wake word '{}' ...", self._wake_word)

        while self._running:
            try:
                # Запись фрагмента
                chunk_frames = int(chunk_sec * sample_rate)
                audio = sd.rec(
                    chunk_frames,
                    samplerate=sample_rate,
                    channels=1,
                    dtype="int16",
                )
                sd.wait()

                if not self._running:
                    break

                # Проверяем полный результат (если Vosk решил, что фраза завершена)
                if rec.AcceptWaveform(audio.tobytes()):
                    raw = rec.FinalResult()
                    try:
                        result = json.loads(raw)
                    except json.JSONDecodeError:
                        result = {}
                    text = result.get("text", "").strip().lower()
                else:
                    # Частичный результат (промежуточный)
                    raw = rec.PartialResult()
                    try:
                        result = json.loads(raw)
                    except json.JSONDecodeError:
                        result = {}
                    text = result.get("partial", "").strip().lower()

                if not text:
                    continue

                logger.debug("Heard: '{}'", text)

                if self._wake_word in text:
                    logger.info("Wake word detected! Starting command recognition ...")

                    # Запускаем распознавание команды
                    cb = self._make_command_callback()
                    self._recognizer.recognize(
                        duration=self._listen_duration,
                        callback=cb,
                    )

                    # Пауза, чтобы не сдетектироваться повторно на том же фрагменте
                    time.sleep(1.5)

                    # Пересоздаём recognizer для следующего цикла
                    with self._recognizer._lock:
                        if self._recognizer._model is not None:
                            rec = KaldiRecognizer(self._recognizer._model, sample_rate)
                            rec.SetWords(False)

            except Exception as exc:
                logger.error("Wake word loop error: {}", exc)
                time.sleep(0.5)

        logger.info("WakeWordDetector loop ended")

    def _make_command_callback(self) -> Callable[[str | None], None]:
        """Создать callback для передачи результата SpeechRecognizer в on_command."""
        def _callback(text: str | None) -> None:
            if text and self._on_command:
                try:
                    self._on_command(text)
                except Exception as exc:
                    logger.error("Command callback error: {}", exc)

        return _callback
