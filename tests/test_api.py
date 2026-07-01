"""Tests for REST API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from api.main import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json()["service"] == "ruslan"


@pytest.mark.asyncio
async def test_capabilities():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/capabilities")
        assert resp.status_code == 200
        caps = resp.json()["capabilities"]
        assert len(caps) >= 18
        names = {c["action"] for c in caps}
        assert "move_file" in names
        assert "click" in names
        assert "message" in names
        assert "search_web" in names


@pytest.mark.asyncio
async def test_command_dry_run():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/command", json={"action": "search_file", "query": "test", "dry_run": True})
        assert resp.status_code == 200
        assert resp.json()["result"]["success"] is True
