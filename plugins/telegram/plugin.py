"""Telegram plugin — send/receive messages via Telethon.

Requires: pip install telethon
Configuration: TELEGRAM_API_ID, TELEGRAM_API_HASH in .env or settings.
"""

from __future__ import annotations

from actions.base import BaseAction, ActionResult


class SendTelegramAction(BaseAction):
    action_name = "send_telegram"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        chat_id = command.get("chat_id", "")
        text = command.get("text", "")

        if dry_run:
            return ActionResult(success=True, message=f"Отправить в Telegram {chat_id}: {text[:50]}...")

        try:
            from telethon import TelegramClient
            from core.config import settings
            api_id = settings.telegram_api_id
            api_hash = settings.telegram_api_hash
            if not api_id or not api_hash:
                return ActionResult(success=False, message="Telegram не настроен (нужны TELEGRAM_API_ID и API_HASH)")

            client = TelegramClient("plugins/telegram/session", api_id, api_hash)
            await client.start()
            await client.send_message(chat_id, text)
            await client.disconnect()
            return ActionResult(success=True, message=f"Сообщение отправлено")
        except ImportError:
            return ActionResult(success=False, message="telethon не установлен. pip install telethon")
        except Exception as e:
            return ActionResult(success=False, error=str(e), message=f"Ошибка Telegram: {e}")

    def get_capability(self) -> dict:
        return {"action": "send_telegram", "description": "Отправить сообщение в Telegram", "params": {"chat_id": "string", "text": "string"}}


class ReadTelegramAction(BaseAction):
    action_name = "read_telegram"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        chat_id = command.get("chat_id", "")
        limit = command.get("limit", 5)

        if dry_run:
            return ActionResult(success=True, message=f"Прочитать {limit} сообщений из {chat_id}")

        try:
            from telethon import TelegramClient
            from core.config import settings
            api_id = settings.telegram_api_id
            api_hash = settings.telegram_api_hash

            client = TelegramClient("plugins/telegram/session", api_id, api_hash)
            await client.start()
            messages = []
            async for msg in client.iter_messages(chat_id, limit=limit):
                messages.append({"id": msg.id, "text": msg.text, "sender": str(msg.sender_id)})
            await client.disconnect()
            return ActionResult(success=True, message=f"Прочитано {len(messages)} сообщений", data={"messages": messages})
        except ImportError:
            return ActionResult(success=False, message="telethon не установлен")
        except Exception as e:
            return ActionResult(success=False, error=str(e), message=f"Ошибка: {e}")

    def get_capability(self) -> dict:
        return {"action": "read_telegram", "description": "Прочитать последние сообщения", "params": {"chat_id": "string", "limit": "int"}}
