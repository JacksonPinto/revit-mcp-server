"""
MEP (Mechanical, Electrical, Plumbing) tools.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient, feet_to_mm


def register_tools(mcp: McpServer) -> None:

    @mcp.tool()
    async def list_mep_systems(
        system_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List MEP systems in the project.

        Args:
            system_type: Optional filter — 'DuctSystem', 'PipingSystem',
                         'ElectricalSystem', or None for all.

        Returns each system's name, ID, system type, and element count.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if system_type:
                params["system_type"] = system_type
            return await client.get("/revit/mep/systems", params=params)

    @mcp.tool()
    async def list_ducts(
        level_name: str | None = None,
        system_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List duct elements in the project.

        Args:
            level_name: Optional level name filter.
            system_name: Optional MEP system name filter.

        Returns each duct's ID, size (width x height mm or diameter mm),
        length (mm), level, and system.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if level_name:
                params["level_name"] = level_name
            if system_name:
                params["system_name"] = system_name
            result = await client.get("/revit/mep/ducts", params=params)
            for duct in result:
                for key in ("width", "height", "diameter", "length"):
                    if key in duct and isinstance(duct[key], (int, float)):
                        duct[f"{key}_mm"] = round(feet_to_mm(duct.pop(key)), 2)
            return result

    @mcp.tool()
    async def list_pipes(
        level_name: str | None = None,
        system_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List pipe elements in the project.

        Args:
            level_name: Optional level name filter.
            system_name: Optional MEP system name filter.

        Returns each pipe's ID, outer diameter (mm), length (mm), level, and system.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if level_name:
                params["level_name"] = level_name
            if system_name:
                params["system_name"] = system_name
            result = await client.get("/revit/mep/pipes", params=params)
            for pipe in result:
                for key in ("diameter", "outer_diameter", "length"):
                    if key in pipe and isinstance(pipe[key], (int, float)):
                        pipe[f"{key}_mm"] = round(feet_to_mm(pipe.pop(key)), 2)
            return result

    @mcp.tool()
    async def list_electrical_circuits() -> list[dict[str, Any]]:
        """
        List all electrical circuits in the project.

        Returns each circuit's name, ID, load name, amperage, voltage, panel name,
        and connected elements.
        """
        async with RevitClient() as client:
            return await client.get("/revit/mep/circuits")

    @mcp.tool()
    async def get_mep_system_info(system_name: str) -> dict[str, Any]:
        """
        Get detailed information about an MEP system.

        Args:
            system_name: The MEP system name.

        Returns the system type, flow, pressure drop, connected elements,
        and a list of element IDs in the system.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/mep/systems/info", params={"system_name": system_name}
            )

    @mcp.tool()
    async def list_mechanical_equipment(
        level_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List mechanical equipment (AHUs, FCUs, VAVs, etc.) in the project.

        Args:
            level_name: Optional level name filter.

        Returns each equipment item's ID, family/type name, level, and system.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if level_name:
                params["level_name"] = level_name
            return await client.get("/revit/mep/mechanical_equipment", params=params)

    @mcp.tool()
    async def list_light_fixtures(
        level_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List light fixtures in the project.

        Args:
            level_name: Optional level name filter.

        Returns each fixture's ID, family/type, level, circuit, and location (mm).
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if level_name:
                params["level_name"] = level_name
            return await client.get("/revit/mep/light_fixtures", params=params)

    @mcp.tool()
    async def list_plumbing_fixtures(
        level_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List plumbing fixtures (sinks, toilets, showers, etc.) in the project.

        Args:
            level_name: Optional level name filter.

        Returns each fixture's ID, family/type, level, and system connections.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if level_name:
                params["level_name"] = level_name
            return await client.get("/revit/mep/plumbing_fixtures", params=params)
