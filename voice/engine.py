"""Voice Engine — STT (Whisper) + TTS (XTTS).

MVP stubs — swap with real implementations later.
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from core.config import settings


class VoiceEngine:
    """Speech-to-text and text-to-speech."""

    def __init__(self) -> None:
        self._stt = None
        self._tts = None

    async def transcribe(self, audio_path: str | Path) -> str:
        """STT: audio file → text. Stub: returns demo text."""
        try:
            from faster_whisper import WhisperModel
            if self._stt is None:
                self._stt = WhisperModel(settings.stt_model, device="cpu", compute_type="int8")
            segments, _ = self._stt.transcribe(str(audio_path), language="ru")
            text = " ".join(seg.text for seg in segments)
            logger.info(f"STT: {text[:100]}...")
            return text
        except ImportError:
            logger.warning("faster-whisper not installed — returning demo text")
            return "Привет, Руслан. Открой Telegram."

    async def speak(self, text: str, output_path: str | Path | None = None) -> str | None:
        """TTS: text → audio file. Returns path."""
        try:
            from TTS.api import TTS
            if self._tts is None:
                self._tts = TTS(settings.tts_model)
            out = Path(output_path or f"voice/output_{hash(text)}.wav")
            out.parent.mkdir(parents=True, exist_ok=True)
            self._tts.tts_to_file(text=text, speaker=settings.tts_speaker, file_path=str(out))
            logger.info(f"TTS: {out}")
            return str(out)
        except ImportError:
            logger.warning("TTS not installed — skipping voice output")
            return None


voice_engine = VoiceEngine()
