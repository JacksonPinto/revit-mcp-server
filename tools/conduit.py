"""
Conduit auto-build tools — electrical circuit to conduit infrastructure.

This module orchestrates the full workflow for constructing conduit runs in Revit
based on existing electrical circuits. The workflow is:

  1. list_electrical_circuits()           → user picks a circuit
  2. analyze_circuit_connectors(id)       → verify all elements have conduit connectors
  3. list_conduit_types()                 → user picks conduit family/type
  4. get_circuit_element_sequence(id)     → see the ordered element chain + panel
  5. build_conduit_from_circuit(...)      → create all conduit segments + fittings

Architecture of the conduit run created:
  Panel ──conduit──> Element_N ──conduit──> ... ──conduit──> Element_1
  (ordered from panel outward through the circuit via connector traversal)

Key Revit API facts used here:
  - Conduit.Create(doc, typeId, startXYZ, endXYZ, levelId)
  - FamilyInstance.MEPModel.ConnectorManager.Connectors  (for fixtures/equipment)
  - Connector.Domain == Domain.DomainConduit              (filter for conduit ports)
  - Connector.Origin                                      (XYZ position)
  - Connector.IsConnected                                 (skip occupied ports)
  - ElectricalSystem.Elements                             (all circuit members)
  - ElectricalSystem.BaseEquipment                        (the panel)
  - doc.Create.NewElbowFitting(c1, c2)                    (corner fitting)
"""

from __future__ import annotations

from typing import Any

from mcp import McpServer

from revit_client import RevitClient, feet_to_mm, mm_to_feet


