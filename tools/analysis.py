"""
Geometry and analysis tools.
Covers areas, volumes, bounding boxes, clash detection, and model summaries.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient, cbft_to_cbm, feet_to_mm, sqft_to_sqm


def register_tools(mcp: McpServer) -> None:

    @mcp.tool()
    async def get_element_bounding_box(element_id: int) -> dict[str, Any]:
        """
        Get the axis-aligned bounding box of an element.

        Args:
            element_id: The integer Revit ElementId.

        Returns min/max XYZ corners in mm and the bounding box dimensions (mm).
        """
        async with RevitClient() as client:
            result = await client.get(f"/revit/elements/{element_id}/bounding_box")
            return _convert_bbox_to_mm(result)

    @mcp.tool()
    async def get_model_extents() -> dict[str, Any]:
        """
        Get the bounding box extents of the entire model.

        Returns min/max XYZ in mm and overall dimensions (width, depth, height) in mm.
        Useful for understanding model scale before placing elements.
        """
        async with RevitClient() as client:
            result = await client.get("/revit/model/extents")
            return _convert_bbox_to_mm(result)

    @mcp.tool()
    async def calculate_room_areas_by_level(
        level_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Calculate total room areas grouped by level (or for a specific level).

        Args:
            level_name: Optional level name. If omitted, returns all levels.

        Returns each level's name, total room area (m²), total room count,
        and average room area (m²).
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if level_name:
                params["level_name"] = level_name
            result = await client.get("/revit/analysis/room_areas", params=params)
            for row in result:
                if "total_area" in row:
                    row["total_area_sqm"] = round(sqft_to_sqm(row.pop("total_area")), 2)
                if "avg_area" in row:
                    row["avg_area_sqm"] = round(sqft_to_sqm(row.pop("avg_area")), 2)
            return result

    @mcp.tool()
    async def calculate_floor_area_by_category(
        category: str = "Floors",
        level_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Calculate the total area of elements in a category.

        Args:
            category: Revit category name, e.g. 'Floors', 'Ceilings', 'Roofs'.
                      Default: 'Floors'.
            level_name: Optional level name filter.

        Returns total area in m², count of elements, and a breakdown by type name.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {"category": category}
            if level_name:
                params["level_name"] = level_name
            result = await client.get("/revit/analysis/area_by_category", params=params)
            if "total_area" in result:
                result["total_area_sqm"] = round(sqft_to_sqm(result.pop("total_area")), 2)
            if "breakdown" in result:
                for item in result["breakdown"]:
                    if "area" in item:
                        item["area_sqm"] = round(sqft_to_sqm(item.pop("area")), 2)
            return result

    @mcp.tool()
    async def calculate_wall_areas(
        level_name: str | None = None,
        wall_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Calculate total wall face areas, useful for finishes takeoffs.

        Args:
            level_name: Optional level name filter.
            wall_type: Optional wall type name filter.

        Returns total wall area (m²), net area excluding openings (m²),
        opening area (m²), and a breakdown by wall type.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if level_name:
                params["level_name"] = level_name
            if wall_type:
                params["wall_type"] = wall_type
            result = await client.get("/revit/analysis/wall_areas", params=params)
            for key in ("total_area", "net_area", "opening_area"):
                if key in result:
                    result[f"{key}_sqm"] = round(sqft_to_sqm(result.pop(key)), 2)
            return result

    @mcp.tool()
    async def get_element_volume(element_id: int) -> dict[str, Any]:
        """
        Calculate the volume of an element.

        Args:
            element_id: The integer Revit ElementId.

        Returns volume in m³ and the element's category and type.
        """
        async with RevitClient() as client:
            result = await client.get(f"/revit/elements/{element_id}/volume")
            if "volume" in result:
                result["volume_cbm"] = round(cbft_to_cbm(result.pop("volume")), 4)
            return result

    @mcp.tool()
    async def find_elements_in_bounding_box(
        min_x_mm: float,
        min_y_mm: float,
        min_z_mm: float,
        max_x_mm: float,
        max_y_mm: float,
        max_z_mm: float,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find all elements whose bounding boxes intersect a specified 3D region.

        Args:
            min_x_mm: Minimum X in mm.
            min_y_mm: Minimum Y in mm.
            min_z_mm: Minimum Z in mm.
            max_x_mm: Maximum X in mm.
            max_y_mm: Maximum Y in mm.
            max_z_mm: Maximum Z in mm.
            category: Optional category filter, e.g. 'Structural Columns'.

        Returns matching element IDs and categories.
        """
        from revit_client import mm_to_feet
        async with RevitClient() as client:
            body: dict[str, Any] = {
                "min_x": mm_to_feet(min_x_mm),
                "min_y": mm_to_feet(min_y_mm),
                "min_z": mm_to_feet(min_z_mm),
                "max_x": mm_to_feet(max_x_mm),
                "max_y": mm_to_feet(max_y_mm),
                "max_z": mm_to_feet(max_z_mm),
            }
            if category:
                body["category"] = category
            return await client.post("/revit/analysis/elements_in_box", body)

    @mcp.tool()
    async def run_clash_detection(
        category_a: str,
        category_b: str,
        tolerance_mm: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Run a basic clash detection between two element categories.

        Args:
            category_a: First element category name, e.g. 'Structural Columns'.
            category_b: Second element category name, e.g. 'Ducts'.
            tolerance_mm: Minimum overlap distance in mm to report as a clash.
                          Use 0 for hard clashes only. Default: 0.

        Returns a list of clashing element pairs with their IDs and overlap distance.

        Note: This is a lightweight bounding-box clash check. For production
        clash detection, use Navisworks or BIM Collaborate.
        """
        from revit_client import mm_to_feet
        async with RevitClient() as client:
            return await client.post(
                "/revit/analysis/clash_detection",
                {
                    "category_a": category_a,
                    "category_b": category_b,
                    "tolerance": mm_to_feet(tolerance_mm),
                },
            )

    @mcp.tool()
    async def get_model_summary() -> dict[str, Any]:
        """
        Get a comprehensive summary of the model for quick orientation.

        Returns:
          - Project name and number
          - Total element count by category (top 20 categories)
          - Level list with elevations
          - Sheet count
          - View count
          - Warning count
          - Model file size
          - Revit version

        Ideal for providing AI context at the start of a Revit session.
        """
        async with RevitClient() as client:
            return await client.get("/revit/analysis/model_summary")


def _convert_bbox_to_mm(bbox: dict[str, Any]) -> dict[str, Any]:
    """Convert bounding box coordinates from feet to mm."""
    result: dict[str, Any] = {}
    for key, val in bbox.items():
        if isinstance(val, dict):
            result[key] = {
                k: round(feet_to_mm(v), 2) if isinstance(v, (int, float)) else v
                for k, v in val.items()
            }
        elif isinstance(val, (int, float)):
            result[f"{key}_mm"] = round(feet_to_mm(val), 2)
        else:
            result[key] = val
    return result
