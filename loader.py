import json
import os
import tile
from structs import *

def load_materials():
	with open("data/materials.json") as mats_file:
		mats_raw = json.load(mats_file)
	
	mats = {}
	for material in mats_raw:
		material["state"] = State(material["state"])
		mats[material["name"]] = Material(**material)

	return mats

def load_features(materials):
	with open("data/maps/tile_features.json") as features_file:
		features = json.load(features_file)

	for i in features:
		features[i]["material"] = materials[features[i]["material"]]
		features[i]["symbol"] = Glyph(**features[i]["symbol"])
		features[i]["name"] = i
		features[i] = tile.TileFeature(**features[i])

	return features

def load_map(materials, features, map_name):
	with open(f"data/maps/{map_name}_defs.json") as defs_file:
		tile_defs = json.load(defs_file)

	with open(f"data/maps/{map_name}.map") as map_file:
		map_raw = map_file.read()

	width = len(map_raw.partition('\n')[0])
	height = map_raw.count('\n')
	map_raw = map_raw.replace("\n", "")

	tiles = tile.TileContainer({}, width, height)
	for z in range(0, len(map_raw)):
		glyph = map_raw[z]
		tile_template = tile_defs[glyph]
		new_tile = tile.Tile(
			materials[tile_template["wall_material"]],
			materials[tile_template["floor_material"]],
			materials[tile_template["ceiling_material"]]
		)
		if "features" in tile_template:
			for feature in tile_template["features"]:
				new_tile.add_feature(features[feature])
		tiles.set_tile(z % width, z // width, new_tile)

	return tiles

def load_templates():
	result = {}
	for filename in os.listdir('data/templates'):
		path = 'data/templates/' + filename
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