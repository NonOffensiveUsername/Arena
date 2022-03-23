import random
from structs import Language, Mood

class BabbleGenerator:
	def __init__(self, language):
		self.language = language

	def generate(self, mood, sentences):
		out_string = ""
		for i in range(0, sentences):
			if random.random() < self.language.interjectionFrequency:
				out_string += "*" + random.choice(self.language.interjections).capitalize() + '*. '
			else:
				buffer_string = ''
				num_words = random.randrange(self.language.sentenceMin, self.language.sentenceMax)
				for e in range(0, num_words):
					buffer_string += random.choice(self.language.vocabulary) + ' '
				buffer_string = buffer_string.strip().capitalize()
				if mood == Mood.EXCITED and random.random() < .5:
					out_string += buffer_string + '! '
				elif mood == Mood.BASHFUL and random.random() < .5:
					out_string += buffer_string + '... '
				else:
					out_string += buffer_string + '. '
		return out_string

# Test code
feloid_vocab = [
	'mecaco',
	'pledoo',
	'sicheetoo',
	'pidge',
	'po',
	'gil',
	'mon',
	'coloco',
	'fip',
	'fepeeto',
	'cat',
	'tudge'
]
feloid_interjections = [
	'mrow',
	'meow',
	'purr',
	'yeow',
	'hiss'
]
feloid = Language(feloid_vocab, feloid_interjections, 2, 4, .2)
babbler = BabbleGenerator(feloid)
print(babbler.generate(Mood.NEUTRAL, 5))
print(babbler.generate(Mood.EXCITED, 5))
print(babbler.generate(Mood.BASHFUL, 5))