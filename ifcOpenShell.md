# IfcOpenShell Python: Complete AI Developer Reference

**System Prompt Context:**
This document maps Natural Language Queries (Q) to runnable Python code using `ifcopenshell` (v0.7.0+ / v0.8.0).
*   **Authoring/Editing:** ALWAYS use `ifcopenshell.api.run("module.usecase", ...)`.
*   **Reading/Analysis:** Preferred `ifcopenshell.util.*`.
*   **Variable Convention:** `model` = `ifcopenshell.file`, `element` = `IfcProduct`.

---

## 1. Core File Operations & Settings
**Library:** `ifcopenshell`

```python
import ifcopenshell
import ifcopenshell.api

# Q: Create a new blank IFC4 project in memory.
model = ifcopenshell.api.run("project.create_file", version="IFC4")

# Q: Create a new blank IFC4x3 project (Infrastructure).
model = ifcopenshell.api.run("project.create_file", version="IFC4X3")

# Q: Load an IFC file from disk.
model = ifcopenshell.open("C:/path/to/model.ifc")

# Q: Load an IFC file from a string blob.
model = ifcopenshell.file.from_string(ifc_string_data)

# Q: Save the model to a file.
model.write("output.ifc")

# Q: Check the IFC Schema version.
# Returns: "IFC4", "IFC2X3", "IFC4X3_ADD2"
schema_ver = model.schema

# Q: Get an entity by its GlobalId (GUID).
element = model.by_guid("28k9$u$C92qv40$1Xw994V")

# Q: Get an entity by its STEP ID (integer).
element = model.by_id(123)

# Q: Create a transaction (Undo/Redo support).
# Note: ifcopenshell.api handles transactions automatically, but manual control is possible.
model.begin_transaction()
# ... operations ...
model.end_transaction()

# Q: Define standard units (SI Units) for the project.
# Sets up Length (Meters), Area, Volume, Angle (Radians), etc.
ifcopenshell.api.run("unit.assign_unit", model) 

# Q: Define Imperial units (Feet/Inches).
ifcopenshell.api.run("unit.assign_unit", model, length={"is_metric": False, "exponent": 0})
```

---

## 2. Project Hierarchy & Spatial Structure
**API Module:** `root`, `project`, `aggregate`, `spatial`

```python
# Q: Setup the Root Project entity.
project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name="My BIM Project")

# Q: Assign the standard Global Unique ID (GUID) and ownership info to a new entity.
# Note: "root.create_entity" does this automatically.

# Q: Create a Site.
site = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSite", name="Construction Site")

# Q: Create a Building.
building = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuilding", name="Main Building")

# Q: Create a Storey (Level).
storey = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Level 01")

# Q: Build the hierarchy (Project -> Site -> Building -> Storey).
ifcopenshell.api.run("aggregate.assign_object", model, relating_object=project, product=site)
ifcopenshell.api.run("aggregate.assign_object", model, relating_object=site, product=building)
ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, product=storey)

# Q: Move an element from one spatial container (Storey) to another.
ifcopenshell.api.run("spatial.assign_container", model, relating_object=new_storey, product=element)

# Q: Unassign an element from its spatial container (make it orphaned).
ifcopenshell.api.run("spatial.unassign_container", model, relating_object=current_storey, product=element)
```

---

## 3. Element Authoring & Typing
**API Module:** `root`, `type`

```python
# Q: Create a physical element (e.g., Wall) without geometry.
wall = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Wall-101")

# Q: Create an element type (e.g., Wall Type).
wall_type = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWallType", name="W-Concrete-200mm")

# Q: Assign a type to an instance.
ifcopenshell.api.run("type.assign_type", model, related_objects=[wall], relating_type=wall_type)

# Q: Remove/Delete a product and all its relationships (safe delete).
ifcopenshell.api.run("root.remove_product", model, product=wall)

# Q: Copy a class/element from one library to the current model.
# Useful for bringing in standards.
ifcopenshell.api.run("root.copy_class", model, product=external_element)
```

---

## 4. Georeferencing & Coordinates
**API Module:** `georeference`, `cogo`

```python
# Q: Set the Map Coordinates (WCS) for the project.
# Defines the conversion between IFC Local origin and GIS (Easting/Northing/Elevation).
ifcopenshell.api.run("georeference.add_georeferencing", model, 
    crs_name="EPSG:3857", 
    easting=500000.0, northing=200000.0, orthogonal_height=100.0,
    x_axis_abscissa=1.0, x_axis_ordinate=0.0, scale=1.0)

# Q: Rotate True North.
ifcopenshell.api.run("georeference.edit_true_north", model, true_north=45.0)

# Q: Add a survey point (COGO).
ifcopenshell.api.run("cogo.add_survey_point", model, name="Point-A", x=10.5, y=20.0, z=0.0)
```

