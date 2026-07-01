"""Ruslan core configuration — pydantic-settings."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM — Hermes (основной)
    hermes_api_url: str = "http://localhost:8080/v1"
    hermes_api_key: str = ""
    hermes_model: str = "kimi-k2.5"

    @classmethod
    def _resolve_api_key(cls) -> str:
        """Взять API ключ из OPENCODE_GO_API_KEY если HERMES_API_KEY не задан."""
        import os
        key = os.environ.get("HERMES_API_KEY") or os.environ.get("OPENCODE_GO_API_KEY", "")
        return key

    # LLM — Ollama (fallback при недоступности Hermes)
    ollama_api_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_fallback: bool = True
    hermes_timeout: int = 15  # секунд до fallback

    # API (для внешних плагинов — Telegram webhook и т.п.)
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/ruslan.log"
    log_json: bool = False

    # Voice
    voice_enabled: bool = True
    stt_model: str = "base"
    wake_word: str = "руслан"
    tts_engine: Literal["system", "edge"] = "system"  # system = macOS say / Win SAPI
    tts_voice: str = ""  # "" = системный голос по умолчанию

    # UI (замена Godot)
    ui_enabled: bool = True
    ui_always_on_top: bool = True
    ui_sprite_file: str = "assets/ruslan_idle.png"
    ui_sprite_size: int = 128
    ui_hotkey: str = "cmd+shift+r"   # macOS
    # ui_hotkey: str = "ctrl+shift+r"  # Windows

    # Windows/macOS общее
    dry_run: bool = False
    confirm_delete: bool = True
    confirm_execute: bool = True
    enable_keyboard: bool = True

    # Godot (устарело — оставлено для обратной совместимости)
    godot_ws_url: str = ""
    character_width: int = 300
    character_height: int = 400

    # Memory
    memory_backend: Literal["sqlite", "postgres"] = "sqlite"
    sqlite_path: str = "data/ruslan.db"

    # Telegram plugin
    telegram_api_id: str = ""
    telegram_api_hash: str = ""

    @property
    def root_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent

    @property
    def assets_dir(self) -> Path:
        """Папка assets/ (спрайты, иконки)."""
        return self.root_dir / "assets"


settings = Settings()
