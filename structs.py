from enum import Enum
import re
import util

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
	# Volume is a logarithmic unit. An event with volume 0 can be heard automatically at a distance of 1 yard.
	# Each +1 volume doubles this distance, each -1 halves it.
	def __init__(self, visual = None, sound = None, volume = 0.0, visual_priority = True):
		self.visual = visual
		self.sound = sound
		self.volume = volume
		self.visual_priority = visual_priority

	@property
	def primary(self):
		return self.visual if self.visual_priority else self.sound

	@property
	def sound_glyph(self):
		char = "!" # TODO: change character based on volume
		return Glyph(char, (255, 255, 0))

class Attack:
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

	def __repr__(self):
		if type(self.character) == int:
			return f"Glyph({self.character}, fg = {self.fg}, bg = {self.bg})"
		return f"Glyph('{self.character}', fg = {self.fg}, bg = {self.bg})"

	# Gets the actual integer representing the character's position on the code page
	@property
	def code(self):
		if type(self.character) == int:
			return self.character
		return ord(self.character)

class GlyphString(list):
	# Regex that matches triplets of comma seperated integers in brackets or
	# a single lowercase letter in brackets. Integer triplets are RPG values
	# and single character tags are shortcuts for certain triplets. A tag
	# changes all the text that follows until a new tag overwrites it.
	# Examples: [255, 255, 255] [0,128,255] [r] [b]
	tag_definition = re.compile(r"\[\d+, ?\d+, ?\d+\]|\[[a-z]\]")

	color_shortcuts = {
		'b': (0, 0, 0),			# Black
		'w': (255, 255, 255),	# White
		'r': (255, 0, 0),		# Red
		'g': (0, 255, 0),		# Green
		'b': (0, 0, 255),		# Black
		'y': (255, 255, 0),		# Yellow
		'm': (255, 0, 255),		# Magenta
		'c': (0, 255, 255),		# Cyan
	}

	def __init__(self, raw):
		self._raw = raw
		self.convert()

	# Turn marked up string into glyph objects
	def convert(self):
		self.clear()
		pure_string = self._raw # Raw with tags stripped out
		tags = [(0, (255, 255, 255))] # Implicit white tag at start
		while tag := GlyphString.tag_definition.search(pure_string):
			start, end = tag.start(), tag.end()
			# Extract content of tag without whitespace or brackets
			tag_inner = tag.group()[1:-1].replace(' ', '')
			# Parse tag content into an rgb tuple
			tag_color = None
			if len(tag_inner) == 1:
				tag_color = GlyphString.color_shortcuts[tag_inner]
			else:
				tag_color = tuple(map(int, tag_inner.split(',')))
			tags.append((start, tag_color))
			pure_string = util.cut(pure_string, start, end)

		color = (255, 255, 255)
		for i in range(len(pure_string)):
			while tags and tags[0][0] == i:
				color = tags.pop(0)[1]
			self.append(Glyph(pure_string[i], fg = color))

	@property
	def raw(self):
		return self._raw

	@raw.setter
	def raw(self, value):
		self._raw = value
		self.convert()

class Language:
	def __init__(self, vocabulary, interjections, sentenceMin, sentenceMax, interjectionFrequency):
		self.vocabulary = vocabulary
		self.interjections = interjections
		self.sentenceMin = sentenceMin
		self.sentenceMax = sentenceMax
		self.interjectionFrequency = interjectionFrequency