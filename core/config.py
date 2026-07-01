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

    # LLM
    hermes_api_url: str = "http://localhost:8080/v1"
    hermes_api_key: str = "***"

    # API
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Logging
    log_level: str = "DEBUG"
    log_file: str = "logs/ruslan.log"
    log_json: bool = False

    # Voice
    stt_model: str = "base"
    tts_model: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    tts_speaker: str = "default"
    wake_word: str = "руслан"

    # Windows
    dry_run: bool = False
    confirm_delete: bool = True
    confirm_execute: bool = True
    enable_keyboard: bool = True

    # Godot
    godot_ws_url: str = "ws://127.0.0.1:8100/character"
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


settings = Settings()
