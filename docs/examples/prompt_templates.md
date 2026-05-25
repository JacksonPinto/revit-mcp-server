# Prompt Templates for Revit MCP Server

A collection of proven prompts for common Revit AI automation workflows.

---

## Session Setup

Always start a Revit session with this prompt to orient the AI:

```
Get me a model summary and project info for the current Revit model.
```

This calls `get_model_summary` and `get_project_info`, giving Claude full context about levels, categories, sheet counts, and project metadata.

---

## Model Audit & QA

### Find elements missing parameters
```
Find all Doors that are missing a 'Mark' parameter value.
Then do the same for Windows.
```

### Review model warnings
```
Get all model warnings. Group them by description and tell me which 
warning type affects the most elements.
```

### Count elements by category
```
Count the elements in the following categories and give me a summary table:
Walls, Doors, Windows, Floors, Ceilings, Structural Columns, Structural Framing
```

---

## Sheet Automation

### Create a full drawing set
```
Create sheets with the following numbers and names:
- A-001: TITLE SHEET
- A-100: SITE PLAN  
- A-101: LEVEL 1 FLOOR PLAN
- A-102: LEVEL 2 FLOOR PLAN
- A-200: ELEVATIONS - NORTH / SOUTH
- A-201: ELEVATIONS - EAST / WEST
- A-300: BUILDING SECTIONS
- A-400: ENLARGED PLANS
- A-500: INTERIOR ELEVATIONS
- A-600: DETAILS

Use the 'E1 30x42 Horizontal' titleblock.
```

### Place all floor plans on sheets
```
List all floor plan views. Then place each one on its corresponding sheet 
(match level name to sheet name). Auto-center each view on the sheet.
```

### Update sheet metadata
```
Set the 'Drawn By' parameter to 'JP' and 'Checked By' to 'TBD' 
on all sheets whose number starts with 'A-'.
```

---

## Parameter Workflows

### Bulk-update a parameter
```
Set the 'Phase Created' parameter to 'New Construction' for all Wall elements.
```

### Find and fix parameter inconsistencies
```
Get all doors and show me which ones have non-standard Mark values 
(anything other than a number between 1 and 999).
```

### Type parameter update
```
Find the door type named 'Single-Flush : 36" x 84"'. 
Get its type parameters. Then set 'Fire Rating' to '90 min'.
```

---

## View Management

### Create a complete view set for a new level
```
Create the following views for 'Level 3':
1. A floor plan named 'LEVEL 3 - FLOOR PLAN'
2. A reflected ceiling plan named 'LEVEL 3 - RCP'
3. Apply the 'Architectural Working' view template to both views.
Set the scale to 1:100 for both.
```

### Audit unused views
```
List all views that are not placed on any sheet. 
Group them by view type and sort by name.
```

---

## Element Analysis

### Spatial analysis
```
Calculate the total room area on each level of the building.
Show me a table with level name, room count, total area (m²), 
and average room area (m²).
```

### Clash detection
```
Run a clash detection between 'Structural Columns' and 'Ducts'.
Tell me how many clashes there are and which element IDs are involved.
```

### Find elements in a zone
```
Find all elements within a 5m x 5m x 4m bounding box centred at 
X=10000mm, Y=15000mm, Z=3000mm. Filter to Mechanical Equipment category.
```

---

## Family & Content Management

### Audit loaded families
```
List all families in the 'Doors' category. 
For each family, show me how many types it has and whether it's a system family.
```

### Place multiple fixtures
```
Place 6 instances of the family 'M_Desk' type '1525 x 762mm' on Level 2 
in a row starting at X=2000mm, Y=3000mm, spaced 2000mm apart in the X direction.
```

---

## Worksharing & Coordination

### Workset audit
```
List all worksets. For each workset, tell me how many elements are on it 
and whether it is currently owned by someone.
```

### Move elements to correct workset
```
Find all elements in the 'Mechanical Equipment' category. 
Move them all to the 'MEP - Mechanical' workset.
```

---

## Combined Workflows

### New level setup (all-in-one)
```
I need to set up a new floor at 12500mm elevation. Please:
1. Create a level called 'Level 4' at elevation 12500mm
2. Create a floor plan view called 'LEVEL 4 - FLOOR PLAN'  
3. Create a ceiling plan view called 'LEVEL 4 - RCP'
4. Create sheet A-104 called 'LEVEL 4 FLOOR PLAN'
5. Place the floor plan view on sheet A-104, auto-centered
6. Apply the 'Architectural Working' view template to both new views
7. Set the scale to 1:100

Report back what was created.
```
