# 00-context.md — ruslan-desktop

## Проект
**ruslan-desktop** (v0.2.1) — визуальный AI-агент «Руслан» для macOS/Windows.
Репозиторий: https://github.com/valldun1/ruslan-desktop
Локально: ~/Desktop/ruslan-desktop/

## Архитектура
- core/main.py — точка входа (tkinter overlay + Brain + Action Engine)
- ui/ — оверлей, чат-диалог, горячая клавиша, drag-drop, аниматор спрайта
- brain/ — Hermes LLM + Ollama fallback
- actions/ — 20 действий (file_ops, window, mouse, keyboard, web, utility)
- voice/ — системный TTS (macOS say / Win SAPI)
- plugins/ — Telegram (telethon), Browser (playwright)

## Текущее состояние
✅ 55 тестов, 0 падений
✅ tkinter overlay (вместо PyQt5 — не собирался на macOS 10.13)
✅ Диалог чата (клик по спрайту → ввод → Brain → ответ)
✅ Горячая клавиша Cmd+Shift+R (отключается через .env)
✅ Action Engine: 20 действий
✅ Brain: Hermes + Ollama fallback
✅ Системный TTS (macOS say)

## Что нужно доделать (3 пункта)

### 1. Voice activation — голосовой ввод
Сейчас: пользователь печатает текст в диалог
Надо: wake word «Руслан» → запись голоса → STT (faster-whisper) → Brain
Проблемы: faster-whisper тяжелый (~2GB моделей), на macOS 10.13 может не собраться

### 2. PNG-спрайт вместо эмодзи
Сейчас: в оверлее показывается эмодзи 🛡
Надо: создать PNG-спрайт персонажа (по референсу — в image_cache/img_fa965c3a1905.jpg)
6 состояний анимации: idle, thinking, speaking, happy, sad, working

### 3. .dmg установщик
Сейчас: устанавливается через pip install
Надо: собрать macOS .dmg с drag-and-drop установкой, включить Python + зависимости
