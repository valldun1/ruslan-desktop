"""FastAPI + WebSocket server — the API layer.

Handles:
- REST endpoints for health, capabilities, commands
- WebSocket for Godot character communication
- WebSocket for user voice/text input
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from core.config import settings
from core.event_bus import event_bus
from core.task_queue import task_queue, TaskStatus
from brain.gateway import gateway
from actions.engine import action_engine


# ── App ──────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown."""
    logger.info("Ruslan API starting...")
    # Register built-in actions
    import actions  # noqa: F401 — registers actions
    yield
    logger.info("Ruslan API shutting down...")


app = FastAPI(
    title="Ruslan Desktop Agent API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── WebSocket Connections ────────────────────────────

godot_connections: list[WebSocket] = []
user_connections: list[WebSocket] = []
_ = godot_connections, user_connections  # used in handlers


# ── REST Endpoints ──────────────────────────────────


@app.get("/")
async def root():
    return {"service": "ruslan", "status": "running", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/capabilities")
async def list_capabilities():
    """Return all registered action capabilities for Hermes."""
    return {"capabilities": action_engine.get_capabilities()}


@app.post("/command")
async def execute_command(command: dict):
    """Execute a single action command directly (no Hermes)."""
    result = await action_engine.execute(command)
    return {"result": result.model_dump()}


@app.post("/chat")
async def chat_endpoint(payload: dict):
    """Send user text → Hermes → execute commands."""
    user_text = payload.get("text", "")
    if not user_text:
        return {"error": "text is required"}

    llm_response = await gateway.process_request(user_text)

    # Execute commands
    results = []
    for cmd_model in llm_response.commands:
        cmd_dict = cmd_model.model_dump()
        result = await action_engine.execute(cmd_dict)
        results.append(result.model_dump())

    return {
        "plan": llm_response.plan,
        "commands": [c.model_dump() for c in llm_response.commands],
        "results": results,
        "response_text": llm_response.response_text,
    }


@app.post("/animate")
async def animate(payload: dict):
    """Send animation command to Godot character."""
    event = payload.get("event", "action:anim")
    data = payload.get("data", {})
    msg = json.dumps({"event": event, "data": data}, ensure_ascii=False)
    for conn in godot_connections.copy():
        try:
            await conn.send_text(msg)
        except Exception:
            godot_connections.remove(conn)
    return {"sent": True, "connections": len(godot_connections)}


# ── History / Settings Endpoints ──


@app.get("/history")
async def get_history(limit: int = 10):
    """Get recent command history."""
    from memory.store import memory
    return {"history": memory.get_history(limit)}


@app.delete("/history")
async def clear_history():
    """Clear all history."""
    from memory.store import memory
    memory.clear_history()
    return {"status": "cleared"}


@app.get("/settings/{key}")
async def get_setting(key: str):
    """Get a setting value."""
    from memory.store import memory
    return {"key": key, "value": memory.get_setting(key)}


@app.put("/settings/{key}")
async def set_setting(key: str, payload: dict):
    """Set a setting value."""
    from memory.store import memory
    value = payload.get("value", "")
    memory.set_setting(key, value)
    return {"key": key, "value": value}


# ── Voice Endpoint ──


@app.post("/voice")
async def voice_endpoint(payload: dict):
    """Receive audio → STT → Hermes → Execute → TTS."""
    from voice.engine import voice_engine
    audio_path = payload.get("audio_path", "")
    if not audio_path:
        return {"error": "audio_path required"}
    text = await voice_engine.transcribe(audio_path)
    llm_response = await gateway.process_request(text)
    response_text = llm_response.response_text or "Готово"
    audio_out = await voice_engine.speak(response_text)
    return {
        "transcribed": text,
        "response_text": response_text,
        "audio_output": audio_out,
    }


# ── WebSocket Endpoints ─────────────────────────────


@app.websocket("/ws/character")
async def character_websocket(ws: WebSocket):
    """Godot character connects here for real-time events."""
    await ws.accept()
    godot_connections.append(ws)
    logger.info("Godot character connected")

    async def send_to_character(event: str, **data):
        """Push event to Godot."""
        msg = json.dumps({"event": event, **data}, ensure_ascii=False)
        for conn in godot_connections.copy():
            try:
                await conn.send_text(msg)
            except Exception:
                godot_connections.remove(conn)

    # Subscribe to events
    async def on_task_started(**data): await send_to_character("task_started", **data)
    async def on_task_completed(**data): await send_to_character("task_completed", **data)

    event_bus.subscribe("task:started", on_task_started)
    event_bus.subscribe("task:completed", on_task_completed)

    try:
        while True:
            data = await ws.receive_text()
            logger.debug(f"From character: {data[:100]}")
    except WebSocketDisconnect:
        godot_connections.remove(ws)
        logger.info("Godot character disconnected")
    finally:
        event_bus.unsubscribe("task:started", on_task_started)
        event_bus.unsubscribe("task:completed", on_task_completed)


@app.websocket("/ws/user")
async def user_websocket(ws: WebSocket):
    """User sends text/voice here, gets real-time responses."""
    await ws.accept()
    user_connections.append(ws)
    logger.info("User connected")

    try:
        while True:
            data = await ws.receive_json()
            user_text = data.get("text", "")
            if not user_text:
                continue

            # Process through Hermes
            llm_response = await gateway.process_request(user_text)

            # Send Hermes response text back immediately
            if llm_response.response_text:
                await ws.send_json({"type": "thought", "text": llm_response.response_text})

            # Execute each command
            for cmd in llm_response.commands:
                cmd_dict = cmd.model_dump()
                await ws.send_json({"type": "action", "action": cmd_dict.get("action")})
                result = await action_engine.execute(cmd_dict)
                await ws.send_json({"type": "result", "result": result.model_dump()})

            # Final
            await ws.send_json({"type": "done"})

    except WebSocketDisconnect:
        user_connections.remove(ws)
        logger.info("User disconnected")


# ── Main ─────────────────────────────────────────────


def main() -> None:
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
