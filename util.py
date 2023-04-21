import math
import random
from copy import deepcopy

# Given two points, return a list of points representing a line between them
# TODO: Heavy cleanup, more thorough testing, simplification
#def get_line(x1, y1, x2, y2):
#
#	# Handling the special case of vertical lines
#	# TODO: fix this, can currently see through walls directly north
#	if x1 == x2:
#		result = []
#		for i in range(y1, y2 + 1):
#			result.append(Vec2(x1, i))
#		return result
#
#	slope = (y2 - y1) / (x2 - x1)
#	x_offset, y_offset = x1, y1
#	x1, y1 = 0, 0
#	x2 -= x_offset
#	y2 -= y_offset
#
#	# Translate and reflect the coordinates so the line passes through 0,0 and has a slope between 0 and 1
#
#	vertical_reflect = 1
#	if y2 < y1:
#		vertical_reflect = -1
#		y2 *= -1
#		slope *= -1
#
#	horizontal_reflect = 1
#	if x2 < x1:
#		horizontal_reflect = -1
#		x2 *= -1
#		slope *= -1
#
#	swap_coords = False
#
#	if slope > 1: 
#		swap_coords = True
#		x1, y1 = y1, x1
#		x2, y2 = y2, x2
#		slope = (y2 - y1) / (x2 - x1)
#
#	result = []
#
#	for i in range(0, x2 + 1):
#		x = i
#		y = round_half_down(i * slope)
#		if swap_coords: x, y = y, x
#		y *= vertical_reflect
#		x *= horizontal_reflect
#		x += x_offset
#		y += y_offset
#		result.append(Vec2(x, y))
#
#	return result

# Rounds to nearest integer, rounds ties down
def round_half_down(num):
	return math.ceil(num -.5)

def dist_between(a, b):
	return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

def dir_between(a, b):
	if type(a) == tuple and type(b) == tuple:
		x = a[0] - b[0]
		if x != 0:
			x //= abs(x)
		y = a[1] - b[1]
		if y != 0:
			y //= abs(y)
		return (x, y)
	return None

def rand_dir():
	return random.choice(((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 0), (0, 1), (1, -1), (1, 0), (1, 1)))

def tup_add(a, b):
	return (a[0] + b[0], a[1] + b[1])

def is_diag(vec):
	return vec[0] != 0 and vec[1] != 0

# Takes two dictionaries as arguments
# Copies a and overwrites b onto the copy
# The new dict is returned
def dict_overwrite(a, b):
	new_dict = deepcopy(a)
	for k in new_dict:
		if k in b:
			if type(b[k]) != dict:
				new_dict[k] = b[k]
			else:
				new_dict[k] = dict_overwrite(new_dict[k], b[k])
	return new_dict

#if __name__ == "__main__":
#	a = {
#		"test": 5,
#		"test2": 7,
#		"test3": {
#			"woag": 99,
#			"woazers": 3
#		}
#	}
#	b = {
#		"test2": 9,
#		"test3": {
#			"woazers": 2
#		}
#	}
#	c = dict_overwrite(a, b)
#	print(c)