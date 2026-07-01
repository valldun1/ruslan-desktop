# 00-context.md — Контекст проекта

## Проект
**Ruslan Desktop Agent** — визуальный AI-агент для Windows/macOS.

## Репозиторий
`~/projects/ruslan/` → `valldun1/ruslan-desktop`

## Текущее состояние
Скелет проекта (35 файлов):
- core/: config, event_bus, task_queue, logger ✅
- brain/: schemas (17 команд), gateway (Hermes) ✅
- actions/: base, engine, file_ops, window_ops ✅
- windows/: controller (pyautogui) ✅
- api/: FastAPI + WebSocket ✅
- voice/: engine (Whisper + XTTS stub) ✅
- memory/: store (SQLite) ✅
- plugins/: manager + example ✅
- character/godot_project/: project.godot, main.tscn, main.gd ✅
- tests/: test_core.py, test_actions.py ✅
- config/: settings.json, pyproject.toml, .gitignore ✅
- PLAN.md: 11 фаз ✅

## Что нужно доделать (из PLAN.md)
- macOS Controller (macos/controller.py)
- Платформенная абстракция (платформа auto-detect)
- Интеграция с Гермесом (gateway)
- Godot анимации (idle, walk, think, search)
- Voice — реальный STT/TTS
- Плагины — Telegram, браузер
- E2E тесты
- CI (GitHub Actions)

## Окружение
- Текущая платформа: Termux (Android) — не Windows, не macOS
- Модель: kimi-k2.5 через OpenCode Go
- GH_TOKEN есть (~/.gh_token)
- Python: через pip/uv

## Автор
Valentin (Кэп), яхта YCCOM. Экосистема Руслан: ruslan, go_ruslan_team, nano_ruslan, ruslan-android, ruslan-desktop.
