import random
import math
import util
from structs import *
import dice
from copy import deepcopy

class BodyPart:
	def __init__(self, name, size = 0, hp_divisor = False, traits = []):
		self._children = []
		self.held = None
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

default_entity_attributes = {
	"attribute": {
		"size": 0,
		"ST": 10,
		"HT": 10,
	},
	"trait": {},
	"bodyplan": BodyType.SIMPLE,
	"factions": [],
	"use_cases": [],
	"melee_attacks": [],
	"ranged_attacks": [],
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
		self._contents = []
		self.position = position
		self.container = None
		self.delay = 0
		self.is_player = is_player
		self.pronoun = "it"
		self.observer = None
		self.material = Entity.DEFAULT_MAT
		self.traits = {}
		self.melee_attacks = []
		self.factions = []

	@classmethod
	def from_template(cls, name, position, *templates, is_player = False):
		e = cls(name, position, is_player)

		full_template = util.deep_update(cls.DEFAULT_TEMPLATE, {})
		for template in templates:
			full_template = util.deep_update(full_template, template)

		e.display_tile = Glyph(**full_template["display"])

		for attribute in full_template["attribute"]:
			setattr(e, attribute, full_template["attribute"][attribute])

		e.construct_body(full_template["bodyplan"])
		e.traits = full_template["trait"]
		e.factions = full_template["factions"]
		e.melee_attacks = full_template["melee_attacks"]
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

		root_is_lever = PartFlag.LEVER in e.root_part.traits
		improvised_attack_skill = Skill.BRAWLING
		if root_is_lever:
			if e.size > -2:
				improvised_attack_skill = Skill.AXE_MACE_2H
			else:
				improvised_attack_skill = Skill.AXE_MACE
		improvised_weapon_reach = list(range(root_is_lever, max(1, e.size + 3)))
		improvised_attack = {
			"skill": improvised_attack_skill,
			"quality": -2,
			"muscle": "thrust",
			"damage_type": DamageType.BASH,
			"damage_mod": -1,
			"ST_requirement": max(e.size * 2 + 14, 1),
			"reach": improvised_weapon_reach,
		}

		e.melee_attacks = [improvised_attack]

		return e

	def construct_body(self, bodyplan):
		if bodyplan == BodyType.HUMANOID:
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
		elif bodyplan == BodyType.CARCINOID:
			root = BodyPart("Thorax", 0, traits = [PartFlag.VITALS])
			head = BodyPart("Head", -7, traits = [PartFlag.MIND])
			eyes = BodyPart("Eyes", -9, 10, traits = [PartFlag.SIGHT])
			l_arm = BodyPart("Left arm", -2, 2, traits = [PartFlag.LEVER])
			r_arm = BodyPart("Right arm", -2, 2, traits = [PartFlag.LEVER])
			l_hand = BodyPart("Left hand", -4, 3, traits = [PartFlag.SECONDARY_GRASPER, PartFlag.STRIKER])
			r_hand = BodyPart("Right hand", -4, 3, traits = [PartFlag.GRASPER, PartFlag.STRIKER])
			front_l_leg = BodyPart("Front left leg", -2, 2, traits = [PartFlag.LEVER, PartFlag.WALKER, PartFlag.BALANCER])
			back_l_leg = BodyPart("Back left leg", -2, 2, traits = [PartFlag.LEVER, PartFlag.WALKER, PartFlag.BALANCER])
			front_r_leg = BodyPart("Front right leg", -2, 2, traits = [PartFlag.LEVER, PartFlag.WALKER, PartFlag.BALANCER])
			back_r_leg = BodyPart("Back right leg", -2, 2, traits = [PartFlag.LEVER, PartFlag.WALKER])

			root.add_children(head, l_arm, r_arm, front_r_leg, front_l_leg, back_r_leg, back_l_leg)
			head.add_children(eyes)
			l_arm.add_children(l_hand)
			r_arm.add_children(r_hand)

			self.root_part = root
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

	def build_contents_tree(self, prefix = ()):
		out = []
		for i in range(len(self._contents)):
			if len(prefix) > 0:
				prefix = prefix[:-1] + (prefix[-1] - 1,)

			str_prefix = "[y]"
			for e in range(o := len(prefix)):
				if prefix[e] > 0:
					if e == o - 1:
						str_prefix += '\xC3\xC4'
					else:
						str_prefix += '\xB3 '
				elif prefix[e] == 0:
					if e == o - 1:
						str_prefix += '\xC0\xC4'
					else:
						str_prefix += '  '
				else:
					str_prefix += '  '
			str_prefix += '[w]'

			out.append(str_prefix + self._contents[i].name)

			if self._contents[i]._contents:
				new_prefix = prefix + (len(self._contents[i]._contents),)
				out += self._contents[i].build_contents_tree(new_prefix)

		return out

	def remove(self, target):
		if target not in self._contents: return False
		target.position = self.position
		target.container = None
		self._contents.remove(target)
		for part in self.root_part.get_part_list():
			if part.held is target:
				part.held = None
				break
		return True

	def insert(self, target):
		if target in self._contents: return False
		target.container = self
		target.position = None
		self._contents.append(target)

class EntityContainer:
	def __init__(self):
		self.contents = []
		self.events = []

	def add_entity(self, *entities):
		for e in entities:
			self.contents.append(e)
			e.observer = self
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

	def get_neighbors(self, e, exclude_self = True):
		targets = []
		for direction in util.MOORE_NEIGHBORHOOD_INCLUSIVE:
			targets.append(util.tup_add(e.position, direction))
		neighbors = self.find_in(targets)
		if exclude_self and e in neighbors: neighbors.remove(e)
		return neighbors

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