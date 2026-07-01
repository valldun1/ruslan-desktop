"""Brain Gateway — Hermes LLM integration.

Sends user requests to Hermes, receives structured JSON commands.
Uses OpenAI-compatible API (Hermes / any LLM with function calling).
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from core.config import settings
from .schemas import LLMResponse, MessageCommand

# Hermes system prompt that makes it output structured commands
SYSTEM_PROMPT = r"""Ты — Гермес, ИИ-координатор визуального агента Руслан.

Твоя задача — превращать запросы пользователя в структурированные команды для Руслана.

Руслан — визуальный персонаж на рабочем столе Windows/macOS. Он может:
- открывать/закрывать программы
- перемещать, копировать, удалять файлы
- искать файлы по имени
- кликать, печатать текст, нажимать горячие клавиши
- открывать сайты и папки
- показывать сообщения

Пример:
Пользователь: "найди договор и открой его"
Ответ:
{
  "plan": ["Найти файл 'договор'", "Открыть найденный файл"],
  "commands": [
    {"action": "search_file", "query": "договор", "description": "Поиск файла договор"},
    {"action": "message", "text": "Нашёл договор. Открываю.", "description": "Сообщение пользователю"}
  ],
  "response_text": "Сейчас найду договор."
}

ПРАВИЛА:
1. Всегда отвечай ТОЛЬКО JSON. Никакого текста вне JSON.
2. Если задача сложная — разбей на несколько команд (до 5).
3. Опасные действия (delete_file) помечай requires_confirmation=true.
4. Добавляй description для каждой команды.
5. Если задача невыполнима — верни команду message с объяснением.
6. Все пути — абсолютные (начинаются с / или C:\).

Доступные action:
- open_app, close_app — открыть/закрыть программу
- move_file, copy_file, delete_file — работа с файлами
- search_file — поиск файла по имени
- create_folder, open_folder — работа с папками
- click, double_click, right_click — клики мыши
- type_text, press_key, hotkey — клавиатура
- open_url, search_web — браузер
- screenshot — снимок экрана
- wait — пауза
- message — показать сообщение
"""


class HermesGateway:
    """HTTP client to Hermes LLM API."""

    def __init__(self, api_url: str | None = None, api_key: str | None = None) -> None:
        self.api_url = (api_url or settings.hermes_api_url).rstrip("/")
        self.api_key = api_key or settings.hermes_api_key

    async def process_request(self, user_text: str, context: dict | None = None) -> LLMResponse:
        """Send user request to Hermes, parse structured response.
        
        Falls back to a message command if Hermes is unavailable or returns invalid JSON.
        """
        import httpx

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

        if context:
            messages.append({"role": "user", "content": json.dumps(context, ensure_ascii=False)})

        messages.append({"role": "user", "content": user_text})

        logger.info(f"Sending to Hermes: {user_text[:100]}...")

        # Try up to 2 times
        last_error = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{self.api_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "hermes",
                            "messages": messages,
                            "response_format": {"type": "json_object"},
                            "temperature": 0.1,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    raw = data["choices"][0]["message"]["content"]
                    break
            except Exception as e:
                last_error = e
                logger.warning(f"Hermes attempt {attempt + 1} failed: {e}")
                if attempt == 0:
                    # Brief pause before retry
                    import asyncio
                    await asyncio.sleep(1)
                else:
                    return self._fallback_response(f"Ошибка связи с Гермесом: {e}")
        else:
            return self._fallback_response(f"Ошибка связи с Гермесом: {last_error}")

        try:
            parsed = json.loads(raw)
            response = LLMResponse(**parsed)
            logger.info(f"Hermes responded: {len(response.commands)} command(s)")
            return response
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse Hermes response: {e}\nRaw: {raw[:300]}")
            return self._fallback_response("Извини, я не понял команду. Попробуй ещё раз.")

    def _fallback_response(self, text: str) -> LLMResponse:
        """Return a safe fallback when Hermes is unavailable."""
        logger.warning(f"Using fallback: {text}")
        return LLMResponse(
            plan=["Ошибка обработки"],
            commands=[MessageCommand(text=text, description=text)],
            response_text=text,
        )


# Global singleton
gateway = HermesGateway()
