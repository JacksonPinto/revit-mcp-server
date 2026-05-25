# Revit MCP Server

A robust, production-ready **Model Context Protocol (MCP) server** for Autodesk Revit, built in Python with 80+ tools covering the full Revit API surface area.

Connect Claude, Cursor, Windsurf, or any MCP-compatible AI client directly to a live Revit model for intelligent BIM automation, documentation, and design assistance.

---

## ✨ Features

- **80+ tools** across 13 categories — elements, parameters, families, views, sheets, worksets, levels, grids, rooms, materials, MEP, analysis, and project info
- **Metric-first unit handling** — all inputs in mm, outputs in mm/m²/m³ (configurable to imperial)
- **Three auth modes** — `none` (dev), `api_key`, `jwt` with OAuth 2.1-ready design
- **Structured retry logic** — exponential backoff on connection failures with configurable limits
- **Structured logging** — JSON or console output with request tracing
- **Revit 2023–2026 support** — automatic version detection via try/except
- **Two-component architecture** — Python MCP server (this repo) + pyRevit extension (included)

---

## Architecture

```
┌─────────────────┐     MCP Protocol      ┌──────────────────────────┐
│  AI Client      │◄─────────────────────►│  revit-mcp-server        │
│ (Claude, Cursor)│     stdio / SSE        │  (Python, mcp SDK)       │
└─────────────────┘                        │  80+ tool definitions    │
                                           └──────────┬───────────────┘
                                                      │ HTTP REST
                                                      │ localhost:48884
                                           ┌──────────▼───────────────┐
                                           │  pyRevit Extension        │
                                           │  (runs inside Revit)      │
                                           │  Routes API handlers      │
                                           └──────────┬───────────────┘
                                                      │ Revit API
                                           ┌──────────▼───────────────┐
                                           │  Autodesk Revit           │
                                           │  (2023 / 2024 / 2025 /   │
                                           │   2026)                   │
                                           └──────────────────────────┘
```

---

## Requirements

