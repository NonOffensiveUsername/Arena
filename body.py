import math
import random
from structs import BodyType, PartFlag

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

def construct_body(bodyplan):
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

		return root
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

		return root
	else:
		return BodyPart("Mass", 0, traits = [PartFlag.SIMPLE])