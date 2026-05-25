"""
pyRevit Startup Script — Revit MCP Server Extension
====================================================

This file is automatically executed by pyRevit when Revit starts.
It registers all the HTTP route handlers that the MCP server calls.

Place this entire `pyrevit_extension` folder inside your pyRevit extensions
directory:
    %APPDATA%\\pyRevit\\Extensions\\RevitMCP.extension\\

Then reload pyRevit (or restart Revit) to activate the routes.

Route base URL: http://localhost:48884
"""

from __future__ import annotations

import sys
import os

# Ensure the routes folder is on sys.path
_THIS_DIR = os.path.dirname(__file__)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

try:
    from pyrevit import routes

    # Create a named API — all routes share this prefix
    api = routes.API("revit-mcp")

    # Register each route module
    from routes import project_routes
    from routes import element_routes
    from routes import parameter_routes
    from routes import family_routes
    from routes import view_routes
    from routes import sheet_routes
    from routes import workset_routes
    from routes import level_routes
    from routes import room_routes
    from routes import material_routes
    from routes import mep_routes
    from routes import analysis_routes

    project_routes._get_routes(api)
    element_routes._get_routes(api)
    parameter_routes._get_routes(api)
    family_routes._get_routes(api)
    view_routes._get_routes(api)
    sheet_routes._get_routes(api)
    workset_routes._get_routes(api)
    level_routes._get_routes(api)
    room_routes._get_routes(api)
    material_routes._get_routes(api)
    mep_routes._get_routes(api)
    analysis_routes._get_routes(api)

    print("[RevitMCP] Routes registered successfully on http://localhost:48884")

except Exception as e:
    import traceback
    print(f"[RevitMCP] ERROR registering routes: {e}")
    traceback.print_exc()