| Component | Requirement |
|-----------|------------|
| Python | 3.10+ |
| Revit | 2023, 2024, 2025, or 2026 |
| pyRevit | 4.8+ ([download](https://github.com/pyrevitlabs/pyRevit/releases)) |
| OS | Windows 10/11 (Revit is Windows-only) |

---

## Quick Start

### 1. Install the Python server

```bash
# Clone the repository
git clone https://github.com/jacksonpinto/revit-mcp-server.git
cd revit-mcp-server

# Install dependencies
pip install -e .

# Or with uv (recommended for isolated environments):
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set REVIT_MCP_API_KEY
```

### 3. Install the pyRevit extension

Copy the `pyrevit_extension` folder to your pyRevit extensions directory:

```
%APPDATA%\pyRevit\Extensions\RevitMCP.extension\
```

Then **reload pyRevit** from the pyRevit tab in Revit, or restart Revit.

Confirm it's running by visiting: `http://localhost:48884/revit/ping`

### 4. Configure your AI client

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "revit": {
      "command": "python",
      "args": ["/path/to/revit-mcp-server/server.py"],
      "env": {
        "REVIT_MCP_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Claude Code / Cursor / Windsurf** — add to your MCP settings:

```json
{
  "mcpServers": {
    "revit": {
      "command": "revit-mcp-server",
      "env": {
        "REVIT_MCP_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

---

## Tool Reference

### Project & Document (9 tools)
| Tool | Description |
|------|-------------|
| `get_project_info` | Project name, number, client, address, status |
| `get_document_stats` | Element counts by category, file size |
| `list_linked_models` | Revit links with load status |
| `get_model_warnings` | All model warnings with affected element IDs |
| `ping_revit` | Health check — Revit version, pyRevit version |
| `get_revit_version` | Application version and build number |
| `list_open_documents` | All open documents including families |
| `get_project_units` | Display unit settings |
| `set_project_parameter` | Update project info parameters |

### Elements (11 tools)
| Tool | Description |
|------|-------------|
| `get_element_by_id` | Full element detail by ElementId |
| `get_elements_by_category` | All instances in a category (with level filter) |
| `get_elements_by_type` | All instances of a type |
| `find_elements_by_parameter` | Filter by parameter value (equals/contains/etc.) |
| `get_selected_elements` | Current UI selection |
| `select_elements` | Programmatically select elements |
| `count_elements_by_category` | Count without full fetch |
| `delete_elements` | Delete elements (with pin check) |
| `move_elements` | Translate by XYZ delta (mm) |
| `copy_elements` | Copy with offset (mm) |
| `rotate_elements` | Rotate around axis and origin |
| `mirror_elements` | Mirror about plane |
| `get_element_location` | Point/curve location in mm |
| `pin_elements` | Pin or unpin elements |
| `change_element_type` | Retype instances |
| `get_element_dependencies` | Dependent element IDs |

### Parameters (9 tools)
| Tool | Description |
|------|-------------|
| `get_element_parameters` | All instance parameters (with group filter) |
| `get_parameter_value` | Single parameter value |
| `set_element_parameter` | Set one parameter |
| `set_element_parameters_batch` | Set multiple parameters in one transaction |
| `get_type_parameters` | Type-level parameters |
| `set_type_parameter` | Set a type parameter |
| `list_shared_parameters` | Shared parameters in the project |
| `list_project_parameters` | Project parameters and category bindings |
| `bulk_update_parameter` | Set same value on all elements in a category |
| `find_elements_missing_parameter` | QA/QC — find elements with empty parameters |

### Families (7 tools)
| Tool | Description |
|------|-------------|
| `list_family_categories` | Categories with family counts |
| `list_families` | Loaded families (category/name filter) |
| `list_family_types` | Types for a specific family |
| `get_family_info` | Family detail including system/in-place flag |
| `place_family_instance` | Place instance at XYZ with rotation and host |
| `load_family` | Load .rfa file into project |
| `duplicate_family_type` | Duplicate a type with new name |
| `rename_family_type` | Rename a type |

### Views (13 tools)
| Tool | Description |
|------|-------------|
| `list_views` | All views (type/name filter, exclude templates) |
| `get_view_by_name` | View detail by name |
| `create_floor_plan` | New floor plan for a level |
| `create_ceiling_plan` | New RCP for a level |
| `create_section_view` | Section from start/end points |
| `create_elevation_view` | Building or interior elevation |
| `create_3d_view` | Orthographic or perspective 3D view |
| `duplicate_view` | Duplicate with or without detailing |
| `list_view_templates` | All view templates |
| `apply_view_template` | Apply template to a view |
| `set_view_scale` | Set scale denominator |
| `set_view_detail_level` | Coarse / Medium / Fine |
| `rename_view` | Rename a view |
| `delete_view` | Delete a view |

### Sheets (11 tools)
| Tool | Description |
|------|-------------|
| `list_sheets` | All sheets (number/discipline filter) |
| `get_sheet_by_number` | Sheet detail with viewports |
| `create_sheet` | Create single sheet with titleblock |
| `create_sheets_bulk` | Create multiple sheets at once |
| `place_view_on_sheet` | Place viewport (auto-center option) |
| `list_views_on_sheet` | Viewports on a sheet |
| `remove_view_from_sheet` | Remove viewport (keep view) |
| `set_sheet_parameter` | Set sheet parameters (Drawn By, etc.) |
| `renumber_sheet` | Change sheet number |
| `list_titleblock_families` | Available titleblock types |
| `get_sheet_issue_history` | Revision history |

### Worksets (8 tools)
| Tool | Description |
|------|-------------|
| `is_workshared` | Check if model uses worksets |
| `list_worksets` | All user worksets with owner info |
| `create_workset` | New workset |
| `get_element_workset` | Which workset an element is on |
| `set_element_workset` | Move elements to a workset |
| `get_workset_elements` | All elements on a workset |
| `set_active_workset` | Change active workset |
| `rename_workset` | Rename a workset |

### Levels & Grids (7 tools)
| Tool | Description |
|------|-------------|
| `list_levels` | All levels sorted by elevation |
| `get_level_by_name` | Level detail with elevation (mm) |
| `create_level` | New level at elevation (mm) |
| `set_level_elevation` | Change level elevation |
| `rename_level` | Rename level + associated views |
| `list_grids` | All grid lines with endpoints (mm) |
| `create_grid_line` | New grid from start/end points (mm) |

### Rooms & Spaces (6 tools)
| Tool | Description |
|------|-------------|
| `list_rooms` | All rooms with area (m²) |
| `get_room_by_number` | Room detail by number |
| `create_room` | Place room at XY point on level |
| `get_room_at_point` | Which room contains a point |
| `list_spaces` | MEP spaces |
| `get_room_boundaries` | Room boundary curves (mm) |

### Materials (5 tools)
| Tool | Description |
|------|-------------|
| `list_materials` | All materials (name filter) |
| `get_material_by_name` | Material detail with colour |
| `create_material` | New material with RGB colour |
| `duplicate_material` | Copy a material |
| `set_element_material` | Assign material to element |

### MEP (7 tools)
| Tool | Description |
|------|-------------|
| `list_mep_systems` | Duct, piping, and electrical systems |
| `list_ducts` | Duct elements with size (mm) |
| `list_pipes` | Pipe elements with diameter (mm) |
| `list_electrical_circuits` | Electrical circuits |
| `get_mep_system_info` | System detail with flow/pressure |
| `list_mechanical_equipment` | AHUs, FCUs, VAVs, etc. |
| `list_light_fixtures` | Lighting fixtures |
| `list_plumbing_fixtures` | Plumbing fixtures |

### Analysis & Geometry (8 tools)
| Tool | Description |
|------|-------------|
| `get_element_bounding_box` | Bounding box in mm |
| `get_model_extents` | Overall model bounding box |
| `calculate_room_areas_by_level` | Total room area per level (m²) |
| `calculate_floor_area_by_category` | Area totals by type (m²) |
| `calculate_wall_areas` | Wall face areas with openings (m²) |
| `get_element_volume` | Element volume (m³) |
| `find_elements_in_bounding_box` | Spatial query by 3D region |
| `run_clash_detection` | Bounding-box clash between two categories |
| `get_model_summary` | Full model context summary for AI |

---

## Security

Authentication is controlled by `REVIT_MCP_AUTH_MODE`:

- **`none`** — No auth. Use only for local development. Never expose over a network.
- **`api_key`** — Static bearer token. Auto-generated if not set. Recommended for most users.
- **`jwt`** — Short-lived signed tokens. Set `REVIT_MCP_JWT_SECRET` and use the `issue_jwt()` method to generate tokens.

All three modes pass the token as an HTTP `Authorization: Bearer <token>` header on every request to the pyRevit Routes API.

See [`docs/SECURITY.md`](docs/SECURITY.md) for threat model and deployment guidance.

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Format
black .

# Type check
mypy server.py
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome — especially for:
- Additional Revit API coverage (structural elements, schedules, phases)
- Test coverage with mock Revit server
- Performance improvements for large models

---

## License

MIT — see [LICENSE](LICENSE).

---

## Acknowledgements

Built on research from the open-source Revit MCP community:
- [mcp-servers-for-revit/revit-mcp](https://github.com/mcp-servers-for-revit/revit-mcp)
- [Demolinator/revit-mcp-server](https://github.com/Demolinator/revit-mcp-server)
- [pyrevitlabs/pyRevit](https://github.com/pyrevitlabs/pyRevit)