def register_tools(mcp: McpServer) -> None:

    # ------------------------------------------------------------------
    # Step 1 — Circuit discovery
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_electrical_circuits(
        panel_name: str | None = None,
        circuit_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List all electrical circuits (ElectricalSystem elements) in the project.

        Use this as the first step before building conduit infrastructure.
        Returns circuits the user can choose from.

        Args:
            panel_name: Optional — filter to circuits fed from a specific
                        electrical panel, e.g. 'LP-1A'.
            circuit_type: Optional — filter by circuit type:
                          'PowerCircuit', 'LightingCircuit', 'Spare', 'Space'.

        Returns each circuit's ID, name, circuit number, panel name,
        load name, voltage, amperage, number of elements, and whether
        conduit infrastructure already exists on this circuit.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if panel_name:
                params["panel_name"] = panel_name
            if circuit_type:
                params["circuit_type"] = circuit_type
            return await client.get("/revit/conduit/circuits", params=params)

    # ------------------------------------------------------------------
    # Step 2 — Connector analysis
    # ------------------------------------------------------------------

    @mcp.tool()
    async def analyze_circuit_connectors(circuit_id: int) -> dict[str, Any]:
        """
        Analyze all elements in a circuit to verify they have conduit connectors.

        This is a MANDATORY pre-flight check before building conduit. Elements
        without conduit-domain connectors in their family cannot have conduit
        connected to them automatically — those families must be modified first.

        Args:
            circuit_id: The ElementId of the ElectricalSystem (circuit).

        Returns:
          - circuit_name: The circuit name/number.
          - panel_name: The feeding electrical panel name.
          - element_count: Total elements in the circuit.
          - ready_elements: List of elements that HAVE conduit connectors.
            Each entry includes: element_id, category, family_name, type_name,
            level, conduit_connector_count, connector_origins_mm.
          - problem_elements: List of elements MISSING conduit connectors.
            Each entry includes: element_id, category, family_name, type_name,
            and a fix_instruction explaining how to add the connector in the
            family editor.
          - can_build: True if ALL elements have conduit connectors (ready to build).
          - panel_has_conduit_connector: Whether the panel itself has a conduit port.

        If can_build is False, show the user the problem_elements list and
        instruct them to modify those families before proceeding.
        """
        async with RevitClient() as client:
            result = await client.get(
                f"/revit/conduit/circuits/{circuit_id}/analyze_connectors"
            )
            # Convert connector origins from feet to mm
            for elem in result.get("ready_elements", []):
                if "connector_origins" in elem:
                    elem["connector_origins_mm"] = [
                        {
                            "x": round(feet_to_mm(pt["x"]), 2),
                            "y": round(feet_to_mm(pt["y"]), 2),
                            "z": round(feet_to_mm(pt["z"]), 2),
                        }
                        for pt in elem.pop("connector_origins")
                    ]
            return result

    # ------------------------------------------------------------------
    # Step 3 — Conduit type selection
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_conduit_types() -> list[dict[str, Any]]:
        """
        List all conduit types (families) loaded in the project.

        Use this to let the user choose which conduit type to use before
        calling build_conduit_from_circuit.

        Returns each conduit type's name, ElementId, trade size list,
        and material (e.g. 'EMT', 'RMC', 'PVC', 'Flexible').
        """
        async with RevitClient() as client:
            return await client.get("/revit/conduit/types")

    @mcp.tool()
    async def get_conduit_type_sizes(conduit_type_id: int) -> list[dict[str, Any]]:
        """
        Get the available standard trade sizes for a conduit type.

        Args:
            conduit_type_id: The ElementId of the ConduitType.

        Returns a list of available sizes with:
          - trade_size_mm: Nominal diameter in mm (e.g. 16, 20, 25, 32, 40, 50, 63)
          - trade_size_label: Display label (e.g. '3/4"', '1"', '1-1/4"')
          - inside_diameter_mm: Actual inner diameter in mm
          - outside_diameter_mm: Actual outer diameter in mm
        """
        async with RevitClient() as client:
            result = await client.get(
                f"/revit/conduit/types/{conduit_type_id}/sizes"
            )
            for s in result:
                for key in ("trade_size", "inside_diameter", "outside_diameter"):
                    if key in s:
                        s[f"{key}_mm"] = round(feet_to_mm(s.pop(key)), 2)
            return result

    # ------------------------------------------------------------------
    # Step 4 — Circuit element sequence preview
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_circuit_element_sequence(circuit_id: int) -> dict[str, Any]:
        """
        Get the ordered sequence of elements in a circuit, from the panel
        outward to the last element.

        The sequence is determined by BFS traversal starting from the panel's
        conduit connector, following the logical connector chain through the
        circuit elements.

        Args:
            circuit_id: The ElementId of the ElectricalSystem.

        Returns:
          - circuit_name: Circuit name.
          - panel: Panel element info (name, ID, level, connector_origin_mm).
          - sequence: Ordered list of elements from panel to last fixture.
            Each item includes: step (1-N), element_id, category, family_name,
            type_name, level, location_mm {x,y,z}, conduit_connector_origin_mm.
          - segment_count: Number of conduit segments that will be created.
          - total_run_length_mm: Estimated total conduit length in mm.

        Use this to preview the conduit path before building.
        """
        async with RevitClient() as client:
            result = await client.get(
                f"/revit/conduit/circuits/{circuit_id}/sequence"
            )
            # Convert all foot-based coordinates to mm
            def _ft_to_mm(pt: dict) -> dict:
                return {k: round(feet_to_mm(v), 2) if isinstance(v, (int, float)) else v
                        for k, v in pt.items()}

            for item in result.get("sequence", []):
                if "location" in item:
                    item["location_mm"] = _ft_to_mm(item.pop("location"))
                if "conduit_connector_origin" in item:
                    item["conduit_connector_origin_mm"] = _ft_to_mm(
                        item.pop("conduit_connector_origin")
                    )
            if "panel" in result and "connector_origin" in result["panel"]:
                result["panel"]["connector_origin_mm"] = _ft_to_mm(
                    result["panel"].pop("connector_origin")
                )
            if "total_run_length" in result:
                result["total_run_length_mm"] = round(
                    feet_to_mm(result.pop("total_run_length")), 2
                )
            return result

    # ------------------------------------------------------------------
    # Step 5 — Build conduit run
    # ------------------------------------------------------------------

    @mcp.tool()
    async def build_conduit_from_circuit(
        circuit_id: int,
        conduit_type_id: int,
        diameter_mm: float,
        routing_strategy: str = "direct",
        level_name: str | None = None,
        offset_z_mm: float = 0.0,
        connect_to_panel: bool = True,
        create_fittings: bool = True,
    ) -> dict[str, Any]:
        """
        Build conduit infrastructure for an entire electrical circuit.

        This is the main construction tool. It:
          1. Retrieves the ordered element sequence from the circuit.
          2. For each consecutive pair (panel→elem1→elem2→...→elemN):
             a. Locates the unused conduit connector on each element.
             b. Creates a Conduit segment from connector origin to connector origin.
             c. Sets the conduit diameter.
             d. Connects conduit end connectors to element connectors.
             e. If direction changes and create_fittings=True, inserts an elbow fitting.
          3. Reports every segment created and any elements that could not be connected.

        BEFORE CALLING THIS TOOL you must have:
          - Confirmed analyze_circuit_connectors shows can_build = True
          - Chosen conduit_type_id from list_conduit_types
          - Chosen diameter_mm from get_conduit_type_sizes

        Args:
            circuit_id: The ElementId of the ElectricalSystem (circuit).
            conduit_type_id: The ElementId of the ConduitType to use.
            diameter_mm: Nominal conduit diameter in mm (e.g. 20, 25, 32).
                         Must be a valid size for the chosen conduit type.
            routing_strategy: How to route conduit between elements:
                              'direct'   — straight line between connector origins
                                           (best for same-level straight runs).
                              'orthogonal' — route with 90° bends using the element
                                           X/Y alignment (generates elbow fittings).
                              Default: 'direct'.
            level_name: Override the level for conduit placement. If omitted,
                        each conduit segment uses the level of its host elements.
            offset_z_mm: Vertical offset applied to ALL conduit segments from
                         the element connector origin in mm. Useful to run conduit
                         above or below element connection points. Default: 0.
            connect_to_panel: If True (default), also create the final conduit
                              segment from the first circuit element back to the
                              electrical panel.
            create_fittings: If True (default), automatically insert elbow fittings
                             at direction changes between segments. Requires
                             elbow fitting families to be loaded.

        Returns:
          - circuit_name: The circuit processed.
          - conduit_type_name: The conduit type used.
          - diameter_mm: The diameter used.
          - segments_created: List of conduit segments created.
            Each segment: from_element, to_element, conduit_id,
            length_mm, start_mm {x,y,z}, end_mm {x,y,z}.
          - fittings_created: List of fitting ElementIds inserted (if any).
          - skipped_connections: Elements that could not be connected and why.
          - total_length_mm: Total conduit length created in mm.
          - success: True if all segments were created without errors.
          - warnings: List of non-fatal warnings (e.g. already-connected ports).
        """
        async with RevitClient() as client:
            body: dict[str, Any] = {
                "circuit_id": circuit_id,
                "conduit_type_id": conduit_type_id,
                "diameter": mm_to_feet(diameter_mm),
                "routing_strategy": routing_strategy,
                "offset_z": mm_to_feet(offset_z_mm),
                "connect_to_panel": connect_to_panel,
                "create_fittings": create_fittings,
            }
            if level_name:
                body["level_name"] = level_name
            result = await client.post("/revit/conduit/build", body)
            # Convert lengths back to mm
            for seg in result.get("segments_created", []):
                if "length" in seg:
                    seg["length_mm"] = round(feet_to_mm(seg.pop("length")), 2)
                for key in ("start", "end"):
                    if key in seg and isinstance(seg[key], dict):
                        seg[f"{key}_mm"] = {
                            k: round(feet_to_mm(v), 2)
                            for k, v in seg.pop(key).items()
                            if isinstance(v, (int, float))
                        }
            if "total_length" in result:
                result["total_length_mm"] = round(
                    feet_to_mm(result.pop("total_length")), 2
                )
            return result

    # ------------------------------------------------------------------
    # Utility / query tools
    # ------------------------------------------------------------------

    @mcp.tool()
    async def list_conduits(
        level_name: str | None = None,
        circuit_id: int | None = None,
        conduit_type_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List conduit segments in the project.

        Args:
            level_name: Optional — filter by level name.
            circuit_id: Optional — filter to conduits belonging to a circuit.
            conduit_type_name: Optional — filter by conduit type name, e.g. 'EMT'.

        Returns each conduit's ID, type, diameter (mm), length (mm), level,
        start/end coordinates (mm), and connected element IDs.
        """
        async with RevitClient() as client:
            params: dict[str, Any] = {}
            if level_name:
                params["level_name"] = level_name
            if circuit_id:
                params["circuit_id"] = circuit_id
            if conduit_type_name:
                params["conduit_type_name"] = conduit_type_name
            result = await client.get("/revit/conduit/list", params=params)
            for c in result:
                for key in ("diameter", "length"):
                    if key in c and isinstance(c[key], (int, float)):
                        c[f"{key}_mm"] = round(feet_to_mm(c.pop(key)), 2)
                for key in ("start", "end"):
                    if key in c and isinstance(c[key], dict):
                        c[f"{key}_mm"] = {
                            k: round(feet_to_mm(v), 2)
                            for k, v in c.pop(key).items()
                            if isinstance(v, (int, float))
                        }
            return result

    @mcp.tool()
    async def get_element_conduit_connectors(element_id: int) -> dict[str, Any]:
        """
        Get all conduit-domain connectors on a specific element.

        Use this to inspect whether an element's family has conduit connectors
        before building conduit infrastructure.

        Args:
            element_id: The integer Revit ElementId of a family instance
                        (light fixture, receptacle, switch, equipment, etc.).

        Returns:
          - element_id: The element ID.
          - family_name: The family name.
          - type_name: The type name.
          - has_conduit_connectors: True/False.
          - connectors: List of conduit connectors found.
            Each connector: index, origin_mm {x,y,z}, direction {x,y,z},
            is_connected (bool), connected_to_id (if connected).
          - fix_instruction: If no conduit connectors found, instructions for
                             adding one in the family editor.
        """
        async with RevitClient() as client:
            result = await client.get(
                f"/revit/conduit/element/{element_id}/connectors"
            )
            for conn in result.get("connectors", []):
                if "origin" in conn and isinstance(conn["origin"], dict):
                    conn["origin_mm"] = {
                        k: round(feet_to_mm(v), 2)
                        for k, v in conn.pop("origin").items()
                        if isinstance(v, (int, float))
                    }
            return result

    @mcp.tool()
    async def delete_circuit_conduits(circuit_id: int) -> dict[str, Any]:
        """
        Delete all conduit segments belonging to a circuit's conduit run.

        Use this to remove an incorrectly built conduit run so you can
        rebuild it with different parameters.

        Args:
            circuit_id: The ElementId of the ElectricalSystem.

        Returns count of conduit segments and fittings deleted.

        WARNING: This operation cannot be undone via the MCP server.
        Save your model before calling this.
        """
        async with RevitClient() as client:
            return await client.delete(
                "/revit/conduit/by_circuit",
                {"circuit_id": circuit_id},
            )

    @mcp.tool()
    async def get_conduit_build_instructions(circuit_id: int) -> dict[str, Any]:
        """
        Get a human-readable, step-by-step summary of what will happen when
        build_conduit_from_circuit is called for this circuit.

        Use this to explain the planned conduit run to the user BEFORE executing
        the build, including which families need conduit connectors added.

        Args:
            circuit_id: The ElementId of the ElectricalSystem.

        Returns a structured plan with:
          - pre_flight_status: 'ready' or 'needs_family_edits'
          - steps: Ordered list of human-readable steps (connect A to B, etc.)
          - problem_families: List of family names that need conduit connectors
          - estimated_total_length_mm: Estimated conduit run length
          - recommended_diameter_mm: Recommended conduit size based on circuit load
        """
        async with RevitClient() as client:
            result = await client.get(
                f"/revit/conduit/circuits/{circuit_id}/build_plan"
            )
            if "estimated_total_length" in result:
                result["estimated_total_length_mm"] = round(
                    feet_to_mm(result.pop("estimated_total_length")), 2
                )
            return result
