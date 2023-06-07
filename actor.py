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

	def update(self, game_state):
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
		action = self.think(game_state)
		self.perform_action(action, game_state)

	def process_goal(self, goal, game_state):
		match goal:
			# Current survive behavior:
			# -Check for visible hostile entities
			# -Try to kill the closest one
			# -If none are visible, stay still
			case GoalType.SURVIVE,:
				seen = set(self.search_for_entities(game_state))
				for e in seen:
					if ('monster' in self.factions) != ('monster' in e.factions):
						self.hostiles.add(e)
				visible_hostiles = list(filter(lambda x: not x.dead, seen & self.hostiles))
				visible_hostiles.sort(key = lambda x: util.manhattan_dist(x.position, self.position))
				if not visible_hostiles:
					return (goal, (ActionType.WAIT,))
				return ((GoalType.SURVIVE,), (GoalType.KILL, visible_hostiles[0]))
			# Current kill behavior:
			# -Shoot if possible
			# -Otherwise melee attack if possible
			# -Otherwise move towards target
			case GoalType.KILL, target:
				if target.dead:
					return ()
				if self.get_ranged_attack_template():
					return (goal, (ActionType.SHOOT, target))
				melee_template = self.get_melee_attack_template()
				dist = util.manhattan_dist(self.position, target.position)
				if dist in melee_template['reach']:
					return (goal, (ActionType.STRIKE, target))
				return (goal, (GoalType.APPROACH, target.position))
			# Current approach behavior:
			# -Move towards target
			case GoalType.APPROACH, target:
				direction = self.path_towards(game_state, target, 1)
				return ((ActionType.MOVE, direction),)
			# Current investigate behavior:
			# -If target is visible abort
			# -otherwise approach
			case GoalType.INVESTIGATE, target:
				if self.traits.get('immobile', False):
					return ()
				if game_state.visibility_between(self.position, target) > .1:
					return ()
				return (goal, (GoalType.APPROACH, target))
		raise Exception(f"{goal} not matched!")

	def process_event(self, event):
		dist_steps = math.log2(max(util.true_distance(self.position, event.position), 0.5))
		modifier = math.trunc(event.volume - dist_steps)
		r = dice.roll()
		p = self.IQ + modifier
		if r > p: # TODO: Use perception instead of IQ
			return
		goal = self._goals[-1]
		match goal:
			case GoalType.SURVIVE,:
				self._goals.append((GoalType.INVESTIGATE, event.position))
		#if self._goals[-1][0] != ActionType.ALERT:
		#	self._goals.append((ActionType.ALERT,))

	def perform_action(self, action, game_state):
		match action:
			case ActionType.WAIT,:
				self.wait()
			case ActionType.MOVE, direction:
				if self.traits.get('immobile', False):
					self.wait()
				else:
					self.move(game_state, direction)
			case ActionType.STRIKE, target:
				self.send_attack(target)
			case ActionType.SHOOT, target:
				template = self.get_ranged_attack_template()
				self.shoot(template, target)
			case ActionType.ALERT,:
				sound_profile = self.traits.get('sound_type', None)
				if sound_profile == 'hunter':
					self.raise_event(Event(sound = 'The hunter hisses!', visual_priority = False, volume = 1.0, position = self.position))
			case _:
				raise Exception(f"{action} not matched!")

	def think(self, game_state):
		goal = self._goals.pop()
		if type(goal[0]) == ActionType:
			return goal
		result = self.process_goal(goal, game_state)
		self._goals += result
		return self.think(game_state)

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

	def search_for_entities(self, game_state):
		local_entities = self.observer.contents
		visible_entities = list(filter(
			lambda x: game_state.visibility_between(self.position, x.global_position) > 0 and x.position is not None,
			local_entities))
		visible_entities.sort(key = lambda x: util.manhattan_dist(self.position, x.global_position))
		return visible_entities

	def get_melee_attack_template(self):
		weapon = self.get_weapon()
		if weapon and weapon.melee_attacks:
			return weaponn.melee_attacks[0]
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
		self.raise_event(Event(sound = "Bang!", visual_priority = False, volume = 8.0, position = self.position))
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

	def receive_attack(self, attacker, attack):
		if self.dodge():
			attack_descriptor = f"{attacker.name} attacks the {self.name}, but {self.pronoun} dodges!"
			self.raise_event(Event(visual = attack_descriptor))
			return
		super().receive_attack(attacker, attack)

		while self.hp <= self.hp_max * self.death_checks * -1:
			self.death_checks += 1
			if dice.roll() > self.HT or self.death_checks >= 5:
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
		distance = util.manhattan_dist(self.position, target)
		if distance <= goal_distance:
			return None
		next_square = game_state.next_step_towards(self.position, target)
		return util.tup_sub(next_square, self.position)