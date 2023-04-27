import math
import random
from copy import deepcopy

def bresenham_line(x0, y0, x1, y1):
	dx = abs(x1 - x0)
	dy = abs(y1 - y0)

	if steep := dy > dx:
		dx, dy = dy, dx
		x0, y0 = y0, x0
		x1, y1 = y1, x1

	x, y = x0, y0
	err = 2 * dy - dx
	x_sign = 1 if x0 < x1 else -1
	y_sign = 1 if y0 < y1 else -1

	points = []
	for i in range(dx + 1):
		points.append((y, x) if steep else (x, y))
		if err > 0:
			y += y_sign
			err += 2 * (dy - dx)
		else:
			err += 2 * dy

		x += x_sign

	return points

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