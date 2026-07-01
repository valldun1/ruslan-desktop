"""Memory — SQLite-based storage for history, settings, habits.

MVP: simple SQLite with key-value store.
V2: vector memory (Chroma/LangGraph) for semantic recall.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from loguru import logger

from core.config import settings


class Memory:
    """Persistent memory backend."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = Path(db_path or settings.sqlite_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_tables()
        logger.info(f"Memory DB: {self._db_path}")

    def _init_tables(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                hermes_response TEXT,
                actions TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        self._conn.commit()

    def save_history(self, user_input: str, hermes_response: str | None = None, actions: list | None = None) -> None:
        if not self._conn:
            return
        self._conn.execute(
            "INSERT INTO history (user_input, hermes_response, actions) VALUES (?, ?, ?)",
            (user_input, hermes_response, json.dumps(actions or [], ensure_ascii=False)),
        )
        self._conn.commit()

    def get_history(self, limit: int = 10) -> list[dict]:
        if not self._conn:
            return []
        cursor = self._conn.execute(
            "SELECT user_input, hermes_response, actions, timestamp FROM history ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [
            {
                "user_input": row[0],
                "hermes_response": row[1],
                "actions": json.loads(row[2] or "[]"),
                "timestamp": row[3],
            }
            for row in cursor.fetchall()
        ]

    def clear_history(self) -> None:
        if not self._conn:
            return
        self._conn.execute("DELETE FROM history")
        self._conn.commit()

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        if not self._conn:
            return default
        cursor = self._conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str) -> None:
        if not self._conn:
            return
        self._conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self._conn.commit()


memory = Memory()
