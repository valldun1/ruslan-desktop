# 🛡 Руслан Desktop Agent — План выполнения (MVP)

**Репозиторий:** `valldun1/ruslan-desktop`  
**Локация:** `~/projects/ruslan/`  
**Ветка:** `main`  

---

## Структура плана

Каждый этап — `Phase N: Name`.  
Внутри этапа — задачи с номером.  
Запуск по команде: `"Фаза 1"` или `"Задача 2.3"`.

---

# Phase 0: Окружение и настройка

Запустить одной командой: `"Фаза 0"`

### 0.1 Установить зависимости Python
```bash
cd ~/projects/ruslan
pip install -e ".[all]"
```

### 0.2 Настроить .env
```bash
cp .env.example .env
# Отредактировать HERMES_API_URL, HERMES_API_KEY
```

### 0.3 Проверить конфигурацию
```bash
python -c "from core.config import settings; print(settings.model_dump())"
```

### 0.4 Создать структуру данных
```bash
cd ~/projects/ruslan
mkdir -p data logs voice/output
```

### 0.5 Запустить тесты (проверка скелета)
```bash
cd ~/projects/ruslan && python -m pytest tests/ -v
```

**Ожидаемый результат:** все тесты зелёные.

---

# Phase 1: API сервер + Health

### 1.1 Запустить API
```bash
cd ~/projects/ruslan && python -m api.main
```

### 1.2 Проверить health
```bash
curl http://127.0.0.1:8000/health
# → {"status": "ok"}
```

### 1.3 Проверить capabilities
```bash
curl http://127.0.0.1:8000/capabilities | python -m json.tool
```
→ список всех 17 действий.

### 1.4 Проверить команду напрямую
```bash
curl -X POST http://127.0.0.1:8000/command \
  -H "Content-Type: application/json" \
  -d '{"action": "search_file", "query": "ruslan"}'
```

### 1.5 Проверить chat endpoint
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "найди файл ruslan"}'
```

---

# Phase 2: Brain — интеграция с Гермесом

### 2.1 Проверить, что gateway может подключиться к Hermes
```bash
cd ~/projects/ruslan && python -c "
import asyncio
from brain.gateway import gateway
result = asyncio.run(gateway.process_request('скажи привет'))
print(result.model_dump_json(indent=2))
"
```

### 2.2 Протестировать system prompt на сложный запрос
```bash
cd ~/projects/ruslan && python -c "
import asyncio
from brain.gateway import gateway
result = asyncio.run(gateway.process_request('открой Telegram и отправь сообщение'))
print('Plan:', result.plan)
print('Commands:', [c.model_dump() for c in result.commands])
"
```

### 2.3 Проверить fallback (если Hermes недоступен)
```bash
cd ~/projects/ruslan && HERMES_API_URL=http://localhost:9999 python -c "
import asyncio
from brain.gateway import gateway
result = asyncio.run(gateway.process_request('тест'))
print(result.model_dump_json(indent=2))
"
```

### 2.4 Оптимизировать system prompt (если Hermes галлюцинирует)
- Отредактировать `brain/gateway.py` → SYSTEM_PROMPT
- Уменьшить temperature до 0.0
- Добавить примеры few-shot

---

# Phase 3: Windows Controller (реальный)

### 3.1 Установить Windows-зависимости
```bash
pip install ruslan[windows]
```

### 3.2 Протестировать controller
```bash
cd ~/projects/ruslan && python -c "
from windows.controller import windows_controller
windows_controller.init()
print('Windows:', windows_controller.is_windows)
print('Ready:', windows_controller._initialized)
"
```

### 3.3 Тест: движение мыши
```bash
cd ~/projects/ruslan && python -c "
import asyncio
from windows.controller import windows_controller
windows_controller.init()
windows_controller.move_to(500, 500)
print('Mouse moved')
"
```

### 3.4 Тест: открыть блокнот + напечатать текст
```bash
cd ~/projects/ruslan && python -c "
import subprocess, time
from windows.controller import windows_controller
windows_controller.init()
subprocess.Popen(['notepad.exe'])
time.sleep(1)
windows_controller.type_text('Привет, Руслан!')
"
```

### 3.5 Тест: скриншот + сохранение
```bash
cd ~/projects/ruslan && python -c "
from windows.controller import windows_controller
windows_controller.init()
img = windows_controller.screenshot()
if img:
    img.save('logs/test_screenshot.png')
    print('Screenshot saved')
