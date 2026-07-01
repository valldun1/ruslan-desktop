# ДЕТАЛЬНЫЙ ПОШАГОВЫЙ ПЛАН ИСПОЛНЕНИЯ — Ruslan Desktop Agent (MVP)

**Репозиторий:** `valldun1/ruslan-desktop`
**Локация:** `~/projects/ruslan/`
**Ветка:** `main`

---

## Phase 0: Окружение и верификация скелета

**Файлы:** `.env`, `pyproject.toml`, `config/settings.json`, `core/config.py`
**Команды:** `pip install -e ".[dev]"`, `pytest tests/ -v`
**Критерий:** pip install успешен, тесты зелёные (4-5 тестов), конфиг читается.

- [ ] **0.1** — Проверить Python 3.12+
- [ ] **0.2** — Установить зависимости `pip install -e ".[dev]"`
- [ ] **0.3** — Настроить `.env` (`cp .env.example .env`)
- [ ] **0.4** — Создать `data/`, `logs/`, `voice/output/`
- [ ] **0.5** — Проверить импорт конфига
- [ ] **0.6** — Запустить существующие тесты `pytest tests/ -v`

---

## Phase 1: Платформенная абстракция + macOS Controller

**Файлы:** `core/platform.py` (новый), `macos/__init__.py` (новый), `macos/controller.py` (новый), `windows/controller.py` (рефакторинг), `actions/window_ops.py` (рефакторинг), `pyproject.toml` (+macos extras)
**Критерий:** Платформа определяется, macOS Controller импортируется, Windows Controller не ломается.

- [ ] **1.1** — Создать `core/platform.py` (OSType enum, Platform класс, get_controller)
- [ ] **1.2** — Создать `macos/__init__.py`
- [ ] **1.3** — Создать `macos/controller.py` (MacOSController: AppleScript + pyautogui)
- [ ] **1.4** — Обновить `windows/controller.py` (добавить right_click, show_notification)
- [ ] **1.5** — Добавить `macos` extras в `pyproject.toml`
- [ ] **1.6** — Обновить `actions/window_ops.py` — использовать `platform.get_controller()`
- [ ] **1.7** — Проверить импорт `python -c "from core.platform import platform; print(platform.os_name)"`

---

## Phase 2: Action Engine — недостающие действия

**Файлы:** `actions/mouse_ops.py` (новый), `actions/keyboard_ops.py` (новый), `actions/web_ops.py` (новый), `actions/utility_ops.py` (новый), `actions/engine.py` (обновить), `actions/__init__.py` (обновить)
**Критерий:** 18+ действий зарегистрированы, тесты проходят.

- [ ] **2.1** — Создать `actions/mouse_ops.py` (Click, DoubleClick, RightClick, Scroll)
- [ ] **2.2** — Создать `actions/keyboard_ops.py` (TypeText, PressKey, Hotkey)
- [ ] **2.3** — Создать `actions/web_ops.py` (SearchWeb — открывает браузер с поиском)
- [ ] **2.4** — Создать `actions/utility_ops.py` (Screenshot, Wait, Message)
- [ ] **2.5** — Обновить `actions/engine.py` — зарегистрировать все новые действия
- [ ] **2.6** — Проверить capabilities: `python -c "from actions.engine import action_engine; action_engine.register_all(); print(action_engine.get_capabilities())"`

---

## Phase 3: Brain — интеграция с Hermes (gateway)

**Файлы:** `brain/gateway.py`, `brain/schemas.py`, `.env`
**Критерий:** Gateway подключается к Hermes API (или fallback), structured JSON парсится.

- [ ] **3.1** — Протестировать gateway напрямую (asyncio.run → process_request)
- [ ] **3.2** — Улучшить system prompt (few-shot, русский язык, absolute paths)
- [ ] **3.3** — Добавить retry + timeout в gateway (tenacity или ручной)
- [ ] **3.4** — Добавить контекстный мемори (последние 3-5 команд из истории)
- [ ] **3.5** — Проверить обработку сложных запросов (curl /chat)
- [ ] **3.6** — Протестировать fallback (недоступный API → message-команда)

---

## Phase 4: API сервер — запуск и тестирование

**Файлы:** `api/main.py`
**Критерий:** API стартует, /health 200, /capabilities 18+, WebSocket принимает.

- [ ] **4.1** — Запустить API `python -m api.main`
- [ ] **4.2** — Проверить health `curl /health`
- [ ] **4.3** — Проверить capabilities `curl /capabilities`
- [ ] **4.4** — Проверить command endpoint (dry run)
- [ ] **4.5** — Проверить WebSocket (Godot mock через websockets)
- [ ] **4.6** — Добавить graceful shutdown (lifespan)

---

## Phase 5: Godot — спрайты и анимации

**Файлы:** `character/godot_project/assets/` (PNG), `main.tscn` (AnimatedSprite2D), `main.gd` (анимации), `api/main.py` (+ /animate)
**Критерий:** Персонаж отображается, проигрывает idle, реагирует на WS.

