"""Tests for Brain — Gateway, schemas, fallback."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from brain.gateway import HermesGateway, SYSTEM_PROMPT
from brain.schemas import (
    LLMResponse, MessageCommand, OpenAppCommand,
    ActionType,
)


class TestSchemas:
    def test_llm_response_minimal(self):
        r = LLMResponse(
            plan=["Test"],
            commands=[MessageCommand(text="hello", description="say hi")],
            response_text="hello",
        )
        assert len(r.commands) == 1
        assert r.commands[0].action == "message"

    def test_action_command(self):
        cmd = OpenAppCommand(
            action=ActionType.OPEN_APP,
            app_name="Safari",
            description="Open Safari",
        )
        assert cmd.action == ActionType.OPEN_APP
        assert cmd.app_name == "Safari"

    def test_action_command_serialization(self):
        cmd = MessageCommand(text="test", description="test")
        d = cmd.model_dump()
        assert d["action"] == "message"
        assert d["text"] == "test"

    def test_message_command(self):
        cmd = MessageCommand(text="test", description="test")
        assert cmd.action == "message"
        assert cmd.text == "test"


class TestGatewayFallback:
    @pytest.mark.asyncio
    async def test_fallback_response(self):
        gateway = HermesGateway(api_url="http://nonexistent:9999")
        gateway._is_local = False
        result = await gateway.process_request("test")
        assert result is not None
        assert len(result.commands) == 1
        assert isinstance(result.commands[0], MessageCommand)
        assert "Ошибка" in result.response_text or "недоступны" in result.response_text

    @pytest.mark.asyncio
    async def test_parse_valid_json(self):
        gateway = HermesGateway()
        raw = '{"plan": ["Step 1"], "commands": [{"action": "message", "text": "ok", "description": "test"}], "response_text": "ok"}'
        result = gateway._parse_response(raw)
        assert result is not None
        assert len(result.commands) == 1

    def test_parse_invalid_json(self):
        gateway = HermesGateway()
        result = gateway._parse_response("not json")
        assert result is None

    def test_parse_empty(self):
        gateway = HermesGateway()
        result = gateway._parse_response("")
        assert result is None


class TestSystemPrompt:
    def test_system_prompt_contains_actions(self):
        assert "open_app" in SYSTEM_PROMPT
        assert "message" in SYSTEM_PROMPT
        assert "delete_file" in SYSTEM_PROMPT

    def test_system_prompt_is_russian(self):
        assert "Гермес" in SYSTEM_PROMPT
        assert "Руслан" in SYSTEM_PROMPT
