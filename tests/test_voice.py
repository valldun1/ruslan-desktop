"""Tests for Voice Engine — system TTS."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from voice.engine import VoiceEngine


class TestVoiceEngine:
    @pytest.mark.asyncio
    async def test_speak_empty_text(self):
        engine = VoiceEngine()
        result = await engine.speak("")
        assert result is None

    @pytest.mark.asyncio
    async def test_transcribe_no_whisper(self):
        engine = VoiceEngine()
        result = await engine.transcribe("/nonexistent/audio.wav")
        # Без faster-whisper возвращает заглушку
        assert isinstance(result, str)
        assert len(result) > 0

    def test_system_tts_darwin(self):
        """Проверить, что _speak_system не падает на macOS."""
        engine = VoiceEngine()
        # Не запускаем реальный say — только проверяем что код грузится
        assert hasattr(engine, "_speak_system")