- [ ] **5.1** — Создать спрайт-лист (AI / placeholder / OpenGameArt)
- [ ] **5.2** — Настроить AnimatedSprite2D в Godot (6 анимаций)
- [ ] **5.3** — Обновить `main.gd` — использовать AnimatedSprite2D
- [ ] **5.4** — Добавить эндпоинт `POST /animate` в API
- [ ] **5.5** — Тест: анимация из API (curl /animate → Godot получает)

---

## Phase 6: Voice — донастройка STT/TTS

**Файлы:** `voice/engine.py`, `api/main.py` (+ /voice), `voice/wake.py` (опционально)
**Критерий:** Whisper транскрибирует, XTTS генерирует речь.

- [ ] **6.1** — Установить voice-зависимости (faster-whisper, TTS)
- [ ] **6.2** — Обновить `voice/engine.py` — убрать stubs
- [ ] **6.3** — Добавить эндпоинт `/voice` (audio → STT → Hermes → TTS)
- [ ] **6.4** — Wake word detection (pvporcupine / vosk)

---

## Phase 7: Плагины — Telegram + Browser (CDP)

**Файлы:** `plugins/telegram/manifest.json`, `plugins/telegram/plugin.py`, `plugins/browser/manifest.json`, `plugins/browser/plugin.py`
**Критерий:** Плагины обнаруживаются, загружаются, регистрируются.

- [ ] **7.1** — Telegram Plugin (send_telegram, read_telegram через Telethon)
- [ ] **7.2** — Browser Plugin (browser_navigate, browser_click, browser_extract через Playwright)
- [ ] **7.3** — Проверить интеграцию плагинов с ActionEngine

---

## Phase 8: Память — история и настройки

**Файлы:** `memory/store.py`, `api/main.py` (+ /history, /settings)
**Критерий:** SQLite работает, история сохраняется, настройки читаются/пишутся.

- [ ] **8.1** — Добавить методы get_history, clear_history в memory/store.py
- [ ] **8.2** — Добавить эндпоинты /history, /settings в API
- [ ] **8.3** — Интегрировать сохранение истории в /chat

---

## Phase 9: E2E тесты

**Файлы:** `tests/test_api.py` (новый), `tests/test_e2e.py` (новый), `tests/test_plugins.py` (новый), `tests/test_macos.py` (новый), `tests/conftest.py` (обновить)
**Критерий:** >80% покрытие core+actions, 15+ тестов, все зелёные.

- [ ] **9.1** — `test_api.py` — тесты REST API (health, capabilities, command)
- [ ] **9.2** — `test_e2e.py` — полный цикл chat → LLM → action → result
- [ ] **9.3** — `test_plugins.py` — discover, load, register
- [ ] **9.4** — `test_macos.py` — macOS Controller (skip if not macOS)
- [ ] **9.5** — `conftest.py` — общие фикстуры (reset globals)

---

## Phase 10: GitHub Actions (CI)

**Файлы:** `.github/workflows/ci.yml` (новый)
**Критерий:** CI проходит на push (Python 3.12, macOS+ubuntu+windows).

- [ ] **10.1** — Создать `.github/workflows/ci.yml` (lint + typecheck + test на 3 ОС)
- [ ] **10.2** — Проверить локально (ruff + mypy)

---

## Phase 11: Документация и релиз

**Файлы:** `README.md`, `AGENTS.md`, `PLAN.md`
**Критерий:** README актуален, релизный тег v0.1.0.

- [ ] **11.1** — Обновить README.md (скриншоты, архитектура, требования)
- [ ] **11.2** — Создать AGENTS.md (инструкция для агента-разработчика)
- [ ] **11.3** — Обновить PLAN.md с текущим статусом
- [ ] **11.4** — Тегнуть релиз `git tag v0.1.0 && git push --tags`
- [ ] **11.5** — Написать release notes

---

## Карта зависимостей

```
Phase 0 (Env) ──→ Phase 1 (Platform) ──→ Phase 2 (Actions) ──→ Phase 4 (API)
                        │                      │                       │
                        ↓                      ↓                       ↓
                 Phase 3 (Brain) ◄─────────────┘               Phase 5 (Godot)
                        │                                      Phase 6 (Voice)
                        ↓                                      Phase 7 (Plugins)
                 Phase 8 (Memory) ◄──────────────────────────────┘
                        │
                        ↓
                 Phase 9 (Tests) ──→ Phase 10 (CI) ──→ Phase 11 (Docs/Release)
```

**Параллельные треки:**
- Phase 5 (Godot) — параллельно с Phase 2-4
- Phase 6 (Voice) — параллельно с Phase 7 (Plugins)
- Phase 10 (CI) — как только есть тесты

---

## Критерии завершения MVP

| Критерий | Фаза | Проверка |
|----------|------|----------|
| `pip install -e ".[dev]"` работает | 0 | exit code 0 |
| `python -m api.main` стартует | 4 | `/health` → 200 |
| `pytest tests/ -v` — зелёные | 9 | 15+ passed |
| macOS Controller создан | 1 | импорт без ошибок |
| Godot подключается по WS | 5 | POST /animate → Godot получает |
| Hermes gateway отвечает | 3 | structured JSON парсится |
| 18+ действий в capabilities | 2 | curl /capabilities |
| CI проходит на push | 10 | GitHub Actions ✅ |
| Release tag v0.1.0 | 11 | `git tag -l` |
