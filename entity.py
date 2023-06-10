import random
import math
import util
from structs import *
import dice
from copy import deepcopy
from collections import defaultdict
from body import BodyPart, construct_body

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
	"ammo": {},
	"display": {
		"character": '*',
		"fg": [255, 255, 255],
		"bg": [0, 0, 0],
	}
}

# List of Entity Attributes:
#  name           - Display name for use in the interface. Not unique or an
#                   identifier.
#  _contents      - Entities that move with the entity because they are on, in,
#                   or held by the entity. Internal use only.
# contents        - Property for accessing an entity's contents. Searches
#                   recursively so that contents of contents are returned as
#                   well.
# position        - (x, y) tuple representing the physical location of the
#                   entity. If the entity is contained in another this is None.
# global_position - (x, y) tuple representing the physical location of the
#                   entity, even if the entity is contained within another.
#                   Property, cannot be set. Change the position or the
#                   position of the container instead.
# container       - The entity this entity is contained by, or None if the
#                   entity is independent. This is the physical container
#                   in the game world, not the EntityContainer object which
#                   manages the entity.
# delay           - The number of ticks until the entity's update() method is
#                   called.
# is_player       - Self explanatory.
# pronoun         - The pronoun used when constructing messages about the
#                   entity for display.
# observer        - The EntityContainer object which manages the entity. Used
#                   to alert the EntityContainer about events and spawn new
#                   entities.
# material        - The material the entity is physically composed of. Used to
#                   calculate hitpoints and damage reduction.
# traits          - Dictionary of traits the entity possesses. Keys are strings
#                   representing different traits and values vary depending on
#                   the trait. Traits with different degrees might be numbers
#                   while an on or off trait could be binary.
# melee_attacks   - List of dictionaries which can be used by the entity as
#                   attack templates.
# ranged_attacks  - Same as above for ranged attacks.
# ammo            - List of ways the entity can be used as ammunition.
# factions        - List of tags used by AI to react to things.
# hp_max          - Self explanatory. Property, cannot be set as it is derived
#                   from other attributes.
# hp              - Hitpoints. Remaining physical durability.
# size            - Physical size of the entity in the game world. 0 is human
#                   sized while every +/- 1 is VERY roughly 50% bigger/smaller.
# ST              - Physical mass, directly translating to maximum HP. 10 is
#                   the human average.
# HT              - Resistance to breakdown when the entity loses HP or is
#                   otherwise put under stress. 10 is average.
# dead            - Entity is deceased or otherwise completely nonfunctional
# death_checks    - How many HT rolls the entity has made to avoid death.

