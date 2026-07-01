"""System operations — clipboard, volume, battery, disk, screen, TTS, etc."""

from __future__ import annotations

import asyncio
import os
import platform as platform_module
import shutil
import subprocess
import sys
import time

from loguru import logger

from .base import BaseAction, ActionResult


class SystemInfoAction(BaseAction):
    action_name = "system_info"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        if dry_run:
            return ActionResult(success=True, message="Информация о системе")

        try:
            import psutil
            uptime_sec = time.time() - psutil.boot_time()
            uptime_str = f"{int(uptime_sec // 3600)}ч {int((uptime_sec % 3600) // 60)}м"
            data = {
                "os": f"{platform_module.system()} {platform_module.release()}",
                "cpu_count": psutil.cpu_count(logical=True),
                "ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 1),
                "uptime": uptime_str,
            }
        except ImportError:
            data = {
                "os": f"{platform_module.system()} {platform_module.release()}",
                "cpu_count": os.cpu_count() or 0,
                "ram_gb": "N/A (установи psutil)",
                "uptime": "N/A",
            }

        return ActionResult(success=True, message="Системная информация", data=data)

    def get_capability(self) -> dict:
        return {"action": "system_info", "description": "Показать информацию о системе (ОС, CPU, RAM, аптайм)"}


class ClipboardGetAction(BaseAction):
    action_name = "clipboard_get"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        if dry_run:
            return ActionResult(success=True, message="Чтение буфера обмена")

        system = platform_module.system()
        try:
            if system == "Darwin":
                result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
                text = result.stdout
            elif system == "Windows":
                try:
                    import pywin32  # noqa: F401
                    import win32clipboard
                    win32clipboard.OpenClipboard()
                    text = win32clipboard.GetClipboardData()
                    win32clipboard.CloseClipboard()
                except ImportError:
                    return ActionResult(success=False, message="pywin32 не установлен")
            else:
                return ActionResult(success=False, message="Неподдерживаемая ОС для clipboard_get")
        except Exception as e:
            logger.error(f"clipboard_get error: {e}")
            return ActionResult(success=False, message=f"Ошибка чтения буфера: {e}")

        return ActionResult(success=True, message="Буфер обмена прочитан", data={"text": text})

    def get_capability(self) -> dict:
        return {"action": "clipboard_get", "description": "Прочитать текст из буфера обмена"}


class ClipboardSetAction(BaseAction):
    action_name = "clipboard_set"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        text = command.get("text", "")
        if not text:
            return ActionResult(success=False, message="Не указан текст для копирования")

        if dry_run:
            return ActionResult(success=True, message=f"Запись в буфер: {text[:50]}...")

        system = platform_module.system()
        try:
            if system == "Darwin":
                proc = subprocess.run(["pbcopy"], input=text, text=True, capture_output=True, timeout=5)
                if proc.returncode != 0:
                    return ActionResult(success=False, message="pbcopy вернул ошибку")
            elif system == "Windows":
                try:
                    import pywin32  # noqa: F401
                    import win32clipboard
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(text)
                    win32clipboard.CloseClipboard()
                except ImportError:
                    return ActionResult(success=False, message="pywin32 не установлен")
            else:
                return ActionResult(success=False, message="Неподдерживаемая ОС для clipboard_set")
        except Exception as e:
            logger.error(f"clipboard_set error: {e}")
            return ActionResult(success=False, message=f"Ошибка записи в буфер: {e}")

        return ActionResult(success=True, message="Текст скопирован в буфер обмена")

    def get_capability(self) -> dict:
        return {"action": "clipboard_set", "description": "Записать текст в буфер обмена", "params": {"text": "string (обязательно)"}}


