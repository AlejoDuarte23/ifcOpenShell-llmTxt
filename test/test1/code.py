import textwrap
from tempfile import NamedTemporaryFile
import colorsys

import viktor as vkt
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element


def _get_material_counts(ifc_file_field):
	"""Extract material names and counts from uploaded IFC file."""
	content = ifc_file_field.file.getvalue()
	if isinstance(content, str):
		content = content.encode('utf-8')
	
	with NamedTemporaryFile(suffix='.ifc', delete=False, mode='wb') as tmp:
		tmp.write(content)
		model = ifcopenshell.open(tmp.name)
	
	counts = {}
	for product in model.by_type('IfcProduct'):
		mat_name = ifcopenshell.util.element.get_material(product)
		if mat_name:
			counts[str(mat_name)] = counts.get(str(mat_name), 0) + 1
	
	return counts


def _color_by_material(ifc_file_field):
	"""Color IFC model by material and return modified file."""
	content = ifc_file_field.file.getvalue()
	if isinstance(content, str):
		content = content.encode('utf-8')
	
	with NamedTemporaryFile(suffix='.ifc', delete=False, mode='wb') as tmp:
		tmp.write(content)
		model = ifcopenshell.open(tmp.name)
	
	# Collect unique materials
	material_map = {}
	for product in model.by_type('IfcProduct'):
		mat = ifcopenshell.util.element.get_material(product)
		if mat:
			mat_str = str(mat)
			if mat_str not in material_map:
				material_map[mat_str] = []
			material_map[mat_str].append(product)
	
	# Generate distinct colors for each material
	num_materials = len(material_map)
	if num_materials == 0:
		model.write(tmp.name)
		return open(tmp.name, 'rb').read()
	
	material_colors = {}
	for i, mat_name in enumerate(sorted(material_map.keys())):
		hue = i / max(num_materials, 1)
		r, g, b = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
		material_colors[mat_name] = (r, g, b)
	
	# Create styles and assign to products
	for mat_name, products in material_map.items():
		r, g, b = material_colors[mat_name]
		
		# Create style
		style = ifcopenshell.api.run("style.add_style", model, name=f"Material_{mat_name[:20]}")
		ifcopenshell.api.run("style.add_surface_style", model, style=style, attributes={
			"SurfaceColour": {"Red": r, "Green": g, "Blue": b}
		})
		
		# Assign style to each product's representation
		for product in products:
			if product.Representation:
				for rep in product.Representation.Representations:
					for item in rep.Items:
						ifcopenshell.api.run("style.assign_representation_styles", model, 
							shape_representation=rep, styles=[style])
						break
	
	# Write modified model
	model.write(tmp.name)
	return open(tmp.name, 'rb').read()


class Parametrization(vkt.Parametrization):
	app_section = vkt.Section('IFC Input')
	app_section.intro = vkt.Text(textwrap.dedent("""
	# IFC Viewer — Materials

	Upload an IFC file to visualize it and to list all materials used
	in the model. The table shows each material name and the number of
	products that reference it.
	"""))

	app_section.ifc = vkt.FileField('Please provide an IFC file')


class Controller(vkt.Controller):
	parametrization = Parametrization

	@vkt.IFCAndDataView('IFC + Materials', x_axis_to_right=True)
	def get_ifc_and_data_view(self, params, **kwargs):
		if not params.app_section.ifc:
			return vkt.IFCAndDataResult(ifc=None, data=vkt.DataGroup(vkt.DataItem('No file', '')))

		counts = _get_material_counts(params.app_section.ifc)
		items = [vkt.DataItem(name, str(count)) for name, count in sorted(counts.items())]
		data = vkt.DataGroup(*items) if items else vkt.DataGroup(vkt.DataItem('No materials', ''))

		# Color the IFC by material
		colored_ifc = _color_by_material(params.app_section.ifc)
		
		return vkt.IFCAndDataResult(ifc=vkt.File.from_data(colored_ifc), data=data)

	@vkt.TableView('Materials Table')
	def materials_table(self, params, **kwargs):
		if not params.app_section.ifc:
			return vkt.TableResult([], column_headers=["Material", "Count"])

		counts = _get_material_counts(params.app_section.ifc)
		data = [[name, count] for name, count in sorted(counts.items())]
		return vkt.TableResult(data, column_headers=["Material", "Count"])
