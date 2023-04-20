from structs import *
from util import tup_add

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
	(True, False, False, False): 205,
	(False, True, False, False): 186,
	(True, True, False, False): 188,
	(False, False, True, False): 186,
	(True, False, True, False): 187,
	(False, True, True, False): 186,
	(True, True, True, False): 185,
	(False, False, False, True): 205,
	(True, False, False, True): 205,
	(False, True, False, True): 200,
	(True, True, False, True): 197,
	(False, False, True, True): 201,
	(True, False, True, True): 187,
	(False, True, True, True): 204,
	(True, True, True, True): 206
}

def visual_map_func(tiles, position):
	tile = tiles[position]
	if tile.wall_material.state == State.SOLID or tile.floor_material.state != State.SOLID:
		if tile.wall_material.smooth:
			neighbors = []
			for direction in ((-1, 0), (0, -1), (0, 1), (1, 0)):
				x = tup_add(position, direction)
				if x in tiles and tiles[x].wall_material.smooth:
					neighbors.append(True)
				else:
					neighbors.append(False)
			return Glyph(smooth_glyphs[tuple(neighbors)], tile.wall_material.fg, (0, 0, 0))
		else:
			return Glyph(tile.wall_material.texture, tile.wall_material.fg, tile.wall_material.bg)
	else:
		char = floor_glyphs[position.__hash__() % 10]
		return Glyph(char, tile.floor_material.floor_color, (0, 0, 0))

def opacity(tile):
	return tile.wall_material.state == State.SOLID