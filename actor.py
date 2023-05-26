import random
import math
from structs import *
from entity import Entity
import dice
import util

default_actor_attributes = {
	"attribute": {
		"size": 0,
		"ST": 10,
		"HT": 10,
		"DX": 10,
		"IQ": 10,
	},
	"trait": {},
	"bodyplan": BodyType.HUMANOID,
	"use_cases": [],
	"factions": [],
	"melee_attacks": [
		{
			"skill": "brawling",
			"quality": 0,
			"muscle": "thrust",
			"damage_type": "bash",
			"damage_mod": -2,
			"ST_requirement": -1,
			"reach": [0, 1],
		}
	],
	"ranged_attacks": [],
	"ammo": [],
	"display": {
		"character": 1,
		"fg": [255, 255, 255],
		"bg": [0, 0, 0],
	}
}

class Actor(Entity):
	DEFAULT_TEMPLATE = default_actor_attributes

	def __init__(self, name, position, is_player = False):
		super().__init__(name, position, is_player)
		self.awareness = Awareness.ALERT
		self.aim_target = None
		self.aim_turns = 0
		self.skills = {'rifle': 10}
		self.goal = None

	@property
	def speed(self):
		return (self.DX + self.HT) / 4 + self.traits.get("speed_boost", 0)

	def get_held_entities(self):
		result = []
		hands = self.root_part.get_parts_with_trait(PartFlag.GRASPER)
		for hand in hands:
			if hand.held:
				result.append([hand, hand.held])
		return result

	def search_for_entities(self, game_state):
		local_entities = self.observer.contents
		visible_entities = list(filter(
			lambda x: game_state.visibility_between(self.position, x.global_position) > 0,
			local_entities))
		visible_entities.sort(key = lambda x: util.manhattan_dist(self.position, x.global_position))
		return visible_entities

	def send_attack(self, target, target_part = None):
		# This all sucks, attack should be selected outside this function
		# Specifically, this function should ONLY handle building the attack object
		# and triggering the targets receiver method.
		primary_hand = None
		if hands := self.root_part.get_parts_with_trait(PartFlag.GRASPER):
			primary_hand = hands[0]
		weapon = None
		if primary_hand and primary_hand.held:
			weapon = primary_hand.held
		attack_template = self.melee_attacks[0]
		if weapon:
			attack_template = weapon.melee_attacks[0]
		# /suckage
		acc = dice.roll()
		swing = attack_template["muscle"] == "swing"
		effective_ST = self.ST + max(2, self.ST - 7) if swing else self.ST
		damage_dice = max((effective_ST - 3) // 8, 1)
		damage_mod = (effective_ST - 3) % 8 // 2 - 1 if effective_ST >= 11 else (effective_ST + 1) // 2 - 7
		power = dice.roll(damage_dice, mod = damage_mod)
		damage_type = attack_template["damage_type"]
		attack = Attack(power, damage_type, target = target_part)
		target.receive_attack(self, attack)
		self.delay = 10

	def shoot(self, attack_template, target, target_part = None):
		effective_skill = self.skills[attack_template['skill']]
		effective_skill += target.size
		if target_part:
			effective_skill += target_part.size
		distance = util.true_distance(self.position, target.position)
		if distance > 0:
			dist_mod = max(int(math.log(distance / 2, 1.5)), 0)
			effective_skill += dist_mod
		else:
			effective_skill -= attack_template['bulk']
		if self.aim_target is target:
			effective_skill += (attack_template['accuracy'] * (self.aim_turns > 0)) + max(0, self.aim_turns - 1)
		# effective_skill += <light level>
		roll = dice.roll()
		self.raise_event(Event(sound = "Bang!", visual_priority = False))
		vector = util.tup_normalize(util.tup_sub(target.position, self.position))
		effect_position = util.tup_add(self.position, vector)
		self.spawn_effect(Effect(effect_position, ['\xB1', '\xB2'], (255, 255, 0), 2))
		if roll > effective_skill:
			return # TODO: Accidental targets / collateral damage
		attack = Attack.from_template(attack_template, target_part)
		target.receive_attack(self, attack)
		self.delay += 10

	def receive_attack(self, attacker, attack):
		if self.dodge():
			attack_descriptor = f"{attacker.name} attacks the {self.name}, but {self.pronoun} dodges!"
			self.raise_event(Event(visual = attack_descriptor))
			return
		super().receive_attack(attacker, attack)

		while self.hp <= self.hp_max * self.death_checks * -1:
			self.death_checks += 1
			if dice.roll() > self.HT:
				self.dead = True
				self.display_tile.fg = (150, 150, 150)
				self.display_tile.bg = (200, 0, 0)
				self.raise_event(Event(visual = f"[m]The {self.name} is struck down."))
				return
			self.raise_event(Event(visual = f"The {self.name} manages to evade death!"))

	def wait(self):
		if self.aim_target is not None:
			self.aim_turns += 1
		self.delay += 10

	def dodge(self):
		dodge_target = int(self.speed) + 3
		r = dice.roll()
		return r <= dodge_target

	def get(self, target):
		if target is self:
			return False # Entities probably shouldn't be their own container
		if not (hands := self.root_part.get_parts_with_trait(PartFlag.GRASPER)):
			return False
		no_hand_available = True
		used_hand = None
		for hand in hands:
			if hand.held is None:
				no_hand_available = False
				used_hand = hand
				break
		if no_hand_available:
			return False
		if not target.can_be_picked_up(self):
			return False
		self.insert(target)
		used_hand.held = target
		self.delay += 10
		return True

	def drop(self, target):
		target.container.remove(target)
		self.delay += 10 # TODO: held items drop easier

	def can_be_picked_up(self, picker):
		if self.dodge():
			self.raise_event(Event(visual = f"The {self.name} dodges the grab!"))
			return False
		return picker.ST > self.ST

	def path_towards(self, game_state, target, goal_distance):
		distance = util.manhattan_dist(self.position, target.position)
		if distance <= goal_distance:
			return None
		next_square = game_state.next_step_towards(self.position, target.position)
		return util.tup_sub(next_square, self.position)

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
		direction = self.path_towards(game_state, self.target, 1)
		if direction is not None:
			self.move(game_state, direction)
			return
		self.send_attack(self.target)

class TetheredWanderer(Actor):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.target_position = self.position

	def update(self, game_state):
		if self.hp <= 0 or self.position is None:
			self.delay = 1000
			return
		dist_from_target = util.manhattan_dist(self.position, self.target_position)
		if dist_from_target > 0:
			next_square = game_state.next_step_towards(self.position, self.target_position)
			direction = (next_square[0] - self.position[0], next_square[1] - self.position[1])
			self.move(game_state, direction)
			return
		if random.randint(0, 9) < 2:
			self.target_position = random.choice(self.tether)
		self.delay = 10

class Monster(Actor):
	def update(self, game_state):
		if self.dead or self.awareness != Awareness.ALERT:
			self.delay = 100
			return
		if self.goal is None:
			visible_entities = self.search_for_entities(game_state)
			for entity in visible_entities:
				if type(entity) != Entity and "monster" not in entity.factions:
					self.goal = entity
					break
		if self.goal is None:
			self.delay = 10
			if random.randint(0, 9) < 2:
				self.move(game_state, random.choice(util.MOORE_NEIGHBORHOOD))
			return
		if (direction := self.path_towards(game_state, self.goal, 1)) is not None:
			self.move(game_state, direction)
			return
		
		self.delay = 10

class Soldier(Actor):
	def update(self, game_state):
		if self.goal and self.goal.dead:
			self.goal = None
		if self.dead or self.awareness != Awareness.ALERT:
			self.delay = 100
			return
		visible_entities = self.search_for_entities(game_state)
		for entity in visible_entities:
			if type(entity) != Entity and "monster" in entity.factions and not entity.dead:
				self.goal = entity
				break
		if self.goal is None:
			self.delay = 10
			if random.randint(0, 9) < 1:
				self.move(game_state, random.choice(util.MOORE_NEIGHBORHOOD))
			return
		weapon = self.get_held_entities()[0][1]
		attack_template = weapon.ranged_attacks[0]
		self.shoot(attack_template, self.goal)