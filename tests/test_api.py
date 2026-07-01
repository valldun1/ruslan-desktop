"""Tests for API endpoints and WebSocket."""

from __future__ import annotations

import pytest


# API тесты требуют fastapi + uvicorn
# pip install ruslan[api]  # или fastapi uvicorn

pytest.importorskip("fastapi")

from api.main import app


class TestAPI:
    def test_root(self):
        """Проверить, что приложение создаётся без ошибок."""
        assert app.title == "Ruslan Desktop Agent API"
        assert app.version == "0.1.0"
