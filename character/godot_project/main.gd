extends Control

# Ruslan Character — Godot 4
# WebSocket client connecting to Python API

const WS_URL := "ws://127.0.0.1:8000/ws/character"

var _ws := WebSocketPeer.new()
var _connected := false
var _anim_player: AnimationPlayer
var _character: Sprite2D

# ── State ──
var _target_position: Vector2 = Vector2(200, 250)
var _speed: float = 300.0  # pixels/sec

func _ready() -> void:
	_anim_player = $AnimPlayer as AnimationPlayer
	_character = $CharacterSprite as Sprite2D
	_connect_ws()
	_play_idle()

func _process(delta: float) -> void:
	_ws.poll()
	
	if _ws.get_ready_state() == WebSocketPeer.STATE_OPEN and not _connected:
		_connected = true
		print("[Ruslan] Connected to API")
		_send({"event": "ready", "message": "Character ready"})
	
	if _ws.get_ready_state() == WebSocketPeer.STATE_CLOSED and _connected:
		_connected = false
		print("[Ruslan] Disconnected — retrying...")
		_connect_ws()
	
	# Read messages
	while _ws.get_available_packet_count() > 0:
		var packet = _ws.get_packet().get_string_from_utf8()
		_handle_message(packet)
	
	# Move character toward target
	var diff = _target_position - _character.position
	if diff.length() > 5.0:
		var step = diff.normalized() * _speed * delta
		if step.length() > diff.length():
			_character.position = _target_position
		else:
			_character.position += step
	
	# Click-through passthrough when idle
	if _character.position.distance_to(_target_position) < 5.0:
		mouse_filter = Control.MOUSE_FILTER_IGNORE
	else:
		mouse_filter = Control.MOUSE_FILTER_PASS  # block during animation

# ── WebSocket ──

func _connect_ws() -> void:
	_ws = WebSocketPeer.new()
	var err = _ws.connect_to_url(WS_URL)
	if err != OK:
		print("[Ruslan] WS connect error: ", err)
		# Retry after 2 seconds
		get_tree().create_timer(2.0).timeout.connect(_connect_ws)

func _send(data: Dictionary) -> void:
	if _ws.get_ready_state() == WebSocketPeer.STATE_OPEN:
		var json_str = JSON.stringify(data)
		_ws.send_text(json_str)

# ── Message handling ──

func _handle_message(raw: String) -> void:
	var data = JSON.parse_string(raw)
	if not data:
		return
	
	var event = data.get("event", "")
	var payload = data.get("data", {})
	
	match event:
		"task_started":
			var action = payload.get("action", "unknown")
			_play_action_animation(action)
		"task_completed":
			if payload.get("success", false):
				_play_celebrate()
			else:
				_play_error()
		"action:anim":
			_handle_anim_command(payload)
		_:
			print("[Ruslan] Unknown event: ", event)

func _handle_anim_command(data: Dictionary) -> void:
	var anim = data.get("animation", "")
	match anim:
		"walk":
			var x = data.get("x", _character.position.x)
			var y = data.get("y", _character.position.y)
			_target_position = Vector2(x, y)
			_play_anim("walk")
		"think":
			_play_anim("think")
		"search":
			_play_anim("search")
		"idle":
			_play_idle()
		"celebrate":
			_play_celebrate()
		"error":
			_play_error()
		_:
			_play_idle()

# ── Animations ──

func _play_anim(name: String) -> void:
	if _anim_player and _anim_player.has_animation(name):
		_anim_player.play(name)
	else:
		print("[Ruslan] No animation: ", name)

func _play_idle() -> void:
	_play_anim("idle")

func _play_celebrate() -> void:
	_play_anim("celebrate")
	# Emit finish event
	_send({"event": "animation_finished", "name": "celebrate"})

func _play_error() -> void:
	_play_anim("error")
	_send({"event": "animation_finished", "name": "error"})

func _play_action_animation(action: String) -> void:
	match action:
		"search_file", "search_web":
			_play_anim("search")
		"move_file", "copy_file", "delete_file":
			_play_anim("walk")
		"open_app", "open_folder", "open_url":
			_play_anim("walk")
		_:
			_play_anim("think")
	_send({"event": "animation_finished", "name": action + "_animation"})

# ── Enable interactive mode (when user clicks on character) ──

func _on_gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_send({"event": "click_through", "position": {"x": event.position.x, "y": event.position.y}})
