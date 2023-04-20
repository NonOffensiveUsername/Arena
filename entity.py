import random
import util
from structs import *
import dice
from copy import deepcopy

class BodyPart:
	def __init__(self, name, size = 1, hp_divisor = False, traits = []):
		self.children = []
		self.name = name
		self.traits = traits
		self.size = size
		self.hp_divisor = hp_divisor
		self.damage = 0

	def get_part_list(self):
		out_list = [self]
		for part in self.children:
			out_list += part.get_part_list()
		return out_list

	def get_parts_with_trait(self, trait):
		return list(filter(lambda x: trait in x.traits, self.get_part_list()))

	def get_weighted_random_part(self):
		parts = self.get_part_list()
		weights = []
		cum = 0
		for part in parts:
			cum += part.size
			weights.append(cum)
		return random.choices(parts, cum_weights = weights)[0]

	def contains_trait(self, trait):
		for part in self.get_part_list():
			if trait in part.traits: return True
		return False

	def entity_from_part(self, parent):
		new_body = deepcopy(self)
		e = Entity(parent.name + " " + self.name, parent.position, material = parent.material, bodytype = new_body)
		return e

default_entity_attributes = {
	"attribute": {
		"size": 10,
		"ST": 10,
		"HT": 10,
		"DX": 10,
		"IQ": 10,
	},
	"trait": {},
	"bodyplan": "humanoid",
	"display": {
		"character": 1,
		"fg": [255, 255, 255],
		"bg": [0, 0, 0],
	}
}

class Entity:

	DEFAULT_MAT = None

	def __init__(self, name, position, template = {}, is_player = False):
		self.name = name
		self.contents = []
		self.position = position
		self.delay = 0
		self.is_player = is_player
		self.pronoun = "it"
		self.observer = None
		self.material = Entity.DEFAULT_MAT

		full_template = util.dict_overwrite(default_entity_attributes, template)

		self.display_tile = Glyph(**full_template["display"])

		for attribute in full_template["attribute"]:
			setattr(self, attribute, full_template["attribute"][attribute])

		self.construct_body(full_template["bodyplan"])

		self.traits = full_template["trait"]

		self.calculate_secondaries()
		self.hp = self.hp_max

	def construct_body(self, bodyplan):
		if bodyplan == "humanoid":
			root = BodyPart("Torso", 35, traits = [PartFlag.VITALS])
			neck = BodyPart("Neck", 5, traits = [PartFlag.CUTTABLE])
			head = BodyPart("Head", 5, traits = [PartFlag.MIND])
			eyes = BodyPart("Eyes", 1, 10, traits = [PartFlag.SIGHT])
			l_arm = BodyPart("Left arm", 10, 2, traits = [PartFlag.LEVER])
			r_arm = BodyPart("Right arm", 10, 2, traits = [PartFlag.LEVER])
			l_hand = BodyPart("Left hand", 5, 4, traits = [PartFlag.SECONDARY_GRASPER, PartFlag.STRIKER])
			r_hand = BodyPart("Right hand", 5, 4, traits = [PartFlag.GRASPER, PartFlag.STRIKER])
			l_leg = BodyPart("Left leg", 10, 2, traits = [PartFlag.LEVER, PartFlag.WALKER])
			r_leg = BodyPart("Right leg", 10, 2, traits = [PartFlag.LEVER, PartFlag.WALKER])
			l_foot = BodyPart("Left Foot", 5, 4, traits = [PartFlag.BALANCER, PartFlag.STRIKER])
			r_foot = BodyPart("Right Foot", 5, 4, traits = [PartFlag.BALANCER, PartFlag.STRIKER])
	
			root.children = [neck, l_arm, r_arm, l_leg, r_leg]
			neck.children = [head]
			head.children = [eyes]
			l_arm.children = [l_hand]
			r_arm.children = [r_hand]
			l_leg.children = [l_foot]
			r_leg.children = [r_foot]
	
			self.root_part =  root
		else:
			self.root_part = BodyPart("Mass", 100, traits = [PartFlag.SIMPLE])

	def calculate_secondaries(self):
		self.hp_max = self.size * self.material.density
		self.speed = (self.DX + self.HT) / 4

	# Consider giving this function a return value as a way to pass signals to the game state
	# e.g. if the object is a light source and it changes how much light it gives off its
	# update call returns a SIGNALS.UPDATE_LIGHTING or something similar telling the game
	# engine to recalculate lighting
	def update(self, game_state = None):
		print(f"The {self.name} continues being a {self.name}.")
		self.delay = random.randint(100, 1000)

	def apply_delta(self, delta):
		self.position = (self.position[0] + delta[0], self.position[1] + delta[1])

	def move(self, game_state, direction):
		new_position = (direction[0] + self.position[0], direction[1] + self.position[1])
		target_tile = game_state.get_tile(new_position[0], new_position[1])
		cost = target_tile.traversal_cost() * (1 + util.is_diag(direction) * 0.4)
		if traversible := cost >= 0:
			self.apply_delta(direction)
			self.delay = cost / self.speed
		else:
			self.delay = 10
		return traversible

	def send_attack(self, target):
		acc = dice.roll()
		damage_dice = max((self.ST - 3) // 8, 1)
		damage_mod = (self.ST - 3) % 8 // 2 - 1 if self.ST >= 11 else (self.ST + 1) // 2 - 7
		power = dice.roll(damage_dice, mod = damage_mod)
		attack = Attack(power, DamageType.BASH, acc)
		target.receive_attack(self, attack)
		self.delay = 100 / self.speed

	def receive_attack(self, attacker, attack):
		if dice.roll() <= 9:
			attack_descriptor = f"{attacker.name} attacks the {self.name}, but {self.pronoun} dodges!"
			self.raise_event(Event(visual = attack_descriptor))
			return
		damage = max(0, attack.power - self.material.hardness)
		target_part = attack.target
		if target_part is None:
			target_part = self.root_part.get_weighted_random_part()
		# Apply multiplier for damage type and target part here
		if target_part.hp_divisor:
			maximum = self.hp_max // target_part.hp_divisor - target_part.damage
			damage = min(damage, maximum)
		target_part.damage += damage
		self.hp -= damage
		attack_descriptor = f"{attacker.name} attacks {self.name} in the {target_part.name} for {damage} damage!"
		self.raise_event(Event(visual = attack_descriptor))
		if target_part.hp_divisor and target_part.damage >= self.hp_max // target_part.hp_divisor and PartFlag.CRIPPLED not in target_part.traits:
			target_part.traits.append(PartFlag.CRIPPLED)
			cripple_descriptor = f"The {self.name}'s {target_part.name} is crippled by the blow!"
			self.raise_event(Event(visual = cripple_descriptor))

	def raise_event(self, event):
		if self.observer:
			self.observer.events.append(event)

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
			self.send_attack(self.target)

class EntityContainer:
	def __init__(self):
		self.contents = []
		self.events = []

	def add_entity(self, entity):
		self.contents.append(entity)
		entity.observer = self

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

	def find_at(self, position):
		found = []
		for e in self.contents:
			if e.position == position: found.append(e)
		return found

	def pop_events(self):
		e = self.events.copy()
		self.events = []
		return e