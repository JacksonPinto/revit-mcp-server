"""
Family and family type tools: listing, loading, placing, and inspecting families.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient, mm_to_feet


def register_tools(mcp: McpServer) -> None:

    @mcp.tool()
    async def list_family_categories() -> list[dict[str, Any]]:
        """
        List all family categories available in the project.

        Returns category names and counts of loaded families per category.
        Useful for exploring what content is available before placing elements.
        """
        async with RevitClient() as client:
            return await client.get("/revit/families/categories")

    @mcp.tool()
    async def list_families(
        category: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List families loaded in the project, optionally filtered by category or name.

        Args:
            category: Optional category name to filter by, e.g. 'Doors', 'Furniture'.
            search: Optional search string to filter family names (case-insensitive).

        Returns each family's name, category, and number of types.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if category:
                params["category"] = category
            if search:
                params["search"] = search
            return await client.get("/revit/families", params=params)

    @mcp.tool()
    async def list_family_types(family_name: str) -> list[dict[str, Any]]:
        """
        List all types (sizes/configurations) of a specific family.

        Args:
            family_name: The exact family name as it appears in the project browser.

        Returns each type's name, ElementId, and key type parameters.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/families/types",
                params={"family_name": family_name},
            )

    @mcp.tool()
    async def get_family_info(family_name: str) -> dict[str, Any]:
        """
        Get detailed information about a loaded family.

        Args:
            family_name: The exact family name.

        Returns the family's category, whether it's a system family, whether it's
        in-place, shared parameter usage, and all type parameters.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/families/info",
                params={"family_name": family_name},
            )

    @mcp.tool()
    async def place_family_instance(
        family_name: str,
        type_name: str,
        x_mm: float,
        y_mm: float,
        z_mm: float = 0.0,
        level_name: str | None = None,
        rotation_degrees: float = 0.0,
        host_element_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Place a family instance at a specific location in the model.

        Args:
            family_name: The family name, e.g. 'Single-Flush'.
            type_name: The type name, e.g. '36" x 84"' or '900 x 2100mm'.
            x_mm: X coordinate in mm.
            y_mm: Y coordinate in mm.
            z_mm: Z coordinate in mm (default 0 — will snap to level).
            level_name: The level name to place the instance on. Uses nearest
                        level if omitted.
            rotation_degrees: Instance rotation angle in degrees. Default: 0.
            host_element_id: Optional host element ID for hosted families (e.g.
                             wall-hosted doors/windows). If provided, x/y/z are
                             relative to the host.

        Returns the new element's ID and placement confirmation.
        """
        async with RevitClient() as client:
            body: dict[str, Any] = {
                "family_name": family_name,
                "type_name": type_name,
                "x": mm_to_feet(x_mm),
                "y": mm_to_feet(y_mm),
                "z": mm_to_feet(z_mm),
                "rotation_degrees": rotation_degrees,
            }
            if level_name:
                body["level_name"] = level_name
            if host_element_id is not None:
                body["host_element_id"] = host_element_id
            return await client.post("/revit/families/place", body)

    @mcp.tool()
    async def load_family(rfa_path: str) -> dict[str, Any]:
        """
        Load a family file (.rfa) into the active Revit project.

        Args:
            rfa_path: Full path to the .rfa family file on the Revit machine.
                      Example: 'C:\\Families\\Custom Door.rfa'

        Returns the loaded family name, category, and number of types.
        """
        async with RevitClient() as client:
            return await client.post("/revit/families/load", {"rfa_path": rfa_path})

    @mcp.tool()
    async def duplicate_family_type(
        family_name: str,
        source_type_name: str,
        new_type_name: str,
    ) -> dict[str, Any]:
        """
        Duplicate an existing family type with a new name.

        Args:
            family_name: The family name.
            source_type_name: The type to duplicate.
            new_type_name: The name for the new duplicate type.

        Returns the new type's ElementId and confirmation.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/families/duplicate_type",
                {
                    "family_name": family_name,
                    "source_type_name": source_type_name,
                    "new_type_name": new_type_name,
                },
            )

    @mcp.tool()
    async def rename_family_type(
        family_name: str,
        old_type_name: str,
        new_type_name: str,
    ) -> dict[str, Any]:
        """
        Rename a family type.

        Args:
            family_name: The family name.
            old_type_name: The current type name.
            new_type_name: The desired new type name.

        Returns confirmation of the rename.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/families/rename_type",
                {
                    "family_name": family_name,
                    "old_type_name": old_type_name,
                    "new_type_name": new_type_name,
                },
            )