"
```

### 3.6 Safe Executor — проверить dry_run + confirm
```bash
cd ~/projects/ruslan && python -c "
from actions.file_ops import DeleteFileAction
import asyncio
action = DeleteFileAction()
result = asyncio.run(action.execute({'path': '/tmp/test.txt', 'permanent': True}, dry_run=True))
print('Dry run:', result.message)
"
```

---

# Phase 4: Godot Character — визуализация

### 4.1 Открыть Godot проект
```bash
# На Windows с установленным Godot:
start godot character/godot_project/project.godot
```

### 4.2 Запустить API сервер
```bash
cd ~/projects/ruslan && python -m api.main
```

### 4.3 Нажать Play в Godot
- Откроется прозрачное окно с персонажем
- В терминале API появится: `"Godot character connected"`

### 4.4 Тест: отправить анимацию из API
```bash
cd ~/projects/ruslan && python -c "
import asyncio, websockets
async def test():
    async with websockets.connect('ws://127.0.0.1:8000/ws/character') as ws:
        await ws.send('{\"event\": \"task_started\", \"data\": {\"action\": \"search_file\"}}')
        print('Sent event')
        resp = await asyncio.wait_for(ws.recv(), timeout=3.0)
        print('Got:', resp)
asyncio.run(test())
"
```

### 4.5 Добавить спрайт персонажа
- Найти/нарисовать спрайт-лист Руслана (кибер-рыцарь)
- Поместить: `assets/sprites/ruslan_spritesheet.png`
- Настроить AnimatedSprite2D в Godot

### 4.6 Создать анимации в Godot
| Анимация | Описание |
|----------|----------|
| `idle` | стоит, слабое дыхание |
| `walk` | идёт в сторону |
| `think` | скрестил руки, зелёное свечение глаз |
| `search` | достаёт голограмму |
| `celebrate` | поднимает меч |
| `error` | качает головой |

### 4.7 Подключить анимации к событиям
- `main.gd` → `_play_action_animation()` уже написан
- Проверить, что каждая анимация проигрывается

---

# Phase 5: Voice — голосовое управление

### 5.1 Установить voice-зависимости (опционально)
```bash
pip install ruslan[voice]
```

### 5.2 Проверить STT (Whisper)
```bash
cd ~/projects/ruslan && python -c "
import asyncio
from voice.engine import voice_engine
text = asyncio.run(voice_engine.transcribe('voice/test_sample.wav'))
print('Transcribed:', text)
"
```

### 5.3 Проверить TTS (XTTS)
```bash
cd ~/projects/ruslan && python -c "
import asyncio
from voice.engine import voice_engine
path = asyncio.run(voice_engine.speak('Привет, я Руслан'))
print('Audio saved:', path)
"
```

### 5.4 Интегрировать voice loop с API
- Добавить эндпоинт `POST /voice` (принимает аудио → STT → Hermes → execute → TTS)
- Модифицировать WebSocket для передачи аудио

### 5.5 Wake word detection
```bash
# Установить porcupine или Vosk
pip install pvporcupine
```
- Добавить always-listening на "Руслан"

---

# Phase 6: Плагины

### 6.1 Создать плагин для Telegram
```bash
mkdir -p plugins/telegram
```
- `manifest.json`:
```json
{"name": "telegram", "capabilities": [{"action": "send_telegram", "description": "Отправить сообщение в Telegram", "params": {"chat_id": "string", "text": "string"}}]}
```
- `plugin.py`: BaseAction → `SendTelegramAction`

### 6.2 Загрузить плагин
```bash
cd ~/projects/ruslan && python -c "
from plugins.manager import plugin_manager
actions = plugin_manager.load_all()
print(f'Loaded {len(actions)} plugin actions')
"
```

### 6.3 Создать плагин для браузера (Chrome CDP)
```bash
pip install playwright
playwright install chromium
```
- `plugins/browser/manifest.json`
- `plugins/browser/plugin.py` → OpenUrlAction, SearchWebAction (через CDP вместо shell)

---

# Phase 7: Память и логи

### 7.1 Проверить SQLite
```bash
cd ~/projects/ruslan && python -c "
from memory.store import memory
memory.connect()
memory.save_history('тест', 'ответ', [{'action': 'test'}])
print('Saved. Setting:', memory.get_setting('language', 'ru'))
"
```

### 7.2 Проверить логгирование
```bash
cat logs/ruslan.log | tail -10
```

### 7.3 Настроить ротацию логов
- loguru уже настроена: 10MB, 30 дней, сжатие

---

# Phase 8: E2E тестирование

### 8.1 Smoke test — полный цикл
```bash
# 1. API запущен
# 2. Отправить команду
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "открой калькулятор"}'

