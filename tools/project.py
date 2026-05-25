"""
Project and document information tools.
Covers project metadata, warnings, linked models, and document statistics.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient, get_revit_client


def register_tools(mcp: McpServer) -> None:

    @mcp.tool()
    async def get_project_info() -> dict[str, Any]:
        """
        Get general information about the active Revit project.

        Returns project name, number, client name, building type, address,
        issue date, status, author, file path, and Revit version.
        """
        async with RevitClient() as client:
            return await client.get("/revit/project/info")

    @mcp.tool()
    async def get_document_stats() -> dict[str, Any]:
        """
        Get statistics about the active Revit document.

        Returns element counts by category, family count, view count,
        sheet count, level count, and file size.
        """
        async with RevitClient() as client:
            return await client.get("/revit/project/stats")

    @mcp.tool()
    async def list_linked_models() -> list[dict[str, Any]]:
        """
        List all Revit link instances in the active model.

        Returns each linked model's name, path, status (loaded/unloaded),
        and instance element ID.
        """
        async with RevitClient() as client:
            return await client.get("/revit/project/links")

    @mcp.tool()
    async def get_model_warnings() -> list[dict[str, Any]]:
        """
        Get all warnings in the active Revit model.

        Returns each warning's description, severity, and the element IDs
        involved. Useful for model health audits.
        """
        async with RevitClient() as client:
            return await client.get("/revit/project/warnings")

    @mcp.tool()
    async def ping_revit() -> dict[str, Any]:
        """
        Test the connection to the Revit pyRevit Routes API.

        Returns server status, Revit version, pyRevit version, and
        whether a document is currently open.
        """
        async with RevitClient() as client:
            return await client.ping()

    @mcp.tool()
    async def get_revit_version() -> dict[str, Any]:
        """
        Get the Revit application version and build number.

        Returns version year, sub-version, build number, and language.
        """
        async with RevitClient() as client:
            return await client.get("/revit/application/version")

    @mcp.tool()
    async def list_open_documents() -> list[dict[str, Any]]:
        """
        List all documents currently open in Revit (including family documents).

        Returns each document's title, path, and whether it is the active document.
        """
        async with RevitClient() as client:
            return await client.get("/revit/application/documents")

    @mcp.tool()
    async def get_project_units() -> dict[str, Any]:
        """
        Get the unit settings for the active Revit project.

        Returns the project's display units for length, area, volume,
        angle, slope, and currency.
        """
        async with RevitClient() as client:
            return await client.get("/revit/project/units")

    @mcp.tool()
    async def set_project_parameter(param_name: str, value: str) -> dict[str, Any]:
        """
        Set a project information parameter (e.g. 'Project Name', 'Project Number').

        Args:
            param_name: The name of the project information parameter to set.
            value: The new string value.

        Returns confirmation with the old and new values.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/project/info/set",
                {"param_name": param_name, "value": value},
            )
