# Conduit Auto-Build from Electrical Circuit Path

This document explains the end-to-end workflow for automatically constructing
conduit infrastructure in Revit from existing electrical circuits using the MCP server.

---

## Overview

The conduit builder traverses an electrical circuit from the panel outward through each
connected fixture/equipment, and creates conduit segments connecting them in sequence.

```
Electrical Panel
      │
    [conduit segment]
      │
  Light Fixture 1
      │
    [conduit segment + elbow fitting if direction changes]
      │
  Light Fixture 2
      │
    [conduit segment]
      │
  Receptacle
```

---

## Pre-requisites

1. **Electrical circuits exist** — panels, lighting circuits, and power circuits must be
   modelled in Revit (MEP model).
2. **pyRevit installed** — the MCP Routes API requires pyRevit 4.8+.
3. **Conduit types loaded** — at least one ConduitType family (e.g. EMT, RMC, PVC) must
   be loaded in the project.
4. **Elbow fittings loaded** — if `create_fittings=True`, conduit elbow families must be
   loaded and set as the default in Conduit Settings.
5. **Families have conduit connectors** — each fixture/equipment family must have a
   conduit-domain connector. If not, the workflow tells you exactly which families to fix.

---

## Step-by-Step Workflow

### Step 1 — Discover circuits

```
List all electrical circuits in the project.
```

Calls `list_electrical_circuits()`. Filter by panel name or circuit type.

**Example AI prompt:**
> "List all power circuits fed from panel LP-1A."

---

### Step 2 — Pre-flight check (REQUIRED)

```
Analyze circuit connectors for circuit ID 12345.
```

Calls `analyze_circuit_connectors(circuit_id)`. This is **mandatory** before building.

The response includes:
- `can_build`: `true` if all elements have conduit connectors.
- `problem_elements`: Elements whose families are missing conduit connectors.
- `fix_instruction`: Exact steps to add a conduit connector in the family editor.

**If `can_build` is `false`**, fix the listed families first:
1. Select the element in Revit → Edit Family.
2. In the Family Editor: **Manage → MEP Settings → Connectors → Add Connector**.
3. Set: **System Classification = Conduit (Electrical)**, **Connector Type = End**,
   **Flow Direction = Bidirectional**.
4. Place the connector at the conduit entry point on the fixture geometry.
5. Save and reload the family into the project (overwrite existing).
6. Re-run `analyze_circuit_connectors` to confirm the fix.

---

### Step 3 — Choose conduit type

```
List all conduit types available in this project.
```

Calls `list_conduit_types()`. Returns names like "EMT", "RMC - Rigid Metal Conduit",
"PVC Conduit Schedule 40", etc.

Then optionally:
```
Get available sizes for conduit type ID 67890.
```

Calls `get_conduit_type_sizes(conduit_type_id)`. Returns nominal sizes in mm.

**Common nominal sizes (mm → closest inch equivalent):**
| mm | Inch |
|----|------|
| 16 | 1/2" |
| 20 | 3/4" |
| 25 | 1"   |
| 32 | 1-1/4" |
| 40 | 1-1/2" |
| 50 | 2"   |

---

### Step 4 — Preview the run (optional but recommended)

```
Show me the conduit build plan for circuit 12345.
```

Calls `get_conduit_build_instructions(circuit_id)`. Returns:
- Ordered element sequence from panel to last fixture.
- Estimated segment lengths.
- Which elements are blocked (missing connector).
- Recommended conduit diameter based on circuit amperage.

---

### Step 5 — Build the conduit run

```
Build conduit for circuit 12345 using conduit type 67890 with 20mm diameter.
```

Calls `build_conduit_from_circuit(circuit_id=12345, conduit_type_id=67890, diameter_mm=20)`.