---

## 5. Geometry & Representation
**API Module:** `geometry`, `profile`, `model.by_type`

### 5.1 Context Setup
```python
# Q: Initialize geometric contexts (Model/Body and Plan/Axis).
# Usually done once per file.
body_context = ifcopenshell.api.run("context.add_context", model, context_type="Model")
axis_context = ifcopenshell.api.run("context.add_context", model, context_type="Model", 
    context_identifier="Axis", target_view="GRAPH_VIEW", parent=body_context)
```

### 5.2 Profiles (2D Cross Sections)
```python
# Q: Create a parameterized Rectangle profile (200x500mm).
rect_profile = ifcopenshell.api.run("profile.add_parameterized_profile", model, 
    ifc_class="IfcRectangleProfileDef", x_dim=0.5, y_dim=0.2)

# Q: Create a parameterized I-Shape (Steel Column).
ishape = ifcopenshell.api.run("profile.add_parameterized_profile", model, 
    ifc_class="IfcIShapeProfileDef", overall_width=0.3, overall_depth=0.3, 
    web_thickness=0.02, flange_thickness=0.02, fillet_radius=0.01)

# Q: Create an Arbitrary Closed Profile (Polygon).
# Points is a list of (x, y) tuples.
poly_profile = ifcopenshell.api.run("profile.add_arbitrary_profile", model, 
    points=[(0.,0.), (1.,0.), (1.,1.), (0.5, 1.5), (0.,1.)])
```

### 5.3 3D Representations
```python
# Q: Create an Extruded Body (Wall/Column) from a profile.
# Extrudes 'rect_profile' upwards by 3.0 meters.
body = ifcopenshell.api.run("geometry.add_wall_representation", model, 
    context=body_context, length=5.0, height=3.0, thickness=0.2)
# Note: For arbitrary profiles/columns, use generic extrusion:
# body = ifcopenshell.api.run("geometry.add_profile_representation", model, context=body_context, profile=ishape, depth=3.0)

# Q: Create a Tessellated Shape (Mesh) from vertices and faces.
# Verts = List of (x,y,z), Faces = List of indices [v1, v2, v3]
mesh_rep = ifcopenshell.api.run("geometry.add_mesh_representation", model, 
    context=body_context, vertices=[[0,0,0], [1,0,0], ...], faces=[[0,1,2], ...])

# Q: Assign the representation to the element.
ifcopenshell.api.run("geometry.assign_representation", model, product=wall, representation=body)

# Q: Update/Edit the placement of an object (Move/Rotate).
# Matrix 4x4.
ifcopenshell.api.run("geometry.edit_object_placement", model, product=wall, matrix=[
    [1.0, 0.0, 0.0, 10.0], # X=10
    [0.0, 1.0, 0.0, 20.0], # Y=20
    [0.0, 0.0, 1.0, 0.0],  # Z=0
    [0.0, 0.0, 0.0, 1.0]
])
```

### 5.4 Constructive Solid Geometry (CSG) & Boolean
```python
# Q: Create a void/opening in a wall (Boolean Difference).
# 1. Create the opening element.
opening = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcOpeningElement")
# 2. Add geometry to the opening (e.g., a box where the hole is).
open_rep = ifcopenshell.api.run("geometry.add_wall_representation", model, context=body_context, length=1.0, height=2.0, thickness=0.5)
ifcopenshell.api.run("geometry.assign_representation", model, product=opening, representation=open_rep)
# 3. Place the opening relative to the wall (or global).
ifcopenshell.api.run("geometry.edit_object_placement", model, product=opening, matrix=...)
# 4. Apply the boolean subtraction.
ifcopenshell.api.run("geometry.add_boolean", model, opening=opening, element=wall)
```

---

## 6. Materials & Styling
**API Module:** `material`, `style`

