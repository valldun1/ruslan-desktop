# 🛡 Руслан — Desktop AI Agent

**Руслан** — визуальный ИИ-агент для Windows. Живёт на рабочем столе, принимает голосовые и текстовые команды, выполняет реальные действия на компьютере через **Гермеса** (LLM).

```
Пользователь → Голос/Текст → Гермес → JSON → Руслан (анимация) → Windows
```

---

## 🔥 Возможности MVP

| Действие | Команда | Пример |
|----------|---------|--------|
| 📂 Файлы | Переместить, скопировать, удалить, найти | *"Найди договор"* |
| 🪟 Окна | Открыть, закрыть программу | *"Открой Telegram"* |
| 🖱 Мышь | Клик, двойной клик, скролл | *"Нажми на кнопку"* |
| ⌨ Клавиатура | Напечатать, горячие клавиши | *"Набери Ctrl+S"* |
| 🌐 Веб | Открыть сайт, поискать | *"Найди в Яндексе..."* |
| 💬 Сообщения | Сказать что-то, показать эмоцию | *"Привет!"* |

---

## 🏗 Архитектура

```
ruslan/
├── core/                # config, event_bus, task_queue, logger
├── brain/               # gateway → Hermes LLM, Pydantic schemas
├── actions/             # Action Engine (17+ действий)
├── windows/             # Windows Controller (pyautogui)
├── voice/               # STT (Whisper) + TTS (XTTS)
├── memory/              # SQLite (история, настройки)
├── api/                 # FastAPI + WebSocket
├── plugins/             # Плагинная система + пример
├── character/           # Godot 4 проект персонажа
├── config/              # settings.json
├── logs/
└── tests/
```

---

## 🚀 Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/valldun1/ruslan.git
cd ruslan

# 2. Установить (рекомендуется uv)
pip install -e ".[dev]"

# 3. Настроить .env
cp .env.example .env
# → отредактировать HERMES_API_URL и HERMES_API_KEY

# 4. Запустить API
python -m api.main

# 5. Открыть Godot персонажа
# → character/godot_project/project.godot → Play
```

---

## 📡 API

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/` | GET | Статус |
| `/health` | GET | Health check |
| `/capabilities` | GET | Список всех действий |
| `/command` | POST | Выполнить одну команду |
| `/chat` | POST | Отправить запрос → Гермес → выполнить |
| `/ws/character` | WS | Godot персонаж |
| `/ws/user` | WS | Пользовательский интерфейс |

---

## 🎮 Godot Character

Персонаж работает в **прозрачном окне поверх рабочего стола**.

### Анимации (MVP)
- `idle` — пассивное состояние
- `walk` — идёт к цели
- `think` — думает (руки скрещены)
- `search` — ищет (зелёная голограмма)
- `celebrate` — успех
- `error` — ошибка

### Подключение
Godot подключается к Python API по WebSocket: `ws://127.0.0.1:8000/ws/character`

---

## 🔌 Плагины

Каждый плагин — папка с `manifest.json` + `plugin.py`:

```
plugins/
├── telegram/
│   ├── manifest.json     # {name, version, capabilities}
│   └── plugin.py         # class TelegramAction(BaseAction)
├── photoshop/
│   └── ...
```

Плагины загружаются автоматически при старте.

---

## 🛡 Безопасность

- **Dry Run** — режим симуляции без реальных действий
- **Подтверждение** — delete, execute требуют согласия
- **Windows Controller** — единственный модуль с доступом к WinAPI
- **Логирование** — все действия записываются в лог
- **Sandbox** — валидация путей перед выполнением

---

## 🗺 Дорожная карта

- [x] Архитектура и скелет проекта
- [x] Action Engine (17 действий)
- [x] Pydantic схемы команд
- [x] WebSocket мост для Godot
- [x] Плагинная система
- [ ] Спрайты и анимации Руслана
- [ ] Голосовое управление (Whisper)
- [ ] Озвучка (XTTS)
- [ ] Плагин для Telegram
- [ ] Плагин для браузера (CDP)
- [ ] Multi-agent (Афина, Гефест)

---

## 🧪 Тесты

```bash
pytest tests/ -v
```

---

## ⚖️ Лицензия

MIT — делай что хочешь, но помни: *Руслан — это душа, а не просто код.* 🛡