**Full parameter reference:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `circuit_id` | required | ElectricalSystem ElementId |
| `conduit_type_id` | required | ConduitType ElementId |
| `diameter_mm` | required | Nominal diameter in mm |
| `routing_strategy` | `"direct"` | `"direct"` = straight line; `"orthogonal"` = 90° bends |
| `level_name` | auto | Override level for all segments |
| `offset_z_mm` | `0` | Raise/lower conduit from connector origin |
| `connect_to_panel` | `true` | Also run conduit back to the panel |
| `create_fittings` | `true` | Insert elbow fittings at direction changes |

**Returns:**
- List of conduit segment ElementIds created
- List of elbow fitting ElementIds inserted
- Any skipped connections with detailed reasons
- Total conduit length in mm

---

## Routing Strategies

### `direct` (default)
Creates a straight-line conduit segment directly from one connector origin to the next.
Best for: same-level horizontal runs, vertical drops, pre-routed conduit paths.

### `orthogonal`
Creates two segments per connection: one horizontal (XY plane) then one vertical (Z).
Inserts an elbow fitting at the bend.
Best for: routing from ceiling fixtures down to junction boxes at a different elevation.

---

## Element Ordering Algorithm

The circuit elements are ordered using BFS traversal from the panel outward:

1. Start at `ElectricalSystem.BaseEquipment` (the panel).
2. Walk through connector `AllRefs` to find adjacent circuit elements.
3. Any elements not reachable via connector chain are sorted by distance from the panel.

This ensures conduit runs in a logical sequence matching the electrical topology.

---

## Prompt Templates

### Full one-shot workflow
```
I need to run conduit for circuit 'LP-1A/3' in this Revit model.
1. Analyze the circuit connectors — tell me if any families need to be modified.
2. Show me available conduit types and sizes.
3. Show me the build plan with estimated lengths.
4. Build the conduit using EMT conduit, 20mm diameter, direct routing.
```

### Re-build after fixing families
```
I've modified the family 'M_Light Fixture - Linear' to add a conduit connector.
Please re-analyze circuit 12345 and then rebuild the conduit run.
```

### Specific level / offset
```
Build conduit for circuit 54321 using PVC conduit, 25mm, 
with a 200mm upward offset from the connector origins, on Level 2.
```

### Delete and rebuild
```
Delete all conduit segments for circuit 12345, then rebuild using 
the orthogonal routing strategy with 20mm EMT.
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `can_build = false` | Element family has no conduit connector | Follow `fix_instruction` in `analyze_circuit_connectors` |
| Segment skipped — "start and end points are identical" | Two elements share the exact same conduit connector origin | Add an `offset_z_mm` value (e.g. 50mm) |
| Elbow fitting failed | Elbow family not loaded or wrong size | Load a matching conduit elbow family, or set `create_fittings=false` |
| `Conduit.Create failed` | Level not found, or overlapping geometry | Set `level_name` explicitly |
| Panel not connected | Panel family has no conduit connector | Add conduit connector to the panel family, or set `connect_to_panel=false` |

---

## API Reference

| Tool | Route | Purpose |
|------|-------|---------|
| `list_electrical_circuits` | GET /revit/conduit/circuits | Discover circuits |
| `analyze_circuit_connectors` | GET /revit/conduit/circuits/{id}/analyze_connectors | Pre-flight check |
| `list_conduit_types` | GET /revit/conduit/types | Available conduit families |
| `get_conduit_type_sizes` | GET /revit/conduit/types/{id}/sizes | Available diameters |
| `get_circuit_element_sequence` | GET /revit/conduit/circuits/{id}/sequence | Preview ordering |
| `get_conduit_build_instructions` | GET /revit/conduit/circuits/{id}/build_plan | Human-readable plan |
| `build_conduit_from_circuit` | POST /revit/conduit/build | **Main build operation** |
| `list_conduits` | GET /revit/conduit/list | Query existing conduits |
| `get_element_conduit_connectors` | GET /revit/conduit/element/{id}/connectors | Inspect connectors |
| `delete_circuit_conduits` | DELETE /revit/conduit/by_circuit | Remove a conduit run |