```python
# Q: Create a simple material "Concrete".
mat_concrete = ifcopenshell.api.run("material.add_material", model, name="Concrete")

# Q: Create a material with a specific color (Surface Style).
# 1. Create Style
style = ifcopenshell.api.run("style.add_style", model, name="Grey Concrete Style")
# 2. Add Surface Colour (RGB 0-1)
ifcopenshell.api.run("style.add_surface_style", model, style=style, attributes={
    "SurfaceColour": {"Red": 0.5, "Green": 0.5, "Blue": 0.5}
})
# 3. Associate style with material
ifcopenshell.api.run("style.assign_material_style", model, material=mat_concrete, style=style)

# Q: Assign material to an element.
ifcopenshell.api.run("material.assign_material", model, product=wall, material=mat_concrete)

# Q: Create a Layered Material Set (e.g., Wall with Brick + Air + Block).
lset = ifcopenshell.api.run("material.add_material_set", model, name="Cavity Wall", set_type="IfcMaterialLayerSet")
mat_brick = ifcopenshell.api.run("material.add_material", model, name="Brick")
ifcopenshell.api.run("material.add_layer", model, layer_set=lset, material=mat_brick, thickness=0.10)
ifcopenshell.api.run("material.add_layer", model, layer_set=lset, material=mat_concrete, thickness=0.20)

# Q: Assign Layer Set to a Wall Type (preferred) or Wall Instance.
ifcopenshell.api.run("material.assign_material", model, product=wall_type, material=lset)
```

---

## 7. Metadata: Properties, Quantities & Classification
**API Module:** `pset`, `classification`

```python
# Q: Add a custom Property Set (Pset) to an element.
pset = ifcopenshell.api.run("pset.add_pset", model, product=wall, name="Pset_WallCommon")

# Q: Edit/Set properties in a Pset.
ifcopenshell.api.run("pset.edit_pset", model, pset=pset, properties={
    "FireRating": "2HR",
    "LoadBearing": True,
    "Reference": "Ext-01"
})

# Q: Add Base Quantities (Qto) to an element.
qto = ifcopenshell.api.run("pset.add_qto", model, product=wall, name="Qto_WallBaseQuantities")
ifcopenshell.api.run("pset.edit_qto", model, qto=qto, properties={
    "Length": 5.0, 
    "Height": 3.0, 
    "Volume": 3.0, # 5 * 3 * 0.2
    "Width": 0.2
})

# Q: Import a Classification System (e.g., Uniclass).
system = ifcopenshell.api.run("classification.add_classification", model, name="Uniclass 2015")

# Q: Classify an element.
ifcopenshell.api.run("classification.add_reference", model, product=wall, classification=system,
    identification="Ss_25_10_32_35", name="External Wall System")
```

---

## 8. Domain: Structural Analysis & Grids
**API Module:** `grid`, `structural`

```python
# Q: Create a Grid Axis (Grid line).
# u=0 means first axis in the set.
axis_curve = ifcopenshell.api.run("grid.create_axis_curve", model, 
    points=[(0.0, 0.0), (10.0, 0.0)]) # Line from 0,0 to 10,0
grid_axis = ifcopenshell.api.run("grid.create_grid_axis", model, 
    axis_tag="A", axis_curve=axis_curve)

# Q: Assign Grid Axis to a Grid system.
grid = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcGrid", name="Main Grid")
ifcopenshell.api.run("aggregate.assign_object", model, relating_object=grid, product=grid_axis)

# Q: Create a Structural Analysis Model.
struct_model = ifcopenshell.api.run("structural.add_structural_analysis_model", model, name="SAP2000 Export")

# Q: Create a Structural Point Connection (Node).
node = ifcopenshell.api.run("structural.add_structural_member_connection", model, 
    name="Node1", coordinate=(0.0, 0.0, 3.0))

# Q: Create a Point Load.
load = ifcopenshell.api.run("structural.add_structural_load", model, name="PointLoad_10kN")
ifcopenshell.api.run("structural.edit_structural_load", model, load_item=load, 
    attributes={"ForceX": 0.0, "ForceY": 0.0, "ForceZ": -10000.0}) # Newtons
```

---

## 9. Domain: MEP (Systems & Connectivity)
**API Module:** `system`

```python
# Q: Create a System (e.g., Supply Air).
hvac_sys = ifcopenshell.api.run("system.add_system", model, ifc_class="IfcDistributionSystem", name="Supply Air")

# Q: Assign an element (Duct) to the System.
duct = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcDuctSegment")
ifcopenshell.api.run("system.assign_system", model, relating_system=hvac_sys, products=[duct])

# Q: Define a Port on an element.
port_1 = ifcopenshell.api.run("system.add_port", model, product=duct, name="Inlet")
ifcopenshell.api.run("geometry.edit_object_placement", model, product=port_1, matrix=...) # Locate port

# Q: Connect two elements via ports.
ifcopenshell.api.run("system.connect_port", model, port1=port_1, port2=port_2)
```

---

