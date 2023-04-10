from structs import *

def visual_map_func(tile):
	if tile.wall_material.state == State.SOLID or tile.floor_material.state != State.SOLID:
		return Glyph(tile.wall_material.texture, tile.wall_material.fg, tile.wall_material.bg)
	else:
		return Glyph(".", tile.floor_material.floor_color, (0, 0, 0))

def opacity(tile):
	return tile.wall_material.state == State.SOLID