from structs import *
from util import tup_add, color_mul, NEUMANN_NEIGHBORHOOD

floor_glyphs = {
	0: '.',
	1: ',',
	2: '\'',
	3: ' ',
	4: ' ',
	5: ' ',
	6: ' ',
	7: ' ',
	8: ' ',
	9: ' ',
}

smooth_glyphs = {
	(False, False, False, False): 'O',
	(True,  False, False, False): 205,
	(False, True,  False, False): 186,
	(True,  True,  False, False): 188,
	(False, False, True,  False): 186,
	(True,  False, True,  False): 187,
	(False, True,  True,  False): 186,
	(True,  True,  True,  False): 185,
	(False, False, False, True ): 205,
	(True,  False, False, True ): 205,
	(False, True,  False, True ): 200,
	(True,  True,  False, True ): 0xCA,
	(False, False, True,  True ): 201,
	(True,  False, True,  True ): 203,
	(False, True,  True,  True ): 204,
	(True,  True,  True,  True ): 206,
}

def visual_map_func(tiles, position, brightness = 1.0):
	tile = tiles[position]
	result = None
	if tile.wall_material.state == State.SOLID:
		if tile.wall_material.smooth:
			neighbors = []
			for direction in NEUMANN_NEIGHBORHOOD:
				x = tup_add(position, direction)
				if x in tiles and (tiles[x].wall_material.smooth or tiles[x].contains_flag('wall_connect')):
					neighbors.append(True)
				else:
					neighbors.append(False)
			result = Glyph(smooth_glyphs[tuple(neighbors)], tile.wall_material.fg, (0, 0, 0))
		else:
			result = Glyph(tile.wall_material.texture, tile.wall_material.fg, tile.wall_material.bg)
	else:
		char = floor_glyphs[position.__hash__() % 10] if not tile.floor_material.smooth else tile.floor_material.texture
		result = Glyph(char, tile.floor_material.floor_color, (0, 0, 0))
	for feature in tile.features:
		if feature.z_index < 0 and tile.wall_material.state == State.SOLID: break
		if feature.fg_overwrite:
			result.fg = feature.symbol.fg
		if feature.bg_overwrite:
			result.bg = feature.symbol.bg
		if feature.char_overwrite:
			result.character = feature.symbol.character
	result.bg = color_mul(result.bg, brightness)
	result.fg = color_mul(result.fg, brightness)
	return result

def opacity(tiles, position):
	tile = tiles[position]
	result = tile.wall_material.opacity
	for feature in tile.features:
		result = max(result, 1 - feature.visibility)
	return result