class VolumeSetAction(BaseAction):
    action_name = "volume_set"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        level = command.get("level", 50)
        if not isinstance(level, (int, float)):
            return ActionResult(success=False, message="Уровень громкости должен быть числом")

        level = max(0, min(100, int(level)))

        if dry_run:
            return ActionResult(success=True, message=f"Установка громкости: {level}%")

        system = platform_module.system()
        try:
            if system == "Darwin":
                proc = subprocess.run(
                    ["osascript", "-e", f"set volume output volume {level}"],
                    capture_output=True, text=True, timeout=5,
                )
                if proc.returncode != 0:
                    return ActionResult(success=False, message=f"osascript error: {proc.stderr}")
            else:
                return ActionResult(success=False, message="Управление громкостью реализовано только для macOS")
        except Exception as e:
            logger.error(f"volume_set error: {e}")
            return ActionResult(success=False, message=f"Ошибка: {e}")

        return ActionResult(success=True, message=f"Громкость установлена на {level}%")

    def get_capability(self) -> dict:
        return {"action": "volume_set", "description": "Установить громкость (0-100)", "params": {"level": "int (0-100)"}}


class SpeakTextAction(BaseAction):
    action_name = "speak_text"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        text = command.get("text", "")
        if not text:
            return ActionResult(success=False, message="Не указан текст для озвучивания")

        if dry_run:
            return ActionResult(success=True, message=f"Озвучивание: {text[:50]}...")

        system = platform_module.system()
        try:
            if system == "Darwin":
                proc = subprocess.run(["say", text], capture_output=True, text=True, timeout=30)
                if proc.returncode != 0:
                    return ActionResult(success=False, message=f"say error: {proc.stderr}")
            elif system == "Windows":
                try:
                    import win32com.client
                    speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    speaker.Speak(text)
                except ImportError:
                    return ActionResult(success=False, message="win32com не доступен для TTS")
            else:
                return ActionResult(success=False, message="TTS реализован только для macOS и Windows")
        except subprocess.TimeoutExpired:
            return ActionResult(success=False, message="Озвучивание превысило таймаут")
        except Exception as e:
            logger.error(f"speak_text error: {e}")
            return ActionResult(success=False, message=f"Ошибка озвучивания: {e}")

        return ActionResult(success=True, message=f"Озвучено: {text[:100]}")

    def get_capability(self) -> dict:
        return {"action": "speak_text", "description": "Озвучить текст через системный TTS", "params": {"text": "string (обязательно)"}}


class DiskUsageAction(BaseAction):
    action_name = "disk_usage"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        if dry_run:
            return ActionResult(success=True, message="Информация о диске")

        try:
            usage = shutil.disk_usage("/")
            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
            percent = round(usage.used / usage.total * 100, 1)

            data = {
                "total_gb": round(total_gb, 1),
                "used_gb": round(used_gb, 1),
                "free_gb": round(free_gb, 1),
                "percent_used": percent,
            }
        except Exception as e:
            logger.error(f"disk_usage error: {e}")
            return ActionResult(success=False, message=f"Ошибка получения данных о диске: {e}")

        return ActionResult(
            success=True,
            message=f"Диск: {data['used_gb']}/{data['total_gb']} ГБ ({data['percent_used']}%)",
            data=data,
        )

    def get_capability(self) -> dict:
        return {"action": "disk_usage", "description": "Показать использование диска"}


