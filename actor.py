import random
import math
from structs import *
from entity import Entity
from tile import TileFeature
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
		# Temporary
		self.skills = {'rifle': 10, 'innate_attack': 15}
		self._goals = []
		# Temporary
		self._goals.append((GoalType.SURVIVE,))
		self.hostiles = set()
		self.known_locations = {}

	@property
	def speed(self):
		s = (self.DX + self.HT) / 4 + self.traits.get("speed_boost", 0)
		if self.hp < self.hp_max / 3: s //= 2
		return s

	def update(self):
		if self.dead or self.awareness == Awareness.UNCONSCIOUS:
			self.delay += 1000
			return
		if self.hp <= 0:
			if dice.roll() > self.HT:
				self.awareness = Awareness.UNCONSCIOUS
				self.delay += 1000
				self.display_tile.bg = (0, 255, 255)
				self.raise_event(Event(visual = f"[c]The {self.name} faints!"))
				return
		action = self.think()
		self.perform_action(action)

	def process_goal(self, goal):
		match goal:
			# SURVIVE
			# -Check for visible hostile entities
			# -If any of them are conscious, attack them
			# -Otherwise, finish off the stragglers (everyone is quite ruthless right now)
			# -Otherwise, mill around
			case GoalType.SURVIVE,:
				seen = set(self.search_for_entities())
				for e in seen:
					if not self.factions & e.factions:
						self.hostiles.add(e)
				visible_hostiles = list(filter(lambda x: not x.dead, seen & self.hostiles))
				visible_hostiles.sort(key = lambda x: util.true_distance(x.position, self.position))
				if not visible_hostiles:
					if random.randint(1, 5) != 1:
						return (goal, (ActionType.WAIT,))
					return (goal, (ActionType.MOVE, random.choice(util.MOORE_NEIGHBORHOOD)))
				conscious_hostiles = list(filter(lambda x: x.awareness == Awareness.ALERT, visible_hostiles))
				if len(visible_hostiles) > len(conscious_hostiles) > 0:
					return ((GoalType.SURVIVE,), (GoalType.ATTACK, conscious_hostiles[0]))
				return ((GoalType.SURVIVE,), (GoalType.ATTACK, visible_hostiles[0]))
			# KILL
			# -Attack if target is alive
			# Not used for normal combat because actor will ignore all other targets
			# even if they pose a more immediate threat.
			case GoalType.KILL, target:
				if target.dead:
					return ()
				return (goal, (GoalType.ATTACK, target))
			# ATTACK
			# -Try to shoot target
			# -Failing that, try to strike target in melee
			# -Failing that, approach target
			case GoalType.ATTACK, target:
				if self.get_ranged_attack_template():
					return ((ActionType.SHOOT, target),)
				melee_template = self.get_melee_attack_template()
				dist = util.manhattan_dist(self.position, target.position)
				# TODO: REWORK SO ATTACKER CAN STEP BEFORE STRIKING
				if dist in melee_template['reach']:
					return ((ActionType.STRIKE, target),)
				if dist > max(melee_template['reach']):
					return ((GoalType.APPROACH, target.position),)
				return ((GoalType.RETREAT, target.position),)
			# APPROACH / RETREAT
			# -Move towards / away from target
			case GoalType.APPROACH, target:
				direction = self.path_towards(target, 1)
				return ((ActionType.MOVE, direction),)
			case GoalType.RETREAT, target:
				direction = util.dir_between(self.position, target)
				return ((ActionType.MOVE, direction),)
			# INVESTIGATE
			# -If target is visible abort
			# -otherwise approach
			case GoalType.INVESTIGATE, target:
				if self.traits.get('immobile', False):
					return ()
				if self.observer.tiles.visibility_between(self.position, target) > .1:
					return ()
				return (goal, (GoalType.APPROACH, target))
		raise Exception(f"{goal} not matched!")

	def process_event(self, event):
		# Actors magically know if a sound was created by an enemy
		# TODO: Figure out how to encode decision making info on sounds
		if event.emitter is not None and (event.emitter.factions & self.factions):
			return
		dist_steps = math.log2(max(util.true_distance(self.position, event.position), 0.5))
		modifier = math.trunc(event.volume - dist_steps)
		r = dice.roll()
		p = self.IQ + modifier
		if r > p: # TODO: Use perception instead of IQ
			return
		goal = self._goals[-1]
		match goal:
			case GoalType.SURVIVE,:
				if self.traits.get('bestial', False):
					self._goals.append((GoalType.INVESTIGATE, event.position))
					self._goals.append((ActionType.ALERT,))

	def perform_action(self, action):
		match action:
			case ActionType.WAIT,:
				self.wait()
			case ActionType.MOVE, direction:
				if self.traits.get('immobile', False):
					self.wait()
				else:
					self.move(direction)
			case ActionType.STRIKE, target:
				self.send_attack(target)
				template = self.get_melee_attack_template()
				if util.manhattan_dist(self.position, target.position) < max(template['reach']):
					self.step_from(target)
			case ActionType.SHOOT, target:
				template = self.get_ranged_attack_template()
				self.shoot(template, target)
			case ActionType.ALERT,:
				sound_profile = self.traits.get('sound_type', None)
				if sound_profile == 'hunter':
					self.emit_sound('[c]Hiss!', 1.0)
			case _:
				raise Exception(f"{action} not matched!")

	def think(self):
		goal = self._goals.pop()
		if type(goal[0]) == ActionType:
			return goal
		result = self.process_goal(goal)
		self._goals += result
		return self.think()

	def get_held_entities(self):
		result = []
		hands = self.root_part.get_parts_with_trait(PartFlag.GRASPER)
		for hand in hands:
			if hand.held:
				result.append([hand, hand.held])
		return result

	def get_weapon(self):
		held = self.get_held_entities()
		if not held: return None
		return held[0][1]

	def search_for_entities(self):
		local_entities = self.observer.contents
		visible_entities = list(filter(
			lambda x: self.observer.tiles.visibility_between(self.position, x.global_position) > 0 and x.position is not None,
			local_entities))
		visible_entities.sort(key = lambda x: util.manhattan_dist(self.position, x.global_position))
		return visible_entities

	def get_melee_attack_template(self):
		weapon = self.get_weapon()
		if weapon and weapon.melee_attacks:
			return weapon.melee_attacks[0]
		return self.melee_attacks[0]

	def get_ranged_attack_template(self):
		if self.ranged_attacks:
			return self.ranged_attacks[0]
		weapon = self.get_weapon()
		if weapon and weapon.ranged_attacks:
			return weapon.ranged_attacks[0]
		return None

	def send_attack(self, target, target_part = None):
		# TODO: This should be passed into the function
		attack_template = self.get_melee_attack_template()
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
		self.emit_sound('Bang!', 8.0)
		vector = util.tup_normalize(util.tup_sub(target.position, self.position))
		effect_position = util.tup_add(self.position, vector)
		self.spawn_effect(Effect(effect_position, ['\xB1', '\xB2'], (255, 255, 0), max(2, attack_template['rate_of_fire'] // 2)))
		if (margin := (effective_skill - roll)) < 0:
			return # TODO: Accidental targets / collateral damage
		shots = 1 + (margin // attack_template['recoil'])
		attack = Attack.from_template(attack_template, target_part)
		for i in range(shots):
			target.receive_attack(self, attack)
		self.delay += 10

	def step_from(self, target):
		direction = util.dir_between(self.position, target.position)
		if direction == (0, 0): direction = random.choice(util.MOORE_NEIGHBORHOOD)
		if 0 <= self.cost_to(direction) <= 10:
			self.apply_delta(direction)

	def receive_attack(self, attacker, attack):
		if self.dodge(attacker):
			attack_descriptor = f"{attacker.name} attacks the {self.name}, but {self.pronoun} dodges!"
			self.raise_event(Event(visual = attack_descriptor))
			return
		if super().receive_attack(attacker, attack) > 0:
			current_tile = self.observer.tiles.get_tile(*self.position)
			current_tile.add_feature(
				TileFeature(
					name = 'Bloodstain',
					z_index = 0,
					fg_overwrite = True,
					char_overwrite = True,
					symbol = Glyph('~', (255, 0, 0))))

		if self.dead: return

		while self.hp <= self.hp_max * self.death_checks * -1:
			self.death_checks += 1
			if dice.roll() > self.HT or self.death_checks >= 5:
				self.dead = True
				self.awareness = Awareness.DEAD
				self.display_tile.fg = (150, 150, 150)
				self.display_tile.bg = (200, 0, 0)
				self.raise_event(Event(visual = f"[m]The {self.name} is struck down."))
				self.name += " corpse"
				return
			self.raise_event(Event(visual = f"The {self.name} manages to evade death!"))

	def wait(self):
		if self.aim_target is not None:
			self.aim_turns += 1
		self.delay += 10

	def dodge(self, attacker):
		if self.awareness != Awareness.ALERT:
			return False
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
		if self.dodge(picker):
			self.raise_event(Event(visual = f"The {self.name} dodges the grab!"))
			return False
		return picker.ST > self.ST

	def path_towards(self, target, goal_distance):
		distance = util.manhattan_dist(self.position, target)
		if distance <= goal_distance:
			return None
		next_square = self.observer.tiles.next_step_towards(self.position, target)
		return util.tup_sub(next_square, self.position)