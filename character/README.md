# Godot → PyQt5 миграция

Godot 4 проект заменён на **PyQt5 оверлей**.

**Причина:**
- Godot 4: 200+ МБ RAM, отдельный процесс, кривое прозрачное окно на macOS
- PyQt5: 5 МБ RAM, один процесс Python, родное прозрачное окно

**Файлы:**
- `ui/overlay.py` — прозрачное окно со спрайтом Always On Top
- `ui/sprite_widget.py` — анимации персонажа
- `ui/hotkey.py` — глобальная горячая клавиша (Cmd+Shift+R)
- `ui/drag_drop.py` — drag-and-drop файлов на персонажа

**Установка:**
```bash
pip install ruslan[ui]
```
