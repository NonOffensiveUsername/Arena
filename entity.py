import random
import util

class Entity:
	def __init__(self, name, position, material):
		self.name = name
		self.contents = []
		self.position = position
		self.delay = 10
		self.display_tile = '@'
		self.is_player = False
		self.speed = 1.0
		self.size = 10
		self.material = material
		self.flags = []
		self.calculate_hp()

	# Consider giving this function a return value as a way to pass signals to the game state
	# e.g. if the object is a light source and it changes how much light it gives off its
	# update call returns a SIGNALS.UPDATE_LIGHTING or something similar telling the game
	# engine to recalculate lighting
	def update(self, game_state = None):
		print("Generic entity " + self.name + " has been updated")

	def apply_delta(self, delta):
		self.position = (self.position[0] + delta[0], self.position[1] + delta[1])

	def move(self, game_state, direction):
		new_position = (direction[0] + self.position[0], direction[1] + self.position[1])
		target_tile = game_state.get_tile(new_position[0], new_position[1])
		cost = target_tile.traversal_cost()
		if traversible := cost >= 0:
			self.apply_delta(direction)
			self.delay = cost * self.speed
		else:
			self.delay = 10 * self.speed
		return traversible

	def calculate_hp(self):
		multiplier = 1
		if "undead" in self.flags:
			multiplier += 1
		self.hp_max = self.size * self.material.density * multiplier
		self.hp = self.hp_max

class RandomWalker(Entity):
	def update(self, game_state):
		direction = (random.randrange(-1, 2), random.randrange(-1, 2))
		self.move(game_state, direction)

class Chaser(Entity):
	def update(self, game_state):
		dist_from_target = util.dist_between(self.position, self.target.position)
		if dist_from_target > 1:
			next_square = game_state.next_step_towards(self.position, self.target.position)
			direction = (next_square[0] - self.position[0], next_square[1] - self.position[1])
			self.move(game_state, direction)
		else:
			self.delay = 10

class EntityContainer:
	def __init__(self):
		self.contents = []

	def sort_entities(self):
		self.contents = sorted(self.contents, key = lambda x: x.delay)

	def process(self, game_state = None):
		self.sort_entities()
		while self.contents[0].is_player == False or self.contents[0].delay > 0:
			self.tick(game_state)

	def tick(self, game_state = None):
		for entity in self.contents:
			entity.delay -= 1
		while self.contents[0].delay <= 0 and self.contents[0].is_player == False:
			self.contents[0].update(game_state)
		self.sort_entities()