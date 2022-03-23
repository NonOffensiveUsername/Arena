from structs import *

def testMappingFunction(tile):
	return tile.wall_material.texture
	#if tile.wall_material.state == State.SOLID:
	#	return 'X'
	#elif tile.wall_material.state == State.LIQUID:
	#	return '~'
	#elif tile.wall_material.state == State.GAS:
	#	return '.'
	#elif tile.wall_material.state == State.PHANTASMAL:
	#	return '*'
	#elif tile.wall_material.state == State.VOID:
	#	return ' '
	#else:
	#	return '?'

def opacity(tile):
	return tile.wall_material.state == State.SOLID