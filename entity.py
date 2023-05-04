import random
import math
import util
from structs import *
import dice
from copy import deepcopy

class BodyPart:
	def __init__(self, name, size = 0, hp_divisor = False, traits = []):
		self._children = []
		self.name = name
		self.traits = traits
		self.size = size
		self.hp_divisor = hp_divisor
		self.damage = 0
		self.parent = None

	def __str__(self):
		return self.treeview(0)

	def treeview(self, depth):
		outstr = f"{'|---' * depth}{self.name} ({self.size})\n"
		for child in self._children:
			outstr += child.treeview(depth + 1)
		return outstr

	def normalize(self):
		parts = self.get_part_list()
		parts.sort(key = lambda x: x.size)
		largest_size = parts[-1].size
		for part in parts:
			part.size -= largest_size

	def add_children(self, *args):
		for child in args:
			child.parent = self
			self._children.append(child)

	def remove_child(self, child):
		self._children.remove(child)

	def kill(self):
		if self.parent:
			self.parent.remove_child(self)

	def get_part_list(self):
		out_list = [self]
		for part in self._children:
			out_list += part.get_part_list()
		return out_list

	def get_parts_with_trait(self, trait):
		return list(filter(lambda x: trait in x.traits, self.get_part_list()))

	def get_weighted_random_part(self):
		parts = self.get_part_list()
		weights = []
		cum = 0
		for part in parts:
			cum += math.pow(1.5, part.size)
			weights.append(cum)
		return random.choices(parts, cum_weights = weights, k = 1)[0]

	def contains_trait(self, trait):
		for part in self.get_part_list():
			if trait in part.traits: return True
		return False

