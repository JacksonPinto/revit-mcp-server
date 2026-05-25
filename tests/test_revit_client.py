"""Tests for the RevitClient using the MockRevitServer."""

from __future__ import annotations

import pytest

from revit_client import RevitClient, RevitConnectionError, feet_to_mm, mm_to_feet
from tests.mock_revit_server import MockRevitServer


@pytest.fixture(scope="module")
def mock_server():
    with MockRevitServer(port=48885) as server:
        yield server


@pytest.fixture
def client():
    from config import RevitConfig
    cfg = RevitConfig(host="localhost", port=48885)
    return RevitClient(config=cfg)


class TestUnitConversions:

    def test_mm_to_feet(self):
        assert abs(mm_to_feet(304.8) - 1.0) < 1e-6

    def test_feet_to_mm(self):
        assert abs(feet_to_mm(1.0) - 304.8) < 1e-6

    def test_round_trip(self):
        original = 12345.678
        assert abs(feet_to_mm(mm_to_feet(original)) - original) < 0.001


class TestRevitClientConnectivity:

    @pytest.mark.asyncio
    async def test_ping(self, mock_server, client):
        async with client as c:
            result = await c.ping()
        assert result["status"] == "ok"
        assert result["revit_version"] == "2025"

    @pytest.mark.asyncio
    async def test_get_project_info(self, mock_server, client):
        async with client as c:
            result = await c.get("/revit/project/info")
        assert result["project_name"] == "Test Project"
        assert "project_number" in result

    @pytest.mark.asyncio
    async def test_get_levels(self, mock_server, client):
        async with client as c:
            result = await c.get("/revit/levels")
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["name"] == "Level 1"

    @pytest.mark.asyncio
    async def test_get_rooms(self, mock_server, client):
        async with client as c:
            result = await c.get("/revit/rooms")
        assert len(result) == 2
        assert result[0]["number"] == "101"

    @pytest.mark.asyncio
    async def test_404_raises_api_error(self, mock_server, client):
        from revit_client import RevitAPIError
        async with client as c:
            with pytest.raises(RevitAPIError) as exc:
                await c.get("/revit/nonexistent/endpoint")
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_connection_refused_raises_connection_error(self):
        from config import RevitConfig
        bad_client = RevitClient(config=RevitConfig(host="localhost", port=19999, max_retries=1))
        async with bad_client as c:
            with pytest.raises(RevitConnectionError):
                await c.ping()
