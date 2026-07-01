# 02-plan.md — план реализации (GLM-5.2)

## Goal A: Голосовая активация (L)

**Файлы:**
- [ ] `voice/wake_word.py` — детекция «Руслан» (Vosk)
- [ ] `voice/stt.py` — запись + распознавание команды
- [ ] `voice/manager.py` — оркестратор (wake → listen → STT → Brain)
- [ ] `core/main.py` — интеграция VoiceManager
- [ ] `ui/overlay.py` — статусы «Слушаю...», «Думаю...», «Говорю...»

**Зависимости:** `vosk` (лёгкий, офлайн), `sounddevice` или `pyobjc-framework-AVFoundation`, `numpy`

**Альтернативы:** `SpeechRecognition` + Google Web Speech API (если Vosk не ставится)

**Тесты:** `test_wake_word.py`, `test_stt.py`, `test_voice_integration.py`

---

## Goal B: PNG-спрайт персонажа (M)

**Файлы:**
- [ ] `assets/sprites/idle.png`, `thinking.png`, `speaking.png`, `happy.png`, `sad.png`, `working.png`
- [ ] `ui/sprite_widget.py` — Pillow ImageTk вместо эмодзи
- [ ] `ui/overlay.py` — проброс статусов

**Зависимости:** `Pillow` (или встроенный tkinter.PhotoImage)

**Альтернатива:** GIF-спрайты если PNG с альфа глючит

**Тесты:** `test_sprite_widget.py`, `test_overlay_sprite.py`

---

## Goal C: .dmg установщик (L)

**Файлы:**
- [ ] `build.spec` — PyInstaller конфиг
- [ ] `scripts/build_dmg.sh` — сборка .app → .dmg
- [ ] `scripts/com.valldun1.ruslan-desktop.plist` — launchd автозапуск
- [ ] `assets/app_icon.icns` — иконка

**Зависимости:** `pyinstaller`, нативные `hdiutil`, `cp`

**Альтернатива:** `py2app` (если PyInstaller падает), zip-архив (если hdiutil сложен)

**Тесты:** `test_installer.py`, ручная проверка