default_actor_attributes = {
	"attribute": {
		"size": 0,
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

default_entity_attributes = {
	"attribute": {
		"size": 0,
		"ST": 10,
		"HT": 10,
	},
	"trait": {},
	"bodyplan": "simple",
	"display": {
		"character": '*',
		"fg": [255, 255, 255],
		"bg": [0, 0, 0],
	}
}

class Entity:
	DEFAULT_MAT = None
	DEFAULT_TEMPLATE = default_entity_attributes

	def __init__(self, name, position, is_player = False):
		self.name = name
		self.contents = []
		self.position = position
		self.container = None
		self.delay = 0
		self.is_player = is_player
		self.pronoun = "it"
		self.observer = None
		self.material = Entity.DEFAULT_MAT
		self.traits = {}

	@classmethod
	def from_template(cls, name, position, template = {}, is_player = False):
		e = cls(name, position, is_player)

		full_template = util.deep_update(cls.DEFAULT_TEMPLATE, template)

		e.display_tile = Glyph(**full_template["display"])

		for attribute in full_template["attribute"]:
			setattr(e, attribute, full_template["attribute"][attribute])

		e.construct_body(full_template["bodyplan"])
		e.traits = full_template["trait"]
		e.calculate_secondaries()
		e.hp = e.hp_max

		return e

	@classmethod
	def from_part(cls, part, parent):
		name = f"{parent.name} severed {part.name}"
		e = cls(name, parent.position)
		e.material = parent.material
		e.root_part = deepcopy(part)
		e.size = e.root_part.size + parent.size
		e.root_part.normalize()
		e.ST = math.ceil(math.pow(1.5, e.size) * parent.ST)
		e.HT = 10
		e.display_tile = Glyph('%', (0, 0, 0), (200, 0, 0)) # TODO: Change glyph based on part traits

		return e

	def construct_body(self, bodyplan):
		if bodyplan == "humanoid":
			root = BodyPart("Torso", 0, traits = [PartFlag.VITALS])
			neck = BodyPart("Neck", -5, traits = [PartFlag.CUTTABLE])
			head = BodyPart("Head", -7, traits = [PartFlag.MIND])
			eyes = BodyPart("Eyes", -9, 10, traits = [PartFlag.SIGHT])
			l_arm = BodyPart("Left arm", -2, 2, traits = [PartFlag.LEVER])
			r_arm = BodyPart("Right arm", -2, 2, traits = [PartFlag.LEVER])
			l_hand = BodyPart("Left hand", -4, 3, traits = [PartFlag.SECONDARY_GRASPER, PartFlag.STRIKER])
			r_hand = BodyPart("Right hand", -4, 3, traits = [PartFlag.GRASPER, PartFlag.STRIKER])
			l_leg = BodyPart("Left leg", -2, 2, traits = [PartFlag.LEVER, PartFlag.WALKER])
			r_leg = BodyPart("Right leg", -2, 2, traits = [PartFlag.LEVER, PartFlag.WALKER])
			l_foot = BodyPart("Left Foot", -4, 3, traits = [PartFlag.BALANCER, PartFlag.STRIKER])
			r_foot = BodyPart("Right Foot", -4, 3, traits = [PartFlag.BALANCER, PartFlag.STRIKER])
			
			root.add_children(neck, l_arm, r_arm, l_leg, r_leg)
			neck.add_children(head)
			head.add_children(eyes)
			l_arm.add_children(l_hand)
			r_arm.add_children(r_hand)
			l_leg.add_children(l_foot)
			r_leg.add_children(r_foot)
	
			self.root_part =  root
		else:
			self.root_part = BodyPart("Mass", 0, traits = [PartFlag.SIMPLE])

	def calculate_secondaries(self): # This is poopy get rid of it
		self.hp_max = int(self.ST * self.material.density)

	def sever(self, part):
		new_entity = Entity.from_part(part, self)
		self.observer.add_entity(new_entity)
		part.kill()

	# Consider giving this function a return value as a way to pass signals to the game state
	# e.g. if the object is a light source and it changes how much light it gives off its
	# update call returns a SIGNALS.UPDATE_LIGHTING or something similar telling the game
	# engine to recalculate lighting
	def update(self, game_state = None):
		#print(f"The {self.name} continues being a {self.name}.")
		self.delay = random.randint(1000, 10000)

	def raise_event(self, event):
		if self.observer:
			self.observer.events.append(event)

	def apply_delta(self, delta):
		self.position = (self.position[0] + delta[0], self.position[1] + delta[1])

	def move(self, game_state, direction):
		if self.position is None: return False
		new_position = (direction[0] + self.position[0], direction[1] + self.position[1])
		target_tile = game_state.get_tile(new_position[0], new_position[1])
		cost = target_tile.traversal_cost() * (1 + util.is_diag(direction) * 0.4)
		if traversible := cost >= 0:
			self.apply_delta(direction)
			self.delay = cost / self.speed
		else:
			self.delay = 10
		return traversible

	def receive_attack(self, attacker, attack):
		damage = max(0, attack.power - self.material.hardness)
		uncapped_damage = damage
		target_part = attack.target
		if target_part is None:
			target_part = self.root_part.get_weighted_random_part()
		# TODO: Apply multiplier for damage type and target part here
		major_injury_threshold = \
			self.hp_max // target_part.hp_divisor + (self.hp_max % target_part.hp_divisor > 0) \
			if target_part.hp_divisor else None
		if target_part.hp_divisor:
			maximum = self.hp_max // target_part.hp_divisor - target_part.damage
			damage = min(damage, maximum)
		target_part.damage += damage
		self.hp -= damage
		damage_num_color = 'r' if damage > 0 else 'g'
		attack_descriptor = f"{attacker.name} attacks {self.name} in the {target_part.name} for [{damage_num_color}]{damage}[w] damage!"
		self.raise_event(Event(visual = attack_descriptor))
		if target_part.hp_divisor and target_part.damage >= major_injury_threshold and PartFlag.CRIPPLED not in target_part.traits:
			if uncapped_damage > (major_injury_threshold * 2):
				if attack.damage_type == DamageType.CUT:
					self.sever(target_part)
					sever_descriptor = f"The {self.name}'s {target_part.name} is [r]severed[w] by the attack!"
					self.raise_event(Event(visual = sever_descriptor))
					return
				target_part.kill()
				destroy_descriptor = f"The {self.name}'s {target_part.name} is [r]pulped[w] by the attack!"
				self.raise_event(Event(visual = destroy_descriptor))
				return
			target_part.traits.append(PartFlag.CRIPPLED)
			cripple_descriptor = f"The {self.name}'s {target_part.name} is [r]crippled[w] by the blow!"
			self.raise_event(Event(visual = cripple_descriptor))

	def can_be_picked_up(self, picker):
		return True

class Actor(Entity):
	DEFAULT_TEMPLATE = default_actor_attributes

	def __init__(self, name, position, is_player = False):
		super().__init__(name, position, is_player)

	def calculate_secondaries(self):
		super().calculate_secondaries()
		self.speed = (self.DX + self.HT) / 4
		if "speed_boost" in self.traits:
			self.speed += self.traits["speed_boost"]

	def send_attack(self, target):
		acc = dice.roll()
		swing = False
		effective_ST = self.ST + max(2, self.ST - 7) if swing else self.ST
		damage_dice = max((effective_ST - 3) // 8, 1)
		damage_mod = (effective_ST - 3) % 8 // 2 - 1 if effective_ST >= 11 else (effective_ST + 1) // 2 - 7
		power = dice.roll(damage_dice, mod = damage_mod)
		attack = Attack(power, DamageType.CUT if self.is_player else DamageType.BASH, acc)
		target.receive_attack(self, attack)
		self.delay = 10

	def receive_attack(self, attacker, attack):
		if dice.roll() <= 9:
			attack_descriptor = f"{attacker.name} attacks the {self.name}, but {self.pronoun} dodges!"
			self.raise_event(Event(visual = attack_descriptor))
			return
		super().receive_attack(attacker, attack)

		if self.hp > 0:
			return

		self.display_tile.fg = (150, 150, 150)
		self.display_tile.bg = (200, 0, 0)
		self.raise_event(Event(visual = f"[m]The {self.name} is struck down."))

	def dodge(self):
		dodge_target = int(self.speed) + 3
		r = dice.roll()
		return r <= dodge_target

	def get(self, target):
		if target is self:
			return False # Entities probably shouldn't be their own container
		if not target.can_be_picked_up(self):
			return False
		target.position = None
		target.container = self
		self.contents.append(target)
		return True

	def can_be_picked_up(self, picker):
		if self.dodge():
			self.raise_event(Event(visual = f"The {self.name} dodges the grab!"))
			return False
		return picker.ST > self.ST

class RandomWalker(Actor):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def update(self, game_state):
		if self.hp <= 0 or self.position is None:
			self.delay = 1000
			return
		direction = (random.randrange(-1, 2), random.randrange(-1, 2))
		self.move(game_state, direction)

class Chaser(Actor):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def update(self, game_state):
		if self.hp <= 0 or self.position is None:
			self.delay = 1000
			return
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
		self.sort_entities()

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

	def find_in(self, positions):
		found = []
		for e in self.contents:
			if e.position in positions: found.append(e)
		return found

	def get_neighbors(self, e):
		targets = []
		for direction in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 0), (0, 1), (1, -1), (1, 0), (1, 1)):
			targets.append(util.tup_add(e.position, direction))
		return self.find_in(targets)

	def pop_events(self):
		e = self.events.copy()
		self.events = []
		return e

	def build_grid(self, visible):
		grid = {}
		for e in sorted(self.contents, key = lambda x: x.size):
			if e.position in visible:
				grid[e.position] = e.display_tile
		return grid