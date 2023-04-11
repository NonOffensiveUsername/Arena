from structs import *
import tilemappings

class Tile:
	def __init__(self, wall_material, floor_material, ceiling_material):
		self.wall_material = wall_material
		self.floor_material = floor_material
		self.ceiling_material = ceiling_material

	# Movement point cost of moving through the tile
	def traversal_cost(self, flyer = False):
		if self.wall_material.state == State.GAS:
			return 10
		elif self.wall_material.state == State.LIQUID:
			return 30
		else:
			return -1

	# How likely a projectile is to strike the tile instead of passing through it
	def cover(self):
		if self.wall_material.state == State.SOLID:
			return 1
		else:
			return 0

	# How much the tile blocks light
	def opacity(self):
		return 0

	def copy(self):
		newTile = Tile(self.wall_material, self.floor_material, self.ceiling_material)
		return newTile

	def is_void(self):
		return False

class VoidTile(Tile):
	def __init__(self):
		VOID = Material("void", State.VOID, 0, 0, 1, '?', 0, 0, 0)
		self.wall_material = VOID
		self.floor_material = VOID
		self.ceiling_material = VOID

	def traversal_cost(self):
		return -1

	def is_void(self):
		return True

class TileContainer:
	def __init__(self, contents, width, height):
		self.contents = contents
		self.width = width
		self.height = height
		self.opacity_grid = {}

	def construct_opacity_grid(self):
		self.opacity_grid = self.map(tilemappings.opacity)

	def is_in_grid(self, x, y):
		return 0 <= x < self.width and 0 <= y < self.height
 
	def get_neighbors(self, x, y):
		dirs = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]
		#dirs = [[-1, 0], [0, -1], [0, 1], [1, 0]]
		neighbors = []
		for direction in dirs:
			neighbor_x = x + direction[0]
			neighbor_y = y + direction[1]
			if self.is_in_grid(neighbor_x, neighbor_y):
				cost = self.get_tile(neighbor_x, neighbor_y).traversal_cost()
				#neighbors.append((neighbor_x, neighbor_y, weight))
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

	def dijkstra(self, start, goal = None):
		#visits = 0
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

			for node in self.get_neighbors(current[0], current[1]):
				#visits += 1
				node_cost = self.contents[node].traversal_cost()
				if node[0] != current[0] and node[1] != current[1]:
					node_cost *= 1.4 # Increase costs for diagonal movement
				node_cost += path_cost[current]

				if node not in path_cost or node_cost < path_cost[node]:
					path_cost[node] = node_cost
					x = 0
					for i in range(0, len(frontier)):
						if frontier[i][1] < node_cost:
							x = i
					frontier.insert(x, (node, node_cost))
					came_from[node] = current

		#print("Visits: " + str(visits))
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

			for node in self.get_neighbors(current[0], current[1]):
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
			result[x] = func(self.contents[x])
		return result

	def get_tile(self, x, y):
		if (x, y) in self.contents:
			return self.contents[(x, y)]
		else:
			return VoidTile()

	def set_tile(self, x, y, tile):
		self.contents[(x, y)] = tile.copy()