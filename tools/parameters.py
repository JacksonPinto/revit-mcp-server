"""
Parameter read/write tools for Revit elements.
Covers instance parameters, type parameters, shared parameters, and project parameters.
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient


def register_tools(mcp: McpServer) -> None:

    @mcp.tool()
    async def get_element_parameters(
        element_id: int,
        include_read_only: bool = False,
        group_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get all parameters for a Revit element.

        Args:
            element_id: The integer Revit ElementId.
            include_read_only: If True, also return read-only parameters. Default: False.
            group_filter: Optional parameter group name to filter by (e.g. 'Dimensions',
                          'Identity Data', 'Constraints', 'Graphics').

        Returns a list of parameters with name, value, storage type,
        group, and whether the parameter is read-only.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {"include_read_only": include_read_only}
            if group_filter:
                params["group_filter"] = group_filter
            return await client.get(f"/revit/elements/{element_id}/parameters", params=params)

    @mcp.tool()
    async def get_parameter_value(element_id: int, param_name: str) -> dict[str, Any]:
        """
        Get the value of a specific parameter on an element.

        Args:
            element_id: The integer Revit ElementId.
            param_name: The parameter name.

        Returns the parameter's name, value, storage type (string/double/int/elementId),
        and display string.
        """
        async with RevitClient() as client:
            return await client.get(
                f"/revit/elements/{element_id}/parameters/{param_name}"
            )

    @mcp.tool()
    async def set_element_parameter(
        element_id: int, param_name: str, value: str | int | float
    ) -> dict[str, Any]:
        """
        Set a parameter value on a Revit element instance.

        Args:
            element_id: The integer Revit ElementId.
            param_name: The parameter name to set.
            value: The new value. Strings are used for text parameters.
                   Numbers are used for numeric parameters (use mm for length values).

        Returns confirmation with old and new values.
        """
        async with RevitClient() as client:
            return await client.post(
                f"/revit/elements/{element_id}/parameters/set",
                {"param_name": param_name, "value": value},
            )

    @mcp.tool()
    async def set_element_parameters_batch(
        element_id: int, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Set multiple parameters on an element in a single transaction.

        Args:
            element_id: The integer Revit ElementId.
            parameters: A dict mapping parameter names to new values.
                        Example: {"Mark": "A-101", "Comments": "Reviewed", "Width": 1200}

        Returns per-parameter success/failure status.
        """
        async with RevitClient() as client:
            return await client.post(
                f"/revit/elements/{element_id}/parameters/batch",
                {"parameters": parameters},
            )

    @mcp.tool()
    async def get_type_parameters(type_id: int) -> list[dict[str, Any]]:
        """
        Get all type parameters for a Revit family type.

        Args:
            type_id: The integer ElementId of the family type.

        Returns a list of type parameters with name, value, and storage type.
        """
        async with RevitClient() as client:
            return await client.get(f"/revit/types/{type_id}/parameters")

    @mcp.tool()
    async def set_type_parameter(
        type_id: int, param_name: str, value: str | int | float
    ) -> dict[str, Any]:
        """
        Set a type parameter on a Revit family type.

        Args:
            type_id: The integer ElementId of the family type.
            param_name: The type parameter name to set.
            value: The new value.

        Returns confirmation with old and new values.
        """
        async with RevitClient() as client:
            return await client.post(
                f"/revit/types/{type_id}/parameters/set",
                {"param_name": param_name, "value": value},
            )

    @mcp.tool()
    async def list_shared_parameters() -> list[dict[str, Any]]:
        """
        List all shared parameters currently loaded in the project.

        Returns each shared parameter's name, GUID, data type, and group.
        """
        async with RevitClient() as client:
            return await client.get("/revit/parameters/shared")

    @mcp.tool()
    async def list_project_parameters() -> list[dict[str, Any]]:
        """
        List all project parameters defined in the active document.

        Returns each project parameter's name, binding type (instance/type),
        data type, and the categories it is bound to.
        """
        async with RevitClient() as client:
            return await client.get("/revit/parameters/project")

    @mcp.tool()
    async def bulk_update_parameter(
        category: str,
        param_name: str,
        value: str | int | float,
        level_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Set the same parameter value on ALL elements in a category.

        Useful for bulk updates like setting 'Phase Created' or 'Comments'
        on all elements in a category.

        Args:
            category: Revit category name, e.g. 'Walls'.
            param_name: The parameter name to update.
            value: The new value to apply to all matching elements.
            level_name: Optional — restrict update to a specific level.

        Returns count of elements updated and any failures.
        """
        async with RevitClient() as client:
            body: dict[str, Any] = {
                "category": category,
                "param_name": param_name,
                "value": value,
            }
            if level_name:
                body["level_name"] = level_name
            return await client.post("/revit/parameters/bulk_update", body)

    @mcp.tool()
    async def find_elements_missing_parameter(
        category: str, param_name: str
    ) -> list[dict[str, Any]]:
        """
        Find elements in a category that have an empty or null value for a parameter.

        Args:
            category: Revit category name, e.g. 'Doors'.
            param_name: The parameter name to check, e.g. 'Mark'.

        Returns list of element IDs and their current (empty) parameter states.
        Useful for model QA/QC workflows.
        """
        async with RevitClient() as client:
            return await client.get(
                "/revit/parameters/missing",
                params={"category": category, "param_name": param_name},
            )
