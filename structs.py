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

class Mode(Enum):
	MAIN = 1
	MENU = 2

class Material:
	def __init__(self, name, state, density, hardness, opacity, texture):
		self.name = name
		self.state = state
		self.density = density
		self.hardness = hardness
		self.opacity = opacity
		self.texture = texture

class Language:
	def __init__(self, vocabulary, interjections, sentenceMin, sentenceMax, interjectionFrequency):
		self.vocabulary = vocabulary
		self.interjections = interjections
		self.sentenceMin = sentenceMin
		self.sentenceMax = sentenceMax
		self.interjectionFrequency = interjectionFrequency