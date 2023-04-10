import json
import tile
from structs import *

def load_materials():
	mats_file = open("data/materials.json")
	mats_raw = mats_file.read()
	mats_file.close()
	mats_obj = json.loads(mats_raw)
	
	mats = {}
	for material in mats_obj:
		material["state"] = string_to_state(material["state"])
		mats[material["name"]] = Material(**material)

	return mats

def load_map(materials):
	tile_defs_file = open("data/tile_defs.json")
	tile_defs = json.loads(tile_defs_file.read())
	tile_defs_file.close()

	map_file = open("data/map.map")
	map_raw = map_file.read().replace("\n", "")
	map_file.close()

	tiles = tile.TileContainer({}, 60, 20)
	for z in range(0, len(map_raw)):
		x = z % 60
		y = z // 60
		glyph = map_raw[z]
		wall_mat_name = tile_defs[glyph]["wall_material"]
		wall_mat = materials[wall_mat_name]
		floor_mat_name = tile_defs[glyph]["floor_material"]
		floor_mat = materials[floor_mat_name]
		ceil_mat_name = tile_defs[glyph]["ceiling_material"]
		ceil_mat = materials[ceil_mat_name]
		new_tile = tile.Tile(wall_mat, floor_mat, ceil_mat)
		tiles.contents[(x, y)] = new_tile

	return tiles