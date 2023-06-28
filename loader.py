import json
import os
import tile
from structs import *
from collections import ChainMap

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

default_tile = {
	'wall': 'air',
	'floor': 'air',
	'ceil': 'air',
}

def load_map(materials, features, map_name):
	with open(f"data/maps/{map_name}_defs.json") as defs_file:
		tile_defs = json.load(defs_file)

	with open(f"data/maps/{map_name}.map") as map_file:
		map_raw = map_file.read()

	width = len(map_raw.partition('\n')[0])
	height = map_raw.count('\n')
	map_raw = map_raw.replace("\n", "")

	tiles = tile.TileContainer({}, width, height)
	entity_blueprint = {}
	for z in range(0, len(map_raw)):
		glyph = map_raw[z]
		tile_template = ChainMap(tile_defs[glyph], default_tile)
		new_tile = tile.Tile(
			materials[tile_template["wall"]],
			materials[tile_template["floor"]],
			materials[tile_template["ceil"]]
		)
		if "features" in tile_template:
			for feature in tile_template["features"]:
				new_tile.add_feature(features[feature])
		x = z % width
		y = z // width
		if "entity" in tile_template:
			entity_blueprint[(x, y)] = tile_template['entity']
		tiles.set_tile(x, y, new_tile)

	return tiles, entity_blueprint

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