from enum import Enum

class State(Enum):
	SOLID = 1
	LIQUID = 2
	GAS = 3
	PHANTASMAL = 4
	VOID = 5

def string_to_state(state):
	if state == "solid":
		return State.SOLID
	elif state == "liquid":
		return State.LIQUID
	elif state == "gas":
		return State.GAS
	elif state == "phantasmal":
		return State.PHANTASMAL
	else:
		return State.VOID

class Mood(Enum):
	NEUTRAL = 1
	EXCITED = 2
	BASHFUL = 3

class Mode(Enum): # Get rid of this garbage ASAP
	MAIN = 1
	MENU = 2

class DamageType(Enum):
	BASH = "bash"
	CUT = "cut"
	PIERCE = "pierce"
	BURN = "burn"

class BodyType(Enum):
	HUMANOID = "humanoid"

class PartFlag(Enum):
	CRIPPLED = "crippled"
	BALANCER = "balancer"
	WALKER = "walker"
	LEVER = "lever"
	GRASPER = "grasper"
	SECONDARY_GRASPER = "secondary_grasper"
	MIND = "mind"
	SIGHT = "sight"
	VITALS = "vitals"
	CUTTABLE = "cuttable"
	STRIKER = "striker"
	SIMPLE = "simple"

class Event():
	def __init__(self, visual = None, sound = None, volume = 1.0):
		self.visual = visual
		self.sound = sound
		self.volume = volume

class Attack():
	def __init__(self, power, damage_type, accuracy, target = None, weapon = None, flags = ()):
		self.power = power
		self.damage_type = damage_type
		self.accuracy = accuracy
		self.target = target
		self.weapon = weapon
		self.flags = flags

	def __str__(self):
		return "Attack: power " + str(self.power) + " acc " + str(self.accuracy)

class Material:
	def __init__(self, name, state, density, hardness, opacity, texture, fg, bg, floor_color, smooth = False):
		self.name = name
		self.state = state
		self.density = density
		self.hardness = hardness
		self.opacity = opacity
		self.texture = texture
		self.fg = fg
		self.bg = bg
		self.floor_color = floor_color
		self.smooth = smooth

class Glyph:
	def __init__(self, character, fg = (255, 255, 255), bg = (0, 0, 0)):
		self.character = character
		self.fg = tuple(fg)
		self.bg = tuple(bg)

	# Gets the actual integer representing the character's position on the code page
	@property
	def code(self):
		if type(self.character) == int:
			return self.character
		return ord(self.character)

class Language:
	def __init__(self, vocabulary, interjections, sentenceMin, sentenceMax, interjectionFrequency):
		self.vocabulary = vocabulary
		self.interjections = interjections
		self.sentenceMin = sentenceMin
		self.sentenceMax = sentenceMax
		self.interjectionFrequency = interjectionFrequency