"""
Material tools.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient


def register_tools(mcp: McpServer) -> None:

    @mcp.tool()
    async def list_materials(search: str | None = None) -> list[dict[str, Any]]:
        """
        List all materials in the project.

        Args:
            search: Optional search string to filter material names.

        Returns each material's name, ID, material class, and appearance asset name.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if search:
                params["search"] = search
            return await client.get("/revit/materials", params=params)

    @mcp.tool()
    async def get_material_by_name(material_name: str) -> dict[str, Any]:
        """
        Get detailed information about a material.

        Args:
            material_name: The exact material name.

        Returns the material's ID, class, colour (RGB), transparency, appearance,
        structural, and thermal asset details.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/materials/by_name", params={"material_name": material_name}
            )

    @mcp.tool()
    async def create_material(
        material_name: str,
        material_class: str = "Generic",
        color_r: int = 128,
        color_g: int = 128,
        color_b: int = 128,
        transparency: int = 0,
    ) -> dict[str, Any]:
        """
        Create a new material in the project.

        Args:
            material_name: The name for the new material (must be unique).
            material_class: Material class, e.g. 'Concrete', 'Metal', 'Wood',
                            'Glass', 'Generic'. Default: 'Generic'.
            color_r: Red component of the material colour (0-255). Default: 128.
            color_g: Green component (0-255). Default: 128.
            color_b: Blue component (0-255). Default: 128.
            transparency: Transparency percentage (0-100). Default: 0.

        Returns the new material's ElementId.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/materials/create",
                {
                    "material_name": material_name,
                    "material_class": material_class,
                    "color_r": color_r,
                    "color_g": color_g,
                    "color_b": color_b,
                    "transparency": transparency,
                },
            )

    @mcp.tool()
    async def duplicate_material(
        source_name: str, new_name: str
    ) -> dict[str, Any]:
        """
        Duplicate an existing material with a new name.

        Args:
            source_name: The material name to copy.
            new_name: The name for the new material.

        Returns the new material's ElementId.
        """
        async with RevitClient() as client:
            return await client.post(
                "/revit/materials/duplicate",
                {"source_name": source_name, "new_name": new_name},
            )

    @mcp.tool()
    async def set_element_material(
        element_id: int,
        material_name: str,
        material_param: str = "Material",
    ) -> dict[str, Any]:
        """
        Assign a material to an element.

        Args:
            element_id: The integer Revit ElementId.
            material_name: The name of the material to assign.
            material_param: The material parameter name on the element.
                            Default: 'Material'.

        Returns confirmation with the previous and new material names.
        """
        async with RevitClient() as client:
            return await client.post(
                f"/revit/elements/{element_id}/material",
                {"material_name": material_name, "material_param": material_param},
            )