class BatteryAction(BaseAction):
    action_name = "battery"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        if dry_run:
            return ActionResult(success=True, message="Информация о батарее")

        system = platform_module.system()
        data = {}

        try:
            if system == "Darwin":
                proc = subprocess.run(
                    ["pmset", "-g", "batt"],
                    capture_output=True, text=True, timeout=5,
                )
                if proc.returncode == 0:
                    # Пример вывода: "Now drawing from 'Battery Power' -InternalBattery-0 85%; discharging;"
                    for line in proc.stdout.splitlines():
                        if "%" in line:
                            parts = line.strip().split("\t")
                            for part in parts:
                                if "%" in part:
                                    pct_str = part.split("%")[0].strip()
                                    data["percent"] = int(pct_str.replace(";", ""))
                                    break
                            if "discharging" in line:
                                data["power_source"] = "battery"
                            elif "charging" in line:
                                data["power_source"] = "charging"
                            elif "AC" in line or "charged" in line:
                                data["power_source"] = "ac_power"
                            break
                    if not data:
                        data["percent"] = 0
                        data["power_source"] = "unknown"
                else:
                    data["percent"] = 0
                    data["power_source"] = "N/A"
            else:
                try:
                    import psutil
                    batt = psutil.sensors_battery()
                    if batt:
                        data["percent"] = int(batt.percent)
                        data["power_source"] = "charging" if batt.power_plugged else "battery"
                        data["secs_left"] = int(batt.secsleft) if batt.secsleft != -1 else None
                    else:
                        data["percent"] = 0
                        data["power_source"] = "N/A (нет батареи)"
                except ImportError:
                    data["percent"] = 0
                    data["power_source"] = "N/A (установи psutil для Windows/Linux)"
        except Exception as e:
            logger.error(f"battery error: {e}")
            return ActionResult(success=False, message=f"Ошибка получения данных о батарее: {e}")

        pct = data.get("percent", 0)
        source = data.get("power_source", "unknown")
        return ActionResult(
            success=True,
            message=f"Батарея: {pct}% ({source})",
            data=data,
        )

    def get_capability(self) -> dict:
        return {"action": "battery", "description": "Показать уровень заряда батареи"}


class WindowMinimizeAction(BaseAction):
    action_name = "window_minimize"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        if dry_run:
            return ActionResult(success=True, message="Минимизация окна")

        system = platform_module.system()
        try:
            if system == "Darwin":
                proc = subprocess.run(
                    ["osascript", "-e", 'tell application "System Events" to keystroke "m" using command down'],
                    capture_output=True, text=True, timeout=5,
                )
                if proc.returncode != 0:
                    return ActionResult(success=False, message=f"osascript error: {proc.stderr}")
            elif system == "Windows":
                try:
                    import pygetwindow as gw
                    active = gw.getActiveWindow()
                    if active:
                        active.minimize()
                    else:
                        return ActionResult(success=False, message="Не найден активный window")
                except ImportError:
                    return ActionResult(success=False, message="pygetwindow не установлен")
            else:
                return ActionResult(success=False, message="Минимизация окна не поддерживается на этой ОС")
        except Exception as e:
            logger.error(f"window_minimize error: {e}")
            return ActionResult(success=False, message=f"Ошибка: {e}")

        return ActionResult(success=True, message="Активное окно свернуто")

    def get_capability(self) -> dict:
        return {"action": "window_minimize", "description": "Свернуть активное окно"}


class LockScreenAction(BaseAction):
    action_name = "lock_screen"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        if dry_run:
            return ActionResult(success=True, message="Блокировка экрана")

        system = platform_module.system()
        try:
            if system == "Darwin":
                # Попробуем pmset сначала, потом CGSession
                proc = subprocess.run(
                    ["pmset", "displaysleepnow"],
                    capture_output=True, text=True, timeout=5,
                )
                if proc.returncode != 0:
                    # Fallback: CGSession
                    cgsession = "/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession"
                    if os.path.exists(cgsession):
                        subprocess.run([cgsession, "-suspend"], timeout=5)
                    else:
                        return ActionResult(success=False, message="Не удалось заблокировать экран")
            elif system == "Windows":
                proc = subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], timeout=5)
                if proc.returncode != 0:
                    return ActionResult(success=False, message="Не удалось заблокировать экран")
            else:
                return ActionResult(success=False, message="Блокировка экрана не поддерживается на этой ОС")
        except Exception as e:
            logger.error(f"lock_screen error: {e}")
            return ActionResult(success=False, message=f"Ошибка: {e}")

        return ActionResult(success=True, message="Экран заблокирован")

    def get_capability(self) -> dict:
        return {"action": "lock_screen", "description": "Заблокировать экран"}