## 10. Domain: Infrastructure (IFC4x3 Alignment)
**API Module:** `alignment`

```python
# Q: Create an Alignment (Road/Rail Axis).
alignment = ifcopenshell.api.run("alignment.create", model, name="Road Axis 1")

# Q: Define Horizontal Alignment (2D).
horiz = ifcopenshell.api.run("alignment.get_horizontal_layout", model, alignment=alignment)
# Add segments: Line -> Curve -> Line
ifcopenshell.api.run("alignment.add_stationing_referent", model, alignment=alignment, station=0.0)
# Use "alignment.create_by_pi_method" or "alignment.create_layout_segment" for detailed curve geometry (Clothoinds/Circular Arcs).

# Q: Define Vertical Alignment (Profile).
vert = ifcopenshell.api.run("alignment.add_vertical_layout", model, alignment=alignment)

# Q: Create a Cant Alignment (Superelevation - Rail specific).
cant = ifcopenshell.api.run("alignment.get_cant_layout", model, alignment=alignment)
```

---

## 11. Domain: 4D (Sequence) & 5D (Cost)
**API Module:** `sequence`, `cost`

```python
# Q: Create a Construction Work Schedule.
schedule = ifcopenshell.api.run("sequence.add_work_schedule", model, name="Construction Phase 1")

# Q: Add a Task to the schedule.
task_a = ifcopenshell.api.run("sequence.add_task", model, work_schedule=schedule, name="Pour Concrete", predefined_type="CONSTRUCTION")

# Q: Set Task Duration and Start Time.
ifcopenshell.api.run("sequence.edit_task_time", model, task=task_a, 
    attributes={"ScheduleStart": "2024-01-01", "ScheduleDuration": "P5D"}) # ISO 8601 Duration (5 Days)

# Q: Assign an Element to a Task (4D Simulation).
ifcopenshell.api.run("sequence.assign_product", model, relating_process=task_a, related_object=wall)

# Q: Create a Cost Schedule.
cost_sched = ifcopenshell.api.run("cost.add_cost_schedule", model, name="BoQ")

# Q: Create a Cost Item.
item = ifcopenshell.api.run("cost.add_cost_item", model, cost_schedule=cost_sched, name="Concrete m3")

# Q: Assign Cost Value (Currency).
ifcopenshell.api.run("cost.add_cost_value", model, parent=item, value=150.0, currency="USD")
```

---

## 12. Data Extraction, Querying & Utilities
**Library:** `ifcopenshell.util.*`

```python
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.selector
import ifcopenshell.util.classification
import ifcopenshell.util.date

# Q: Filter elements using a Selector Query (CSS/jQuery style).
# Syntax: "Class[Attribute='Value']", ".Group", "#Id"
walls_ext = ifcopenshell.util.selector.filter_elements(model, 'IfcWall[IsExternal="TRUE"]')
doors_fire = ifcopenshell.util.selector.filter_elements(model, 'IfcDoor, IfcWindow')

# Q: Get all Property Sets as a dictionary.
# Returns: {'Pset_WallCommon': {'FireRating': '2HR'}, ...}
psets = ifcopenshell.util.element.get_psets(wall)

# Q: Get the specific value of a property safely.
rating = ifcopenshell.util.element.get_pset(wall, "Pset_WallCommon", "FireRating")

# Q: Get the absolute Global Matrix (coordinates) of an element.
# Returns: 4x4 numpy array.
matrix = ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement)

# Q: Get the container (Storey) of an element.
storey = ifcopenshell.util.element.get_container(wall)

# Q: Get the Material name(s).
# Returns: String or List of Strings depending on material usage.
mat_name = ifcopenshell.util.element.get_material(wall)

# Q: Convert IFC Date string to Python datetime object.
dt = ifcopenshell.util.date.ifc2datetime("2024-01-01T12:00:00")
```

---

## 13. Geometric Analysis (Meshing)
**Library:** `ifcopenshell.geom`

```python
import ifcopenshell.geom
import ifcopenshell.util.shape

# Q: Configure settings for geometry generation (Triangle Mesh).
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True) # Map to global (0,0,0) instead of local
settings.set(settings.USE_PYTHON_OPENCASCADE, True) # Use high-precision kernel

# Q: Create a Shape object for analysis.
try:
    shape = ifcopenshell.geom.create_shape(settings, wall)
    
    # Q: Access Vertices (Flattened list: x, y, z, x, y, z...).
    verts = shape.geometry.verts 
    
    # Q: Access Faces (Triangles: i1, i2, i3).
    faces = shape.geometry.faces
    
    # Q: Get the Transformation Matrix (if not using WORLD_COORDS).
    matrix = shape.transformation.matrix.data
except:
    print("Geometry generation failed (e.g., missing profile).")

# Q: Calculate Volume/Area using the shape engine.
# Note: This is geometric calculation, distinct from Qto attributes.
vol = ifcopenshell.util.shape.get_volume(wall)
area = ifcopenshell.util.shape.get_footprint_area(wall)

# Q: Get Axis Aligned Bounding Box (AABB).
# Returns: (min_x, min_y, min_z, max_x, max_y, max_z)
bbox = ifcopenshell.util.shape.get_element_bbox(wall)
```