# 3. Проверить, что калькулятор открылся
# 4. Проверить лог
cat logs/ruslan.log | grep "Opened"
```

### 8.2 Тест: файловые операции
```bash
cd ~/projects/ruslan && python -c "
from actions.engine import action_engine
import asyncio

# Создать тестовый файл
open('/tmp/test_ruslan.txt', 'w').write('hello')

# Переместить
r = asyncio.run(action_engine.execute({'action': 'move_file', 'source': '/tmp/test_ruslan.txt', 'destination': '/tmp/test_moved.txt'}))
print('Move:', r.message)

# Найти
r = asyncio.run(action_engine.execute({'action': 'search_file', 'query': 'test_moved'}))
print('Search:', r.message, r.data)
"
```

### 8.3 Тест: Godot → API → обратно
```bash
# Запустить API
# Запустить Godot
# Отправить из Godot событие
# Проверить, что API получил
```

---

# Phase 9: Документация и деплой

### 9.1 Обновить README
```bash
# README.md уже есть — дополнить скриншотами
```

### 9.2 Создать GUILD (руководство для агентов)
```bash
# AGENTS.md — инструкция для ИИ-агента
cat > AGENTS.md << 'EOF'
# Инструкция для агента-разработчика

## Проект: ruslan-desktop
Руслан — визуальный desktop AI-агент.

## Стек
- Python 3.12 + FastAPI + WebSocket
- Godot 4 (персонаж)
- Hermes (LLM мозг)

## Структура
см. README.md

## Первый запуск
1. pip install -e ".[dev]"
2. python -m api.main
3. Открыть Godot проект character/godot_project/

## Ключевые принципы
- Не вызывать Win32 из других модулей — только через windows/controller.py
- Все команды проходят через Action Engine
- Все события — через EventBus
- Плагины — в plugins/

## Текущая задача
...
EOF
```

### 9.3 Тегнуть релиз
```bash
cd ~/projects/ruslan
git tag v0.1.0 -m "MVP: скелет проекта"
git push origin v0.1.0
```

### 9.4 Настроить GitHub Actions (CI)
```bash
mkdir -p .github/workflows
```
- `ci.yml`: pytest на push

---

# Phase 10: Полировка — анимации и FX

### 10.1 Создать визуальные эффекты в Godot
- GPUParticles2D для "матрицы" вокруг головы
- Shader для свечения зелёных глаз
- Анимация "портала" при сложных задачах

### 10.2 Добавить эмоции персонажа
| Эмоция | Триггер |
|--------|---------|
| 😊 Радость | задача выполнена |
| 🤔 Думает | Гермес обрабатывает |
| 😢 Ошибка | action failed |
| 😴 Спит | idle > 30 секунд |

### 10.3 Click-through toggle
- Горячая клавиша (Scroll Lock) → персонаж "активируется"
- В активном режиме — клики перехватываются
- В пассивном — клики проходят сквозь

---

# Команды для агента

Для запуска конкретного этапа используй:

```
Ruslan, выполни Фазу 0
Ruslan, задача 2.1
Ruslan, Phase 3
```

Каждый блок начинается с одной команды.
После выполнения — перейти к следующей.

---

## Легенда статуса

| Маркер | Значение |
|--------|----------|
| ⬜ | Не начато |
| 🟡 | В процессе |
| ✅ | Готово |
| ❌ | Ошибка / блокер |

---

## Текущий статус (на момент создания)

⬜ Phase 0 — Окружение
⬜ Phase 1 — API сервер
⬜ Phase 2 — Brain / Hermes
⬜ Phase 3 — Windows Controller
⬜ Phase 4 — Godot Character
⬜ Phase 5 — Voice
⬜ Phase 6 — Плагины
⬜ Phase 7 — Память
⬜ Phase 8 — E2E
⬜ Phase 9 — Документация
⬜ Phase 10 — Полировка
