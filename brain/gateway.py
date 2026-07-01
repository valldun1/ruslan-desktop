"""Brain Gateway — Hermes LLM integration.

Sends user requests to Hermes, receives structured JSON commands.
Uses OpenAI-compatible API (Hermes / any LLM with function calling).
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from core.config import settings
from .schemas import LLMResponse, AnyCommand

# Hermes system prompt that makes it output structured commands
SYSTEM_PROMPT = """Ты — Гермес, ИИ-координатор визуального агента Руслан.

Твоя задача — превращать запросы пользователя в структурированные команды для Руслана.

Руслан — визуальный персонаж на рабочем столе Windows. Он может:
- открывать/закрывать программы
- перемещать, копировать, удалять файлы
- искать файлы по имени
- кликать, печатать текст, нажимать горячие клавиши
- открывать сайты и папки
- показывать сообщения

ПРАВИЛА:
1. Всегда отвечай ТОЛЬКО JSON. Никакого текста вне JSON.
2. Если задача сложная — разбей на несколько команд.
3. Опасные действия (delete, execute) помечай requires_confirmation=true.
4. Добавляй description для каждой команды (человекочитаемое описание).
5. Если задача невыполнима — верни команду message с объяснением.

Формат ответа:
{
  "plan": ["шаг 1", "шаг 2", ...],
  "commands": [
    {
      "action": "open_app",
      "app_name": "Telegram",
      "description": "Открыть Telegram"
    }
  ],
  "response_text": "Сейчас открою Telegram."
}

Доступные action: open_app, close_app, move_file, copy_file, delete_file,
search_file, create_folder, open_folder, click, type_text, hotkey,
open_url, search_web, screenshot, message, wait
"""


class HermesGateway:
    """HTTP client to Hermes LLM API."""

    def __init__(self, api_url: str | None = None, api_key: str | None = None) -> None:
        self.api_url = (api_url or settings.hermes_api_url).rstrip("/")
        self.api_key = api_key or settings.hermes_api_key

    async def process_request(self, user_text: str, context: dict | None = None) -> LLMResponse:
        """Send user request to Hermes, parse structured response."""
        import httpx

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

        if context:
            messages.append({"role": "user", "content": json.dumps(context, ensure_ascii=False)})

        messages.append({"role": "user", "content": user_text})

        logger.info(f"Sending to Hermes: {user_text[:100]}...")

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.api_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "hermes",  # Hermes auto-routes
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]

        try:
            parsed = json.loads(raw)
            response = LLMResponse(**parsed)
            logger.info(f"Hermes responded: {len(response.commands)} command(s)")
            return response
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse Hermes response: {e}\nRaw: {raw[:300]}")
            # Fallback: message command
            return LLMResponse(
                plan=["Ошибка обработки"],
                commands=[AnyCommand(action="message", text="Извини, я не понял команду. Попробуй ещё раз.")],
                response_text="Ошибка",
            )


# Global singleton
gateway = HermesGateway()
