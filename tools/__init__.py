"""
Tool modules for the Revit MCP Server.

Each submodule exposes a `register_tools(mcp)` function that registers
its tools with the MCP server instance.
"""

from tools.analysis import register_tools as register_analysis_tools
from tools.conduit import register_tools as register_conduit_tools
from tools.elements import register_tools as register_element_tools
from tools.families import register_tools as register_family_tools
from tools.levels import register_tools as register_level_tools
from tools.materials import register_tools as register_material_tools
from tools.mep import register_tools as register_mep_tools
from tools.parameters import register_tools as register_parameter_tools
from tools.project import register_tools as register_project_tools
from tools.rooms import register_tools as register_room_tools
from tools.sheets import register_tools as register_sheet_tools
from tools.types import register_tools as register_type_tools
from tools.views import register_tools as register_view_tools
from tools.worksets import register_tools as register_workset_tools


def register_all_tools(mcp: object) -> None:
    """Register every tool category with the MCP server."""
    register_project_tools(mcp)
    register_element_tools(mcp)
    register_parameter_tools(mcp)
    register_family_tools(mcp)
    register_view_tools(mcp)
    register_sheet_tools(mcp)
    register_workset_tools(mcp)
    register_type_tools(mcp)
    register_room_tools(mcp)
    register_level_tools(mcp)
    register_material_tools(mcp)
    register_mep_tools(mcp)
    register_analysis_tools(mcp)
    register_conduit_tools(mcp)


__all__ = ["register_all_tools"]
