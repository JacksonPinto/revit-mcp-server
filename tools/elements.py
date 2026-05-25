"""
Element query, creation, modification, and deletion tools.
The most comprehensive tool module — covers CRUD + transforms for all Revit elements.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient, mm_to_feet


def register_tools(mcp: McpServer) -> None:

    # ------------------------------------------------------------------
    # Query tools
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_element_by_id(element_id: int) -> dict[str, Any]:
        """
        Get detailed information about a Revit element by its ElementId.

        Args:
            element_id: The integer Revit ElementId.

        Returns element category, family, type, level, location, and all
        visible parameters.
        """
        async with RevitClient() as client:
            return await client.get(f"/revit/elements/{element_id}")

    @mcp.tool()
    async def get_elements_by_category(
        category: str,
        level_name: str | None = None,
        include_type_elements: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Get all elements belonging to a Revit built-in category.

        Args:
            category: The Revit category name, e.g. 'Walls', 'Doors', 'Windows',
                      'Structural Columns', 'Mechanical Equipment'.
            level_name: Optional — filter results to a specific level name.
            include_type_elements: If True, also return type elements (default False).

        Returns a list of element summaries with ID, type, and key parameters.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {
                "category": category,
                "include_type_elements": include_type_elements,
            }
            if level_name:
                params["level_name"] = level_name
            return await client.get("/revit/elements/by_category", params=params)

    @mcp.tool()
    async def get_elements_by_type(type_id: int) -> list[dict[str, Any]]:
        """
        Get all instances of a specific element type.

        Args:
            type_id: The integer ElementId of the family type.

        Returns all instances with their IDs and placement information.
        """
        async with RevitClient() as client:
            return await client.get(f"/revit/elements/by_type/{type_id}")

    @mcp.tool()
    async def find_elements_by_parameter(
        category: str,
        param_name: str,
        param_value: str,
        operator: str = "equals",
    ) -> list[dict[str, Any]]:
        """
        Find elements where a parameter matches a given value.

        Args:
            category: Revit category name to search within, e.g. 'Walls'.
            param_name: Parameter name to filter on, e.g. 'Mark', 'Comments'.
            param_value: Value to search for.
            operator: Comparison operator: 'equals', 'contains', 'starts_with',
                      'ends_with', 'greater_than', 'less_than'. Default: 'equals'.

        Returns matching elements with their IDs and parameter values.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/elements/find_by_parameter",
                {
                    "category": category,
                    "param_name": param_name,
                    "param_value": param_value,
                    "operator": operator,
                },
            )

    @mcp.tool()
    async def get_selected_elements() -> list[dict[str, Any]]:
        """
        Get the elements currently selected in the Revit UI.

        Returns the IDs, categories, and key parameters of all selected elements.
        """
        async with RevitClient() as client:
            return await client.get("/revit/selection")

    @mcp.tool()
    async def select_elements(element_ids: list[int]) -> dict[str, Any]:
        """
        Programmatically select elements in the Revit UI.

        Args:
            element_ids: List of integer ElementIds to select.

        Returns confirmation of how many elements were selected.
        """
        async with RevitClient() as client:
            return await client.post("/revit/selection", {"element_ids": element_ids})

    @mcp.tool()
    async def count_elements_by_category(category: str) -> dict[str, Any]:
        """
        Count elements in a category without fetching all element data.

        Args:
            category: Revit category name, e.g. 'Walls'.

        Returns the total instance count and type count.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/elements/count", params={"category": category}
            )

    # ------------------------------------------------------------------
    # Modification tools
    # ------------------------------------------------------------------

    @mcp.tool()
    async def delete_elements(element_ids: list[int]) -> dict[str, Any]:
        """
        Delete one or more elements from the Revit model.

        Args:
            element_ids: List of integer ElementIds to delete.

        Returns count of deleted elements and any elements that could not
        be deleted (e.g. pinned or read-only elements).

        WARNING: This operation cannot be undone via the MCP server.
        """
        async with RevitClient() as client:
            return await client.delete("/revit/elements", {"element_ids": element_ids})

    @mcp.tool()
    async def move_elements(
        element_ids: list[int],
        delta_x_mm: float,
        delta_y_mm: float,
        delta_z_mm: float = 0.0,
    ) -> dict[str, Any]:
        """
        Move elements by a translation vector (in millimetres).

        Args:
            element_ids: List of integer ElementIds to move.
            delta_x_mm: Translation along the X axis in mm.
            delta_y_mm: Translation along the Y axis in mm.
            delta_z_mm: Translation along the Z axis in mm (default 0).

        Returns count of successfully moved elements.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/elements/move",
                {
                    "element_ids": element_ids,
                    "delta_x": mm_to_feet(delta_x_mm),
                    "delta_y": mm_to_feet(delta_y_mm),
                    "delta_z": mm_to_feet(delta_z_mm),
                },
            )

    @mcp.tool()
    async def rotate_elements(
        element_ids: list[int],
        angle_degrees: float,
        axis: str = "z",
        origin_x_mm: float = 0.0,
        origin_y_mm: float = 0.0,
        origin_z_mm: float = 0.0,
    ) -> dict[str, Any]:
        """
        Rotate elements around a point and axis.

        Args:
            element_ids: List of integer ElementIds to rotate.
            angle_degrees: Rotation angle in degrees (positive = counter-clockwise).
            axis: Rotation axis — 'x', 'y', or 'z'. Default: 'z'.
            origin_x_mm: X coordinate of rotation origin in mm. Default: 0.
            origin_y_mm: Y coordinate of rotation origin in mm. Default: 0.
            origin_z_mm: Z coordinate of rotation origin in mm. Default: 0.

        Returns count of successfully rotated elements.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/elements/rotate",
                {
                    "element_ids": element_ids,
                    "angle_degrees": angle_degrees,
                    "axis": axis,
                    "origin_x": mm_to_feet(origin_x_mm),
                    "origin_y": mm_to_feet(origin_y_mm),
                    "origin_z": mm_to_feet(origin_z_mm),
                },
            )

    @mcp.tool()
    async def copy_elements(
        element_ids: list[int],
        delta_x_mm: float,
        delta_y_mm: float,
        delta_z_mm: float = 0.0,
    ) -> dict[str, Any]:
        """
        Copy elements with a translation offset (in millimetres).

        Args:
            element_ids: List of integer ElementIds to copy.
            delta_x_mm: Copy offset along X axis in mm.
            delta_y_mm: Copy offset along Y axis in mm.
            delta_z_mm: Copy offset along Z axis in mm. Default: 0.

        Returns IDs of the newly created copy elements.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/elements/copy",
                {
                    "element_ids": element_ids,
                    "delta_x": mm_to_feet(delta_x_mm),
                    "delta_y": mm_to_feet(delta_y_mm),
                    "delta_z": mm_to_feet(delta_z_mm),
                },
            )

    @mcp.tool()
    async def mirror_elements(
        element_ids: list[int],
        mirror_plane: str,
        create_copies: bool = True,
    ) -> dict[str, Any]:
        """
        Mirror elements about a plane.

        Args:
            element_ids: List of integer ElementIds to mirror.
            mirror_plane: Plane descriptor — 'xz', 'yz', 'xy', or an element ID
                          of a reference plane/grid/wall to use as the mirror axis.
            create_copies: If True (default), keep originals and create mirrored copies.
                           If False, mirror the elements in place.

        Returns IDs of mirrored (or newly created) elements.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/elements/mirror",
                {
                    "element_ids": element_ids,
                    "mirror_plane": mirror_plane,
                    "create_copies": create_copies,
                },
            )

    @mcp.tool()
    async def get_element_location(element_id: int) -> dict[str, Any]:
        """
        Get the spatial location of an element in mm coordinates.

        Args:
            element_id: The integer Revit ElementId.

        Returns:
          - For point-based elements (columns, furniture): x, y, z in mm and rotation angle.
          - For curve-based elements (walls, beams): start/end points in mm and length in mm.
          - For area-based elements: bounding box corners in mm.
        """
        async with RevitClient() as client:
            result = await client.get(f"/revit/elements/{element_id}/location")
            # Convert feet to mm in the response
            return _convert_location_to_mm(result)

    @mcp.tool()
    async def pin_elements(element_ids: list[int], pinned: bool = True) -> dict[str, Any]:
        """
        Pin or unpin elements to prevent accidental modification.

        Args:
            element_ids: List of integer ElementIds.
            pinned: True to pin (default), False to unpin.

        Returns count of elements whose pin state was changed.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/elements/pin",
                {"element_ids": element_ids, "pinned": pinned},
            )

    @mcp.tool()
    async def change_element_type(
        element_ids: list[int], new_type_id: int
    ) -> dict[str, Any]:
        """
        Change the type of one or more elements.

        Args:
            element_ids: List of instance ElementIds to retype.
            new_type_id: ElementId of the new family type.

        Returns count of successfully retyped elements.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/elements/change_type",
                {"element_ids": element_ids, "new_type_id": new_type_id},
            )

    @mcp.tool()
    async def get_element_dependencies(element_id: int) -> dict[str, Any]:
        """
        Get the dependent elements of a given element.

        Returns hosted elements, joined elements, and other dependent elements
        that would be affected if this element were deleted or modified.

        Args:
            element_id: The integer Revit ElementId.
        """
        async with RevitClient() as client:
            return await client.get(f"/revit/elements/{element_id}/dependencies")


def _convert_location_to_mm(location: dict[str, Any]) -> dict[str, Any]:
    """Recursively convert any feet values to mm in a location dict."""
    from revit_client import feet_to_mm

    def _walk(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _walk(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_walk(i) for i in obj]
        if isinstance(obj, float):
            # Heuristic: if value is less than ~1000 ft it's probably a coordinate
            return round(feet_to_mm(obj), 2)
        return obj

    return _walk(location)
