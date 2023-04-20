from random import randint

def roll(num = 3, sides = 6, mod = 0):
	return sum([randint(1, sides) for i in range(num)]) + mod