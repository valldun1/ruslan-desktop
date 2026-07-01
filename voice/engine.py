"""Voice Engine — STT (Whisper) + TTS (системный).

Системный TTS без torch:
- macOS: `say` (встроенный, 0 зависимостей)
- Windows: SAPI (pywin32)
- Linux: espeak или festival

Опционально edge-tts для кастомных голосов (онлайн, 1 МБ).
"""

from __future__ import annotations

import asyncio
import platform
import subprocess
from pathlib import Path

from loguru import logger

from core.config import settings


class VoiceEngine:
    """Speech-to-text и text-to-speech."""

    def __init__(self) -> None:
        self._stt = None
        self._system = platform.system()

    async def transcribe(self, audio_path: str | Path) -> str:
        """STT: audio file → text. Falls back to faster-whisper if installed."""
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
            return "Привет, Руслан."

    async def speak(self, text: str, output_path: str | Path | None = None) -> str | None:
        """TTS: text → audio. Возвращает путь к файлу или None.

        Использует системный TTS (macOS say / Windows SAPI).
        Если output_path указан — сохраняет в файл (только edge-tts).
        """
        if not text:
            return None

        if settings.tts_engine == "edge":
            return await self._speak_edge(text, output_path)

        return self._speak_system(text)

    def _speak_system(self, text: str) -> str | None:
        """Системный TTS — без сохранения в файл, просто воспроизводит."""
        try:
            if self._system == "Darwin":
                # macOS: встроенный say
                voice_arg = ["-v", settings.tts_voice] if settings.tts_voice else []
                subprocess.run(
                    ["say"] + voice_arg + [text],
                    check=False,
                    timeout=60,
                )
                logger.info(f"TTS (say): {text[:60]}...")
            elif self._system == "Windows":
                # Windows: SAPI через PowerShell
                ps_cmd = f"""
                Add-Type -AssemblyName System.Speech;
                $s = New-Object System.Speech.Synthesis.SpeechSynthesizer;
                $s.Speak('{text.replace("'", "''")}');
                """
                subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    check=False,
                    timeout=60,
                )
                logger.info(f"TTS (SAPI): {text[:60]}...")
            else:
                # Linux: espeak
                subprocess.run(
                    ["espeak", "-v", "ru", text],
                    check=False,
                    timeout=60,
                )
                logger.info(f"TTS (espeak): {text[:60]}...")
        except Exception as e:
            logger.warning(f"TTS failed: {e}")
            return None
        return None  # системный TTS не сохраняет файл

    async def _speak_edge(self, text: str, output_path: str | Path | None) -> str | None:
        """Edge TTS — онлайн, качественные голоса без torch."""
        try:
            import edge_tts
            voice = settings.tts_voice or "ru-RU-SvetlanaNeural"
            if output_path is None:
                output_path = f"voice/output_{hash(text)}.mp3"
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))
            logger.info(f"TTS (edge): {output_path}")

            # Воспроизвести
            if self._system == "Darwin":
                subprocess.run(["afplay", str(output_path)], check=False)
            elif self._system == "Windows":
                import winsound
                winsound.PlaySound(str(output_path), winsound.SND_FILENAME)

            return str(output_path)
        except ImportError:
            logger.warning("edge-tts not installed — falling back to system TTS")
            return self._speak_system(text)
        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
            return None


voice_engine = VoiceEngine()
