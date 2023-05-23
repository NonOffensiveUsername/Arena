from functools import cache
from structs import *
import tilemappings
import util

class Tile:
	def __init__(self, wall_material, floor_material, ceiling_material):
		self.wall_material = wall_material
		self.floor_material = floor_material
		self.ceiling_material = ceiling_material
		self._features = []

	@property
	def features(self):
		return tuple(self._features)

	def add_feature(self, feature):
		self._features.append(feature)
		self._features.sort(key = lambda x: x.z_index)

	def build_descriptor(self):
		wall_tag = util.build_tag(self.wall_material.fg, self.wall_material.bg)
		wall_entry = f"Wall: {wall_tag}{self.wall_material.name}"
		floor_tag = util.build_tag(self.floor_material.fg, self.floor_material.bg)
		floor_entry = f"Floor: {floor_tag}{self.floor_material.name}"
		return [wall_entry, floor_entry] + [i.build_descriptor() for i in self._features]

	# Movement point cost of moving through the tile
	def traversal_cost(self, flyer = False):
		cost = -1
		if self.wall_material.state == State.GAS:
			cost = 10
		elif self.wall_material.state == State.LIQUID:
			cost = 30
		for feature in self._features:
			cost *= feature.walkability
		return cost

	# How likely a projectile is to strike the tile instead of passing through it
	def cover(self):
		return int(self.wall_material.state == State.SOLID)

	def copy(self):
		newTile = Tile(self.wall_material, self.floor_material, self.ceiling_material)
		newTile._features = self._features.copy()
		return newTile

	def is_void(self):
		return False

class VoidTile(Tile):
	VOID = Material("void", State.VOID, 0, 0, 1, '?', (0, 0, 0), (128, 0, 128), (128, 0, 128))

	def __init__(self):
		self.wall_material = VoidTile.VOID
		self.floor_material = VoidTile.VOID
		self.ceiling_material = VoidTile.VOID

	def traversal_cost(self):
		return -1

	def is_void(self):
		return True

class TileFeature:
	def __init__(self, name, z_index, material = None, fg_overwrite = False, bg_overwrite = False,
		char_overwrite = False, symbol = None, walkability = 1.0, visibility = 1.0, flags = ()):
		self.name = name
		self.z_index = z_index
		self.material = material
		self.fg_overwrite = fg_overwrite
		self.bg_overwrite = bg_overwrite
		self.char_overwrite = char_overwrite
		self.symbol = symbol
		self.walkability = walkability
		self.visibility = visibility
		self.flags = flags

	def build_descriptor(self):
		tag = util.build_tag(self.symbol.fg, self.symbol.bg)
		return tag + self.name

class TileContainer:
	def __init__(self, contents, width, height):
		self.contents = contents
		self.width = width
		self.height = height
		self.voidtile = VoidTile()
		self.construct_opacity_grid()

	def construct_opacity_grid(self):
		self.opacity_grid = self.map(tilemappings.opacity)

	@cache
	def visible_from(self, position):
		visible_tiles = {}
		targets = []
		# Cast rays from origin to each tile on the outer edge
		# ensuring all tiles are hit at least once
		for i in range(0, self.width):
			targets.append((i, 0))
			targets.append((i, self.height))
		for i in range(0, self.height):
			targets.append((0, i))
			targets.append((self.width, i))
		for t in targets:
			line = util.build_line(*position, *t)
			visibility = 1.0
			for point in line:
				if visibility < .1: break
				visible_tiles[point] = visibility
				visibility *= 1 - self.opacity_grid.get(point, 0.0)
		return visible_tiles

	def visibility_between(self, a, b):
		return max(
			self.visible_from(a).get(b, 0),
			self.visible_from(b).get(a, 0))
 
	def get_neighbors(self, x, y):
		neighbors = []
		for direction in util.MOORE_NEIGHBORHOOD:
			neighbor_x = x + direction[0]
			neighbor_y = y + direction[1]
			if (neighbor_x, neighbor_y) not in self.contents:
				continue
			cost = self.get_tile(neighbor_x, neighbor_y).traversal_cost()
			if cost >= 0:
				neighbors.append((neighbor_x, neighbor_y))
		return neighbors

	# Most search code modified from red blob games
	def breadth_first_search(self, start, goal = None):
		start = tuple(start)
		goal = tuple(goal)

		frontier = [start]
		came_from = {}
		came_from[start] = True

		while frontier:
			current = frontier.pop(0)

			if current == goal:
				break

			for node in self.get_neighbors(current[0], current[1]):
				if node not in came_from:
					frontier.append(node)
					came_from[node] = current

		return came_from

	def heuristic(self, start, goal = None):
		start = tuple(start)
		goal = tuple(goal)

		frontier = [(start, 0)]
		came_from = {}
		came_from[start] = True
		path_cost = { start: 0 }

		while frontier:
			current = frontier.pop(0)[0]

			if current == goal:
				break

			for node in self.get_neighbors(*current):
				node_cost = self.contents[node].traversal_cost()
				if node[0] != current[0] and node[1] != current[1]:
					node_cost = int(node_cost * 1.4) # Increase costs for diagonal movement
				node_cost += path_cost[current]

				if node not in path_cost or node_cost < path_cost[node]:
					path_cost[node] = node_cost
					x_dist = abs(node[0] - goal[0])
					y_dist = abs(node[1] - goal[1])
					heuristic_dist = int((x_dist + y_dist - (min(x_dist, y_dist) * 0.6)) * 10)
					priority = heuristic_dist + node_cost
					x = 0
					for i in range(0, len(frontier)):
						x = i
						if frontier[i][1] > priority:
							break
						x += 1
					frontier.insert(x, (node, priority))
					came_from[node] = current

		return came_from

	def next_step_towards(self, start, goal):
		paths = self.heuristic(goal, start)
		return paths[start]

	def map(self, func):
		result = {}
		for x in self.contents:
			result[x] = func(self.contents, x)
		return result

	# This is currently coupled too tightly to the definition of visual mapper
	def map_visible(self, func, position, sees, seen):
		result = {}
		for x in self.contents:
			if x in sees:
				result[x] = func(self.contents, x)
			elif x in seen:
				result[x] = func(self.contents, x, 0.4)
		return result

	def get_tile(self, x, y):
		if (x, y) in self.contents:
			return self.contents[(x, y)]
		else:
			return self.voidtile

	def set_tile(self, x, y, tile):
		self.contents[(x, y)] = tile.copy()
		self.construct_opacity_grid()