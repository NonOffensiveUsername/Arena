import json
import os
import tile
from structs import *

def load_materials():
	mats_file = open("data/materials.json")
	mats_raw = mats_file.read()
	mats_file.close()
	mats_obj = json.loads(mats_raw)
	
	mats = {}
	for material in mats_obj:
		material["state"] = State(material["state"])
		mats[material["name"]] = Material(**material)

	return mats

def load_map(materials, map_name):
	with open(f"data/maps/{map_name}_defs.json") as defs_file:
		tile_defs = json.load(defs_file)

	with open(f"data/maps/{map_name}.map") as map_file:
		map_raw = map_file.read()

	width = len(map_raw.partition('\n')[0])
	height = map_raw.count('\n')
	map_raw = map_raw.replace("\n", "")

	tiles = tile.TileContainer({}, width, height)
	for z in range(0, len(map_raw)):
		x = z % width
		y = z // width
		glyph = map_raw[z]
		wall_mat_name = tile_defs[glyph]["wall_material"]
		wall_mat = materials[wall_mat_name]
		floor_mat_name = tile_defs[glyph]["floor_material"]
		floor_mat = materials[floor_mat_name]
		ceil_mat_name = tile_defs[glyph]["ceiling_material"]
		ceil_mat = materials[ceil_mat_name]
		new_tile = tile.Tile(wall_mat, floor_mat, ceil_mat)
		tiles.set_tile(x, y, new_tile)

	return tiles

def load_templates():
	result = {}
	for filename in os.listdir('data/templates'):
		path = 'data/templates/' + filename
		print(f"Loading template file {path}")
		with open(path) as file:
			templates = json.load(file)

		# Filtering strings into enums
		for template in templates.values():
			if "bodyplan" in template:
				template["bodyplan"] = BodyType(template["bodyplan"])
			if "melee_attacks" in template:
				for attack in template["melee_attacks"]:
					attack["skill"] = Skill(attack["skill"])
					attack["damage_type"] = DamageType(attack["damage_type"])

		result.update(templates)

	return result