class EmptyTrashAction(BaseAction):
    action_name = "empty_trash"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        if dry_run:
            return ActionResult(success=True, message="Очистка корзины")

        system = platform_module.system()
        try:
            if system == "Darwin":
                proc = subprocess.run(
                    ["osascript", "-e", 'tell application "Finder" to empty trash'],
                    capture_output=True, text=True, timeout=30,
                )
                if proc.returncode != 0:
                    return ActionResult(success=False, message=f"Ошибка: {proc.stderr}")
            elif system == "Windows":
                try:
                    import winshell
                    winshell.empty_recycle_bin()
                except ImportError:
                    return ActionResult(success=False, message="winshell не установлен")
            else:
                return ActionResult(success=False, message="Очистка корзины не поддерживается на этой ОС")
        except Exception as e:
            logger.error(f"empty_trash error: {e}")
            return ActionResult(success=False, message=f"Ошибка: {e}")

        return ActionResult(success=True, message="Корзина очищена")

    def get_capability(self) -> dict:
        return {"action": "empty_trash", "description": "Очистить корзину"}


class RunCommandAction(BaseAction):
    action_name = "run_command"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        cmd = command.get("command", "")
        if not cmd:
            return ActionResult(success=False, message="Не указана команда для выполнения")

        # SECURITY: dry_run=true by default, requires explicit confirm
        if not dry_run:
            confirm = command.get("confirm", False)
            if not confirm:
                return ActionResult(
                    success=False,
                    message="Требуется подтверждение. Передайте confirm=true для выполнения.",
                    data={"command": cmd, "requires_confirm": True},
                )

            system = platform_module.system()
            shell = "cmd" if system == "Windows" else True  # True = /bin/sh
            try:
                proc = subprocess.run(
                    cmd,
                    shell=shell,
                    capture_output=True, text=True, timeout=command.get("timeout", 30),
                )
                stdout = proc.stdout
                stderr = proc.stderr
                return ActionResult(
                    success=proc.returncode == 0,
                    message=f"Команда выполнена (exit code: {proc.returncode})",
                    data={
                        "stdout": stdout,
                        "stderr": stderr,
                        "returncode": proc.returncode,
                    },
                )
            except subprocess.TimeoutExpired:
                return ActionResult(success=False, message="Команда превысила таймаут")
            except Exception as e:
                logger.error(f"run_command error: {e}")
                return ActionResult(success=False, message=f"Ошибка выполнения: {e}")

        # dry_run=True
        return ActionResult(
            success=True,
            message=f"Команда (dry run): {cmd[:100]}",
            data={"command": cmd},
        )

    def get_capability(self) -> dict:
        return {
            "action": "run_command",
            "description": "Выполнить команду в терминале (требует подтверждения)",
            "params": {
                "command": "string (обязательно)",
                "confirm": "bool (обязательно true для выполнения)",
                "timeout": "int (опционально, секунды)",
            },
        }


class OpenTrashAction(BaseAction):
    action_name = "open_trash"

    async def execute(self, command: dict, dry_run: bool = False) -> ActionResult:
        if dry_run:
            return ActionResult(success=True, message="Открытие корзины")

        system = platform_module.system()
        try:
            if system == "Darwin":
                trash_path = os.path.expanduser("~/.Trash")
                if not os.path.isdir(trash_path):
                    return ActionResult(success=False, message="Папка корзины не найдена")
                proc = subprocess.run(["open", trash_path], capture_output=True, text=True, timeout=5)
                if proc.returncode != 0:
                    return ActionResult(success=False, message=f"Ошибка: {proc.stderr}")
            elif system == "Windows":
                proc = subprocess.run(["explorer", "shell:RecycleBinFolder"], timeout=5)
                if proc.returncode != 0:
                    return ActionResult(success=False, message="Не удалось открыть корзину")
            else:
                return ActionResult(success=False, message="Открытие корзины не поддерживается на этой ОС")
        except Exception as e:
            logger.error(f"open_trash error: {e}")
            return ActionResult(success=False, message=f"Ошибка: {e}")

        return ActionResult(success=True, message="Корзина открыта")

    def get_capability(self) -> dict:
        return {"action": "open_trash", "description": "Открыть папку корзины"}
