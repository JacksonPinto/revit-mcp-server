"""
Level and grid management tools.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient, feet_to_mm, mm_to_feet


def register_tools(mcp: McpServer) -> None:

    @mcp.tool()
    async def list_levels() -> list[dict[str, Any]]:
        """
        List all levels in the project, sorted by elevation.

        Returns each level's name, ID, elevation (mm above project base point),
        and whether it has an associated floor plan view.
        """
        async with RevitClient() as client:
            result = await client.get("/revit/levels")
            for lvl in result:
                if "elevation" in lvl:
                    lvl["elevation_mm"] = round(feet_to_mm(lvl.pop("elevation")), 2)
            return result

    @mcp.tool()
    async def get_level_by_name(level_name: str) -> dict[str, Any]:
        """
        Get detailed information about a level.

        Args:
            level_name: The level name, e.g. 'Level 1' or 'Ground Floor'.

        Returns the level's ID, name, elevation (mm), and associated views.
        """
        async with RevitClient() as client:
            result = await client.get(
                "/revit/levels/by_name", params={"level_name": level_name}
            )
            if "elevation" in result:
                result["elevation_mm"] = round(feet_to_mm(result.pop("elevation")), 2)
            return result

    @mcp.tool()
    async def create_level(
        elevation_mm: float,
        level_name: str | None = None,
        create_associated_views: bool = True,
    ) -> dict[str, Any]:
        """
        Create a new level at a specified elevation.

        Args:
            elevation_mm: Elevation in mm above the project base point (Z=0).
            level_name: Optional custom name. Auto-names if omitted.
            create_associated_views: If True (default), automatically creates
                                     a floor plan and ceiling plan for this level.

        Returns the new level's ID, name, and elevation.
        """
        async with RevitClient() as client:
            body: dict[str, Any] = {
                "elevation": mm_to_feet(elevation_mm),
                "create_associated_views": create_associated_views,
            }
            if level_name:
                body["level_name"] = level_name
            result = await client.post("/revit/levels/create", body)
            if "elevation" in result:
                result["elevation_mm"] = round(feet_to_mm(result.pop("elevation")), 2)
            return result

    @mcp.tool()
    async def set_level_elevation(
        level_name: str, elevation_mm: float
    ) -> dict[str, Any]:
        """
        Set the elevation of an existing level.

        Args:
            level_name: The level name to modify.
            elevation_mm: New elevation in mm.

        Returns confirmation with old and new elevation values.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/levels/set_elevation",
                {"level_name": level_name, "elevation": mm_to_feet(elevation_mm)},
            )

    @mcp.tool()
    async def rename_level(old_name: str, new_name: str) -> dict[str, Any]:
        """
        Rename a level. Also renames associated views if they match the old name.

        Args:
            old_name: Current level name.
            new_name: New level name.

        Returns confirmation and list of views that were also renamed.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/levels/rename",
                {"old_name": old_name, "new_name": new_name},
            )

    @mcp.tool()
    async def list_grids() -> list[dict[str, Any]]:
        """
        List all grid lines in the project.

        Returns each grid's name, ID, start/end coordinates (mm), and extents.
        """
        async with RevitClient() as client:
            result = await client.get("/revit/grids")
            # Convert grid endpoints from feet to mm
            for grid in result:
                for key in ("start", "end"):
                    if key in grid and isinstance(grid[key], dict):
                        grid[key] = {
                            k: round(feet_to_mm(v), 2)
                            for k, v in grid[key].items()
                            if isinstance(v, (int, float))
                        }
            return result

    @mcp.tool()
    async def create_grid_line(
        start_x_mm: float,
        start_y_mm: float,
        end_x_mm: float,
        end_y_mm: float,
        grid_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new grid line.

        Args:
            start_x_mm: Start X coordinate in mm.
            start_y_mm: Start Y coordinate in mm.
            end_x_mm: End X coordinate in mm.
            end_y_mm: End Y coordinate in mm.
            grid_name: Optional grid label. Auto-increments from last grid if omitted.

        Returns the new grid's ID and name.
        """
        async with RevitClient() as client:
            body: dict[str, Any] = {
                "start_x": mm_to_feet(start_x_mm),
                "start_y": mm_to_feet(start_y_mm),
                "end_x": mm_to_feet(end_x_mm),
                "end_y": mm_to_feet(end_y_mm),
            }
            if grid_name:
                body["grid_name"] = grid_name
            return await client.post("/revit/grids/create", body)
