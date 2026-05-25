"""
View creation and management tools.
Covers floor plans, ceiling plans, sections, elevations, 3D views, schedules,
view templates, and view properties.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient


def register_tools(mcp: McpServer) -> None:

    @mcp.tool()
    async def list_views(
        view_type: str | None = None,
        search: str | None = None,
        exclude_template_views: bool = True,
    ) -> list[dict[str, Any]]:
        """
        List views in the active Revit project.

        Args:
            view_type: Optional filter by view type: 'FloorPlan', 'CeilingPlan',
                       'Section', 'Elevation', 'ThreeD', 'DraftingView',
                       'Schedule', 'Legend', 'AreaPlan', 'Rendering'.
            search: Optional search string to filter view names.
            exclude_template_views: Exclude view templates from results. Default: True.

        Returns list of views with ID, name, type, scale, level, and sheet placement.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {"exclude_template_views": exclude_template_views}
            if view_type:
                params["view_type"] = view_type
            if search:
                params["search"] = search
            return await client.get("/revit/views", params=params)

    @mcp.tool()
    async def get_view_by_name(view_name: str) -> dict[str, Any]:
        """
        Get detailed information about a view by name.

        Args:
            view_name: The exact view name.

        Returns the view's ID, type, scale, discipline, detail level,
        view template, associated level, and crop region.
        """
        async with RevitClient() as client:
            return await client.get("/revit/views/by_name", params={"view_name": view_name})

    @mcp.tool()
    async def create_floor_plan(
        level_name: str,
        view_name: str | None = None,
        view_family_type: str | None = None,
        scope_box_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new floor plan view for a level.

        Args:
            level_name: The name of the level to create the plan for.
            view_name: Optional custom name. Defaults to level name + ' - Floor Plan'.
            view_family_type: Optional view family type name. Uses the first available
                              floor plan type if omitted.
            scope_box_name: Optional scope box name to apply to the new view.

        Returns the new view's ID and name.
        """
        async with RevitClient() as client:
            body: dict[str, Any] = {"level_name": level_name}
            if view_name:
                body["view_name"] = view_name
            if view_family_type:
                body["view_family_type"] = view_family_type
            if scope_box_name:
                body["scope_box_name"] = scope_box_name
            return await client.post("/revit/views/create/floor_plan", body)

    @mcp.tool()
    async def create_ceiling_plan(
        level_name: str,
        view_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new reflected ceiling plan (RCP) view for a level.

        Args:
            level_name: The name of the level to create the RCP for.
            view_name: Optional custom name.

        Returns the new view's ID and name.
        """
        async with RevitClient() as client:
            body: dict[str, Any] = {"level_name": level_name}
            if view_name:
                body["view_name"] = view_name
            return await client.post("/revit/views/create/ceiling_plan", body)

    @mcp.tool()
    async def create_section_view(
        start_x_mm: float,
        start_y_mm: float,
        end_x_mm: float,
        end_y_mm: float,
        level_name: str,
        view_name: str | None = None,
        depth_mm: float = 5000.0,
        height_mm: float | None = None,
    ) -> dict[str, Any]:
        """
        Create a building section view.

        Args:
            start_x_mm: Section line start X in mm.
            start_y_mm: Section line start Y in mm.
            end_x_mm: Section line end X in mm.
            end_y_mm: Section line end Y in mm.
            level_name: Reference level for the section cut height.
            view_name: Optional custom name for the section view.
            depth_mm: Far clip offset behind the section line in mm. Default: 5000.
            height_mm: View height in mm. Defaults to floor-to-floor height.

        Returns the new view's ID and name.
        """
        from revit_client import mm_to_feet
        async with RevitClient() as client:
            body: dict[str, Any] = {
                "start_x": mm_to_feet(start_x_mm),
                "start_y": mm_to_feet(start_y_mm),
                "end_x": mm_to_feet(end_x_mm),
                "end_y": mm_to_feet(end_y_mm),
                "level_name": level_name,
                "depth": mm_to_feet(depth_mm),
            }
            if view_name:
                body["view_name"] = view_name
            if height_mm is not None:
                body["height"] = mm_to_feet(height_mm)
            return await client.post("/revit/views/create/section", body)

    @mcp.tool()
    async def create_elevation_view(
        element_id: int | None = None,
        direction: str = "north",
        level_name: str | None = None,
        view_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Create an elevation view.

        Args:
            element_id: Optional element ID to generate an interior elevation around.
                        If omitted, creates a building elevation.
            direction: Elevation direction for building elevations:
                       'north', 'south', 'east', 'west'. Default: 'north'.
            level_name: Associated level name.
            view_name: Optional custom name.

        Returns the new view's ID and name.
        """
        async with RevitClient() as client:
            body: dict[str, Any] = {"direction": direction}
            if element_id is not None:
                body["element_id"] = element_id
            if level_name:
                body["level_name"] = level_name
            if view_name:
                body["view_name"] = view_name
            return await client.post("/revit/views/create/elevation", body)

    @mcp.tool()
    async def create_3d_view(
        view_name: str | None = None,
        is_perspective: bool = False,
        view_template_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new 3D (orthographic or perspective) view.

        Args:
            view_name: Optional custom name.
            is_perspective: If True, creates a perspective (camera) view.
            view_template_name: Optional view template to apply.

        Returns the new view's ID and name.
        """
        async with RevitClient() as client:
            body: dict[str, Any] = {"is_perspective": is_perspective}
            if view_name:
                body["view_name"] = view_name
            if view_template_name:
                body["view_template_name"] = view_template_name
            return await client.post("/revit/views/create/3d", body)

    @mcp.tool()
    async def duplicate_view(
        source_view_name: str,
        new_view_name: str,
        duplicate_with_detailing: bool = False,
    ) -> dict[str, Any]:
        """
        Duplicate an existing view.

        Args:
            source_view_name: The name of the view to duplicate.
            new_view_name: The name for the new duplicate view.
            duplicate_with_detailing: If True, also copy annotation and detail
                                      elements. Default: False.

        Returns the new view's ID.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/views/duplicate",
                {
                    "source_view_name": source_view_name,
                    "new_view_name": new_view_name,
                    "with_detailing": duplicate_with_detailing,
                },
            )

    @mcp.tool()
    async def list_view_templates() -> list[dict[str, Any]]:
        """
        List all view templates in the project.

        Returns each template's name, ID, view type, and the disciplines it applies to.
        """
        async with RevitClient() as client:
            return await client.get("/revit/views/templates")

    @mcp.tool()
    async def apply_view_template(
        view_name: str, template_name: str
    ) -> dict[str, Any]:
        """
        Apply a view template to a view.

        Args:
            view_name: The target view name.
            template_name: The view template name to apply.

        Returns confirmation with previous and new template names.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/views/apply_template",
                {"view_name": view_name, "template_name": template_name},
            )

    @mcp.tool()
    async def set_view_scale(view_name: str, scale_denominator: int) -> dict[str, Any]:
        """
        Set the display scale of a view.

        Args:
            view_name: The view name.
            scale_denominator: The denominator of the scale ratio.
                               E.g. 100 for 1:100, 50 for 1:50, 20 for 1:20.

        Returns confirmation with old and new scale.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/views/set_scale",
                {"view_name": view_name, "scale_denominator": scale_denominator},
            )

    @mcp.tool()
    async def set_view_detail_level(
        view_name: str, detail_level: str
    ) -> dict[str, Any]:
        """
        Set the detail level of a view.

        Args:
            view_name: The view name.
            detail_level: One of 'Coarse', 'Medium', or 'Fine'.

        Returns confirmation with old and new detail level.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/views/set_detail_level",
                {"view_name": view_name, "detail_level": detail_level},
            )

    @mcp.tool()
    async def rename_view(old_name: str, new_name: str) -> dict[str, Any]:
        """
        Rename a view.

        Args:
            old_name: Current view name.
            new_name: New view name.

        Returns confirmation.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/views/rename",
                {"old_name": old_name, "new_name": new_name},
            )

    @mcp.tool()
    async def delete_view(view_name: str) -> dict[str, Any]:
        """
        Delete a view from the project.

        Args:
            view_name: The name of the view to delete.

        WARNING: This cannot be undone via the MCP server. Deleting a view
        placed on a sheet will also remove the viewport from the sheet.
        """
        async with RevitClient() as client:
            return await client.delete("/revit/views", {"view_name": view_name})
