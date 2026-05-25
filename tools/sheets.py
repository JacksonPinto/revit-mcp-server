"""
Sheet management tools: creating, numbering, placing views, and exporting sheets.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient


def register_tools(mcp: McpServer) -> None:

    @mcp.tool()
    async def list_sheets(
        search: str | None = None,
        discipline: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List all sheets in the project.

        Args:
            search: Optional search string for sheet number or name.
            discipline: Optional discipline filter (e.g. 'Architectural', 'Structural',
                        'Mechanical', 'Electrical', 'Plumbing').

        Returns each sheet's number, name, ID, views placed on it, and revision.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if search:
                params["search"] = search
            if discipline:
                params["discipline"] = discipline
            return await client.get("/revit/sheets", params=params)

    @mcp.tool()
    async def get_sheet_by_number(sheet_number: str) -> dict[str, Any]:
        """
        Get detailed information about a sheet by its number.

        Args:
            sheet_number: The sheet number, e.g. 'A-101' or '001'.

        Returns the sheet's name, ID, titleblock family, revision, views placed
        on it with their viewport IDs, and all sheet parameters.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/sheets/by_number", params={"sheet_number": sheet_number}
            )

    @mcp.tool()
    async def create_sheet(
        sheet_number: str,
        sheet_name: str,
        titleblock_family: str | None = None,
        titleblock_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new sheet in the project.

        Args:
            sheet_number: The sheet number (must be unique), e.g. 'A-102'.
            sheet_name: The sheet name, e.g. 'GROUND FLOOR PLAN'.
            titleblock_family: Optional titleblock family name. Uses the project
                               default if omitted.
            titleblock_type: Optional titleblock type/size, e.g. 'A1' or '24x36'.

        Returns the new sheet's ElementId and confirmation.
        """
        async with RevitClient() as client:
            body: dict[str, Any] = {
                "sheet_number": sheet_number,
                "sheet_name": sheet_name,
            }
            if titleblock_family:
                body["titleblock_family"] = titleblock_family
            if titleblock_type:
                body["titleblock_type"] = titleblock_type
            return await client.post("/revit/sheets/create", body)

    @mcp.tool()
    async def create_sheets_bulk(
        sheets: list[dict[str, str]],
        titleblock_family: str | None = None,
    ) -> dict[str, Any]:
        """
        Create multiple sheets in a single operation.

        Args:
            sheets: List of dicts, each with 'sheet_number' and 'sheet_name'.
                    Example: [{"sheet_number": "A-101", "sheet_name": "LEVEL 1 PLAN"},
                               {"sheet_number": "A-102", "sheet_name": "LEVEL 2 PLAN"}]
            titleblock_family: Optional titleblock family to use for all sheets.

        Returns count of sheets created and any failures (duplicate numbers etc).
        """
        async with RevitClient() as client:
            body: dict[str, Any] = {"sheets": sheets}
            if titleblock_family:
                body["titleblock_family"] = titleblock_family
            return await client.post("/revit/sheets/create_bulk", body)

    @mcp.tool()
    async def place_view_on_sheet(
        view_name: str,
        sheet_number: str,
        x_mm: float | None = None,
        y_mm: float | None = None,
        auto_center: bool = False,
    ) -> dict[str, Any]:
        """
        Place a view onto a sheet as a viewport.

        Args:
            view_name: The name of the view to place.
            sheet_number: The sheet number to place the view on.
            x_mm: X position on the sheet in mm from sheet origin. Optional if
                  auto_center is True.
            y_mm: Y position on the sheet in mm from sheet origin. Optional if
                  auto_center is True.
            auto_center: If True, automatically center the view on the sheet.
                         Overrides x_mm/y_mm. Default: False.

        Returns the new viewport's ElementId and position.
        """
        from revit_client import mm_to_feet
        async with RevitClient() as client:
            body: dict[str, Any] = {
                "view_name": view_name,
                "sheet_number": sheet_number,
                "auto_center": auto_center,
            }
            if x_mm is not None:
                body["x"] = mm_to_feet(x_mm)
            if y_mm is not None:
                body["y"] = mm_to_feet(y_mm)
            return await client.post("/revit/sheets/place_view", body)

    @mcp.tool()
    async def list_views_on_sheet(sheet_number: str) -> list[dict[str, Any]]:
        """
        List all views (viewports) placed on a sheet.

        Args:
            sheet_number: The sheet number.

        Returns each viewport's view name, view type, viewport ID, and position.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/sheets/views", params={"sheet_number": sheet_number}
            )

    @mcp.tool()
    async def remove_view_from_sheet(
        view_name: str, sheet_number: str
    ) -> dict[str, Any]:
        """
        Remove a viewport from a sheet (does not delete the view itself).

        Args:
            view_name: The view name to remove.
            sheet_number: The sheet number to remove it from.

        Returns confirmation.
        """
        async with RevitClient() as client:
            return await client.delete(
                "/revit/sheets/remove_view",
                {"view_name": view_name, "sheet_number": sheet_number},
            )

    @mcp.tool()
    async def set_sheet_parameter(
        sheet_number: str, param_name: str, value: str
    ) -> dict[str, Any]:
        """
        Set a parameter on a sheet (e.g. title block parameters).

        Args:
            sheet_number: The sheet number.
            param_name: The parameter name, e.g. 'Drawn By', 'Checked By',
                        'Approved By', 'Current Revision'.
            value: The new value.

        Returns confirmation with old and new values.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/sheets/set_parameter",
                {"sheet_number": sheet_number, "param_name": param_name, "value": value},
            )

    @mcp.tool()
    async def renumber_sheet(old_number: str, new_number: str) -> dict[str, Any]:
        """
        Change a sheet's number.

        Args:
            old_number: The current sheet number.
            new_number: The desired new sheet number (must not already exist).

        Returns confirmation.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/sheets/renumber",
                {"old_number": old_number, "new_number": new_number},
            )

    @mcp.tool()
    async def list_titleblock_families() -> list[dict[str, Any]]:
        """
        List all titleblock families loaded in the project.

        Returns each titleblock's family name and available types (sizes).
        """
        async with RevitClient() as client:
            return await client.get("/revit/sheets/titleblocks")

    @mcp.tool()
    async def get_sheet_issue_history(sheet_number: str) -> list[dict[str, Any]]:
        """
        Get the revision/issue history of a sheet.

        Args:
            sheet_number: The sheet number.

        Returns a list of revisions with sequence number, date, description,
        issued by, and issued to.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/sheets/revisions", params={"sheet_number": sheet_number}
            )
