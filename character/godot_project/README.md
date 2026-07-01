### Godot Project: Руслан — Desktop Character

## Requirements

- Godot 4.2+ (stable)
- Windows OS (for transparent always-on-top overlay)

## Setup

1. Открой `character/godot_project/` в Godot 4
2. Нажми **Play** — увидишь окно персонажа поверх рабочего стола
3. Для прозрачного фона: `Project → Settings → Display → Window → Transparent = On`

## How it works

```
Python API  ←WebSocket→  Godot Character
```

Godot подключается к Python API по WebSocket (`ws://127.0.0.1:8000/ws/character`).

Когда приходит событие — Godot проигрывает анимацию.

## Events from Python

| Event | Data | Animation |
|-------|------|-----------|
| `task_started` | `{action: "open_app"}` | Walk → Think |
| `task_completed` | `{success: true}` | Celebrate / Idle |
| `action:anim` | `{animation: "walk", x: 100, y: 200}` | Move character |

## Events to Python

| Event | When |
|-------|------|
| `animation_finished` | Анимация закончена |
| `click_through` | Пользователь кликнул сквозь окно |
| `ready` | Персонаж загружен |

## Structure

```
godot_project/
├── project.godot
├── main.tscn              # Main scene (Sprite2D + WebSocket)
├── main.gd                # Main script
├── assets/
│   ├── ruslan_spritesheet.png
│   └── animations.tres
└── scenes/
    └── character.tscn
```

## Creating animations

1. Создай или найди спрайт-лист персонажа (2D Spine / Live2D)
2. Настрой `AnimationPlayer` с анимациями:
   - `idle` — стоит
   - `walk` — идёт
   - `think` — думает (руки скрещены)
   - `search` — ищет (достаёт голограмму)
   - `celebrate` — радуется
   - `error` — ошибка
3. Подключи к событиям из WebSocket
