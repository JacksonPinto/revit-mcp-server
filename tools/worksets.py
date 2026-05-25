"""
Workset management tools for Revit workshared models.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient


def register_tools(mcp: McpServer) -> None:

    @mcp.tool()
    async def list_worksets() -> list[dict[str, Any]]:
        """
        List all user-defined worksets in the project.

        Returns each workset's name, ID, owner (if checked out), and whether
        it is currently visible in the active view.

        Note: Only available in workshared (collaboration) models.
        """
        async with RevitClient() as client:
            return await client.get("/revit/worksets")

    @mcp.tool()
    async def create_workset(name: str) -> dict[str, Any]:
        """
        Create a new workset in the project.

        Args:
            name: The name of the new workset (must be unique).

        Returns the new workset's ID and confirmation.
        """
        async with RevitClient() as client:
            return await client.post("/revit/worksets/create", {"name": name})

    @mcp.tool()
    async def get_element_workset(element_id: int) -> dict[str, Any]:
        """
        Get the workset that an element belongs to.

        Args:
            element_id: The integer Revit ElementId.

        Returns the workset name and ID.
        """
        async with RevitClient() as client:
            return await client.get(f"/revit/elements/{element_id}/workset")

    @mcp.tool()
    async def set_element_workset(
        element_ids: list[int], workset_name: str
    ) -> dict[str, Any]:
        """
        Move one or more elements to a specified workset.

        Args:
            element_ids: List of integer ElementIds to reassign.
            workset_name: The target workset name.

        Returns count of elements moved and any that could not be moved
        (e.g. system elements or elements owned by another user).
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/worksets/set_elements",
                {"element_ids": element_ids, "workset_name": workset_name},
            )

    @mcp.tool()
    async def set_active_workset(workset_name: str) -> dict[str, Any]:
        """
        Set the active workset. New elements will be placed on this workset.

        Args:
            workset_name: The name of the workset to make active.

        Returns confirmation with the previous and new active workset names.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/worksets/set_active", {"workset_name": workset_name}
            )

    @mcp.tool()
    async def get_workset_elements(workset_name: str) -> list[dict[str, Any]]:
        """
        List all elements that belong to a specific workset.

        Args:
            workset_name: The workset name.

        Returns element IDs, categories, and type names for all elements
        on the workset.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/worksets/elements", params={"workset_name": workset_name}
            )

    @mcp.tool()
    async def rename_workset(old_name: str, new_name: str) -> dict[str, Any]:
        """
        Rename a workset.

        Args:
            old_name: The current workset name.
            new_name: The new workset name (must be unique).

        Returns confirmation.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/worksets/rename",
                {"old_name": old_name, "new_name": new_name},
            )

    @mcp.tool()
    async def is_workshared() -> dict[str, Any]:
        """
        Check if the active Revit model is workshared (uses worksets).

        Returns {'workshared': True/False} and if workshared, also returns
        the central model path and current user checkout status.
        """
        async with RevitClient() as client:
            return await client.get("/revit/worksets/status")