class Entity:
	DEFAULT_MAT = None
	DEFAULT_TEMPLATE = default_entity_attributes

	def __init__(self, name, position, is_player = False):
		self.name = name
		self._contents = []
		self._position = position
		self.container = None
		self.delay = dice.roll()
		self.is_player = is_player
		self.pronoun = "it"
		self.observer = None
		self.material = Entity.DEFAULT_MAT
		self.traits = {}
		self.melee_attacks = []
		self.ranged_attacks = []
		self.ammo = []
		self.factions = set()
		self.dead = False
		self.death_checks = 0

	@classmethod
	def from_template(cls, name, position, *templates, is_player = False):
		e = cls(name, position, is_player)

		full_template = util.deep_update(cls.DEFAULT_TEMPLATE, {})
		for template in templates:
			full_template = util.deep_update(full_template, template)

		e.display_tile = Glyph(**full_template["display"])

		for attribute in full_template["attribute"]:
			setattr(e, attribute, full_template["attribute"][attribute])

		e.root_part = construct_body(full_template["bodyplan"])
		e.traits = full_template["trait"]
		e.factions = set(full_template["factions"])
		e.melee_attacks = full_template["melee_attacks"]
		e.ranged_attacks = full_template["ranged_attacks"]
		e.ammo = full_template["ammo"]
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

	@property
	def contents(self):
		result = []
		for thing in self._contents:
			result.append(thing)
			if x := thing.contents:
				result += x
		return result

	@property
	def position(self):
		return self._position

	@position.setter
	def position(self, new):
		old = self._position
		self._position = new
		try:
			self.observer.rebucket(self, old, new)
		except AttributeError:
			pass

	@property
	def global_position(self):
		x = self
		while x.position is None:
			x = x.container
		return x.position
	
	@property
	def hp_max(self):
		return self.ST * self.material.density + self.traits.get("hp_boost", 0)

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

	def emit_sound(self, descriptor, volume = 0.0):
		e = Event(
			sound = descriptor,
			volume = volume,
			visual_priority = False,
			position = self.position,
			emitter = self
		)
		self.raise_event(e)

	def raise_event(self, event):
		if self.observer:
			self.observer.add_event(event)

	def process_event(self, event):
		return

	def spawn_effect(self, effect):
		if self.observer:
			self.observer.effects.append(effect)

	def apply_delta(self, delta):
		new = (self.position[0] + delta[0], self.position[1] + delta[1])
		self.position = new

	def move(self, game_state, direction):
		if self.position is None: return False
		new_position = (direction[0] + self.position[0], direction[1] + self.position[1])
		target_tile = game_state.get_tile(new_position[0], new_position[1])
		cost = target_tile.traversal_cost() * (1 + util.is_diag(direction) * 0.4)
		if traversible := cost >= 0:
			self.apply_delta(direction)
			if "shambler" in self.traits:
				cost *= (1 + random.random() * self.traits["shambler"])
			self.delay = cost / self.speed
		else:
			self.delay = 10
		return traversible

	def receive_attack(self, attacker, attack):
		# TODO: armor
		damage = max(0, attack.power - self.material.hardness)
		target_part = attack.target
		if target_part is None:
			target_part = self.root_part.get_weighted_random_part()
		# Damage type/target part multipliers
		multiplier = util.calculate_damage_multiplier(attack.damage_type, target_part, self.traits.get('injury_tolerance', None))
		damage = math.floor(damage * multiplier)
		uncapped_damage = damage
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
		target.position = self.global_position
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
		self.buckets = defaultdict(list)
		self._events = []
		self.effects = []

	def add_entity(self, *entities):
		for e in entities:
			self.contents.append(e)
			e.observer = self
			self.buckets[e.global_position].append(e)
		self.sort_entities()

	def add_event(self, event):
		self._events.append(event)
		if event.position is None:
			return
		for e in self.contents:
			e.process_event(event)

	# TODO: Make insertions keep entities sorted by size
	# TODO: Make sort preserving insertion utility function
	def rebucket(self, entity, old, new):
		self.buckets[old].remove(entity)
		self.buckets[new].append(entity)

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
		expired = []
		for effect in self.effects:
			effect.age += 1
			if effect.age > effect.duration:
				expired.append(effect)
		for effect in expired:
			self.effects.remove(effect)

	def get_within_radius(self, e, radius = 1, exclude_self = True):
		ex, ey = e.global_position
		discovered = []
		for x in range(ex - radius, ex + radius + 1):
			for y in range(ey - radius, ey + radius + 1):
				discovered += self.buckets[(x, y)]
		if exclude_self and e in discovered:
			discovered.remove(e)
		return discovered

	def pop_events(self):
		e = self._events.copy()
		self._events = []
		return e

	def build_grid(self):
		grid = {}
		for e in sorted(self.contents, key = lambda x: x.size):
			if e.position is not None:
				grid[e.position] = e.display_tile
		for e in self.effects:
			grid[e.position] = e.sample()
		return grid

	def build_grid_with_visibility(self, visible):
		grid = {}
		for e in sorted(self.contents, key = lambda x: x.size):
			if e.position in visible:
				grid[e.position] = e.display_tile
		for e in self.effects:
			grid[e.position] = e.sample()
		return grid