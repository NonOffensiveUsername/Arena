import math
import random
from copy import copy

MOORE_NEIGHBORHOOD = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
MOORE_NEIGHBORHOOD_INCLUSIVE = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 0), (0, 1), (1, -1), (1, 0), (1, 1))
NEUMANN_NEIGHBORHOOD = ((-1, 0), (0, -1), (0, 1), (1, 0))
NEUMANN_NEIGHBORHOOD_INCLUSIVE = ((-1, 0), (0, -1), (0, 0), (0, 1), (1, 0))

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

def manhattan_dist(a, b):
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

def color_mul(color, m):
	return (int(color[0] * m), int(color[1] * m), int(color[2] * m))

# Takes two dictionaries and returns a recursively updated copy
def deep_update(a, b):
	new_dict = copy(a)
	for x, y in b.items():
		if type(y) == dict:
			new_dict[x] = deep_update(a.get(x, {}), y)
			continue
		new_dict[x] = y
	return new_dict

def cut(string, start, stop):
	return string[0:start] + string[stop:]