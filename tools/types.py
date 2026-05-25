"""
Element type and category tools.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient


def register_tools(mcp: McpServer) -> None:

    @mcp.tool()
    async def list_categories(
        category_type: str = "model",
    ) -> list[dict[str, Any]]:
        """
        List Revit categories.

        Args:
            category_type: 'model', 'annotation', 'analytical', or 'all'. Default: 'model'.

        Returns category names, IDs, and whether they have sub-categories.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/categories", params={"category_type": category_type}
            )

    @mcp.tool()
    async def list_element_types(
        category: str,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List all element types for a given category.

        Args:
            category: The Revit category name, e.g. 'Walls', 'Doors'.
            search: Optional search string to filter type names.

        Returns each type's name, family name, ID, and key type parameters.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {"category": category}
            if search:
                params["search"] = search
            return await client.get("/revit/types", params=params)

    @mcp.tool()
    async def get_type_by_id(type_id: int) -> dict[str, Any]:
        """
        Get detailed information about a specific element type.

        Args:
            type_id: The integer ElementId of the family type.

        Returns the type's family name, type name, category, all type parameters,
        and number of placed instances.
        """
        async with RevitClient() as client:
            return await client.get(f"/revit/types/{type_id}")

    @mcp.tool()
    async def get_type_by_name(
        family_name: str, type_name: str
    ) -> dict[str, Any]:
        """
        Get a type by family name and type name.

        Args:
            family_name: The family name.
            type_name: The type name.

        Returns the type's ElementId and all type parameters.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/types/by_name",
                params={"family_name": family_name, "type_name": type_name},
            )

    @mcp.tool()
    async def duplicate_type(
        source_type_id: int,
        new_type_name: str,
    ) -> dict[str, Any]:
        """
        Duplicate an element type with a new name.

        Args:
            source_type_id: The ElementId of the type to duplicate.
            new_type_name: The name for the new type.

        Returns the new type's ElementId.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/types/duplicate",
                {"source_type_id": source_type_id, "new_type_name": new_type_name},
            )

    @mcp.tool()
    async def rename_type(type_id: int, new_name: str) -> dict[str, Any]:
        """
        Rename a Revit element type.

        Args:
            type_id: The integer ElementId of the type.
            new_name: The new type name.

        Returns confirmation.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/types/rename",
                {"type_id": type_id, "new_name": new_name},
            )

    @mcp.tool()
    async def get_unused_types(category: str) -> list[dict[str, Any]]:
        """
        Find types in a category that have no placed instances.

        Args:
            category: The Revit category name.

        Returns unused type names and IDs. Useful for purging content.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/types/unused", params={"category": category}
            )
