"""Brain Gateway — Hermes LLM integration + Ollama fallback.

Отправляет запросы пользователя в LLM (Hermes), получает структурированные JSON.
При недоступности Hermes — переключается на локальную Ollama.
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from core.config import settings
from .schemas import LLMResponse, MessageCommand

# Системный промпт для Hermes
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
- system_info — информация о системе
- clipboard_get, clipboard_set — буфер обмена
- volume_set — громкость (0-100)
- speak_text — озвучивание текста
- disk_usage — использование диска
- battery — заряд батареи
- window_minimize — свернуть окно
- lock_screen — блокировка экрана
- empty_trash — очистка корзины
- run_command — выполнить команду (требует confirm=true)
- open_trash — открыть корзину
"""


class HermesGateway:
    """HTTP client to Hermes LLM API with Ollama fallback."""

    def __init__(self, api_url: str | None = None, api_key: str | None = None) -> None:
        self.api_url = (api_url or settings.hermes_api_url).rstrip("/")
        self.api_key = api_key or settings.hermes_api_key
        self._is_local = False  # True = используем ollama

    @property
    def using_local(self) -> bool:
        """True если сейчас используем Ollama вместо Hermes."""
        return self._is_local

    async def process_request(self, user_text: str, context: dict | None = None) -> LLMResponse:
        """Send user request to LLM, parse structured response.

        Пытается Hermes ×2. Если оба раза ошибка — fallback на Ollama.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        if context:
            messages.append({"role": "user", "content": json.dumps(context, ensure_ascii=False)})
        messages.append({"role": "user", "content": user_text})

        logger.info(f"Sending to LLM: {user_text[:100]}...")

        # Попытка 1-2: Hermes
        if not self._is_local:
            result = await self._try_hermes(messages)
            if result is not None:
                return result

        # Fallback: Ollama
        if settings.ollama_fallback:
            logger.info("Hermes недоступен — пробуем Ollama")
            result = await self._try_ollama(messages)
            if result is not None:
                return result
            return self._fallback_response("Ошибка: Hermes и Ollama недоступны")

        return self._fallback_response("Ошибка связи с Гермесом")

    async def _try_hermes(self, messages: list[dict]) -> LLMResponse | None:
        """Попытка отправить запрос в Hermes/OpenAI API. Возвращает None при ошибке."""
        import httpx

        last_error = None
        for attempt in range(2):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                # Browser headers for Cloudflare (OpenCode Go)
                if "opencode" in self.api_url:
                    headers.update({
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36",
                        "Origin": "https://opencode.ai",
                        "Referer": "https://opencode.ai/",
                    })

                async with httpx.AsyncClient(timeout=settings.hermes_timeout) as client:
                    resp = await client.post(
                        f"{self.api_url}/chat/completions",
                        headers=headers,
                        json={
                            "model": settings.hermes_model,
                            "messages": messages,
                            "response_format": {"type": "json_object"},
                            "temperature": 0.1,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    raw = data["choices"][0]["message"]["content"]
                    return self._parse_response(raw)
            except Exception as e:
                last_error = e
                logger.warning(f"Hermes attempt {attempt + 1} failed: {e}")
                if attempt == 0:
                    import asyncio
                    await asyncio.sleep(1)

        logger.error(f"Hermes failed after 2 attempts: {last_error}")
        self._is_local = True
        return None

    async def _try_ollama(self, messages: list[dict]) -> LLMResponse | None:
        """Отправить запрос в локальную Ollama."""
        import httpx

        try:
            # Ollama API: /api/chat
            ollama_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in messages
            ]
            url = f"{settings.ollama_api_url}/api/chat"
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    json={
                        "model": settings.ollama_model,
                        "messages": ollama_messages,
                        "stream": False,
                        "options": {"temperature": 0.1},
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                raw = data["message"]["content"]
                return self._parse_response(raw)
        except Exception as e:
            logger.error(f"Ollama failed: {e}")
            return None

    def _parse_response(self, raw: str) -> LLMResponse | None:
        """Распарсить JSON-ответ LLM в LLMResponse."""
        try:
            parsed = json.loads(raw)
            # Ollama может обернуть JSON в текст — попробуем извлечь
            if isinstance(parsed, dict) and "commands" not in parsed:
                # Поиск JSON в тексте
                import re
                match = re.search(r'\{[^{}]*"commands"[^{}]*\}', raw, re.DOTALL)
                if match:
                    parsed = json.loads(match.group())
            response = LLMResponse(**parsed)
            logger.info(f"LLM responded: {len(response.commands)} command(s)")
            return response
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse LLM response: {e}\nRaw: {raw[:300]}")
            return None

    def _fallback_response(self, text: str) -> LLMResponse:
        """Безопасный fallback, когда LLM недоступен."""
        logger.warning(f"Using fallback: {text}")
        return LLMResponse(
            plan=["Ошибка обработки"],
            commands=[MessageCommand(text=text, description=text)],
            response_text=text,
        )


# Global singleton
gateway = HermesGateway()