---

## 14. Validation & Quality Control
**Library:** `ifctester`, `ifcopenshell.validate`

```python
import ifctester.ids
import ifctester.reporter

# Q: Validate the model against an IDS (Information Delivery Specification) file.
# IDS defines requirements like "All Walls must have FireRating property".
ids_file = ifctester.ids.open("requirements.ids")
my_ids_spec = ids_file.validate(model)

# Q: Generate a validation report (HTML).
reporter = ifctester.reporter.Html(my_ids_spec)
reporter.report() # Writes 'report.html'
# print(reporter.to_string()) # Get raw HTML

# Q: Validate IFC Syntax and Schema compliance (Standard check).
import ifcopenshell.validate
logger = ifcopenshell.validate.json_logger()
ifcopenshell.validate.validate(model, logger)
# logger.statements contains list of schema errors.
```

---

## 15. Miscellaneous Useful Functions
**Library:** `group`, `document`, `owner`

```python
# Q: Create a Group (arbitrary collection of objects).
group = ifcopenshell.api.run("group.add_group", model, name="Zone A")
ifcopenshell.api.run("group.assign_group", model, group=group, products=[wall, door])

# Q: Add an external Document Reference (URL/PDF).
doc = ifcopenshell.api.run("document.add_information", model, name="Datasheet", location="http://spec.com/wall.pdf")
ifcopenshell.api.run("document.assign_document", model, products=[wall], document_information=doc)

# Q: Create a Person and Organization (Owner).
person = ifcopenshell.api.run("owner.add_person", model, given_name="John", family_name="Doe")
org = ifcopenshell.api.run("owner.add_organisation", model, name="ACME Corp")
actor = ifcopenshell.api.run("owner.add_person_and_organisation", model, person=person, organisation=org)

# Q: Update Owner History of an object.
ifcopenshell.api.run("owner.update_owner_history", model, product=wall)
```

## 16. Viktor IFC Viewer
```python
import viktor as vkt

class Controller(vkt.Controller):
    @vkt.IFCView('IFC view')
    def get_ifc_view(self, params, **kwargs):
        ifc = vkt.File.from_path(Path(__file__).parent / 'sample.ifc')
        return vkt.IFCResult(ifc)
```

### Select stuff with viktor
```python

import viktor as vkt
import ifcopenshell
import ifcopenshell.util.element
from pathlib import Path
from tempfile import NamedTemporaryFile


class Parametrization(vkt.Parametrization):
    ifc = vkt.FileField("Please provide an IFC file")
    geometry = vkt.GeometrySelectField("Select Geometry")


class Controller(vkt.Controller):
    parametrization = Parametrization

    @vkt.IFCAndDataView("IFC", x_axis_to_right=True)
    def get_ifc_and_data_view(self, params, **kwargs):
        ifc_file = params.ifc.file
        if selected_geometry := params.geometry: # If user has made a selection, add its properties to `data`
            # parse your ifc file (e.g. with ifcopenshell as below)
            with NamedTemporaryFile(suffix=".ifc", delete=False, mode="w") as temp_f:
                temp_f.write(ifc_file.getvalue())

            model = ifcopenshell.open(Path(temp_f.name))
            elem = model.by_id(int(selected_geometry))
            
            # See https://wiki.osarch.org/index.php?title=IFC_attributes_and_properties
            # for a list of available IFC attributes and properties
            
            data_items = []
            for key, val in ifcopenshell.util.element.get_psets(elem).items():
                sub_data_items = []
                for k,v in val.items():
                    sub_data_items.append(vkt.DataItem(k, v))
                data_items.append(vkt.DataItem(key, '', subgroup=vkt.DataGroup(*sub_data_items)))
                
            data = vkt.DataGroup(*data_items)
        else:
            data = vkt.DataGroup(vkt.DataItem('No geometries selected', ''))
        return vkt.IFCAndDataResult(ifc=ifc_file, data=data)
```