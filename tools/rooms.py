"""
Room and space tools.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient, mm_to_feet, sqft_to_sqm


def register_tools(mcp: McpServer) -> None:

    @mcp.tool()
    async def list_rooms(
        level_name: str | None = None,
        search: str | None = None,
        unplaced_only: bool = False,
    ) -> list[dict[str, Any]]:
        """
        List rooms in the project.

        Args:
            level_name: Optional level name to filter rooms.
            search: Optional search string for room name or number.
            unplaced_only: If True, return only unplaced rooms. Default: False.

        Returns each room's ID, number, name, level, area (m²), perimeter (m),
        and occupancy.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {"unplaced_only": unplaced_only}
            if level_name:
                params["level_name"] = level_name
            if search:
                params["search"] = search
            result = await client.get("/revit/rooms", params=params)
            # Convert area from ft² to m²
            for room in result:
                if "area" in room:
                    room["area_sqm"] = round(sqft_to_sqm(room.pop("area")), 2)
            return result

    @mcp.tool()
    async def get_room_by_number(room_number: str) -> dict[str, Any]:
        """
        Get detailed information about a room by its number.

        Args:
            room_number: The room number, e.g. '101' or 'A-101'.

        Returns the room's ID, name, number, level, area (m²), perimeter (m),
        height (m), and all room parameters.
        """
        async with RevitClient() as client:
            result = await client.get(
                "/revit/rooms/by_number", params={"room_number": room_number}
            )
            if "area" in result:
                result["area_sqm"] = round(sqft_to_sqm(result.pop("area")), 2)
            return result

    @mcp.tool()
    async def create_room(
        level_name: str,
        x_mm: float,
        y_mm: float,
        room_number: str | None = None,
        room_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Place a new room at a location on a level.

        Args:
            level_name: The level to place the room on.
            x_mm: X coordinate in mm (must be inside a room boundary).
            y_mm: Y coordinate in mm (must be inside a room boundary).
            room_number: Optional room number.
            room_name: Optional room name.

        Returns the new room's ElementId, number, and name.
        """
        async with RevitClient() as client:
            body: dict[str, Any] = {
                "level_name": level_name,
                "x": mm_to_feet(x_mm),
                "y": mm_to_feet(y_mm),
            }
            if room_number:
                body["room_number"] = room_number
            if room_name:
                body["room_name"] = room_name
            return await client.post("/revit/rooms/create", body)

    @mcp.tool()
    async def get_room_at_point(
        x_mm: float, y_mm: float, level_name: str
    ) -> dict[str, Any]:
        """
        Find which room contains a given point on a level.

        Args:
            x_mm: X coordinate in mm.
            y_mm: Y coordinate in mm.
            level_name: The level to check.

        Returns the room at that point, or {'room': None} if no room exists there.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/rooms/at_point",
                params={
                    "x": mm_to_feet(x_mm),
                    "y": mm_to_feet(y_mm),
                    "level_name": level_name,
                },
            )

    @mcp.tool()
    async def list_spaces(level_name: str | None = None) -> list[dict[str, Any]]:
        """
        List MEP spaces in the project.

        Args:
            level_name: Optional level name to filter spaces.

        Returns each space's ID, number, name, level, and area (m²).
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if level_name:
                params["level_name"] = level_name
            result = await client.get("/revit/spaces", params=params)
            for space in result:
                if "area" in space:
                    space["area_sqm"] = round(sqft_to_sqm(space.pop("area")), 2)
            return result

    @mcp.tool()
    async def get_room_boundaries(room_id: int) -> list[dict[str, Any]]:
        """
        Get the boundary curves of a room.

        Args:
            room_id: The integer ElementId of the room.

        Returns a list of boundary curve segments with start/end coordinates in mm.
        """
        from revit_client import feet_to_mm
        async with RevitClient() as client:
            result = await client.get(f"/revit/rooms/{room_id}/boundaries")
            # Convert foot coordinates to mm
            def _convert(pt: dict) -> dict:
                return {k: round(feet_to_mm(v), 2) if isinstance(v, (int, float)) else v
                        for k, v in pt.items()}
            for seg in result:
                if "start" in seg:
                    seg["start"] = _convert(seg["start"])
                if "end" in seg:
                    seg["end"] = _convert(seg["end"])
            return result
