from structs import Glyph, GlyphString

class Widget:
	def __init__(self, x, y, w, h):
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.buffer = {}
		self.draw()

	def draw(self):
		self.buffer = {}

	def fill(self, char = ' '):
		for i in range(self.w):
			for e in range(self.h):
				self.buffer[(i+self.x, e+self.y)] = Glyph(char)

	def frame(self):
		for i in range(self.x+1, self.x+self.w):
			self.buffer[(i, self.y)] = Glyph(205)
			self.buffer[(i, self.y+self.h)] = Glyph(205)
		for e in range(self.y+1, self.y+self.h):
			self.buffer[(self.x, e)] = Glyph(179)
			self.buffer[(self.x+self.w, e)] = Glyph(179)
		self.buffer[(self.x, self.y)] = Glyph(213)
		self.buffer[(self.x+self.w, self.y)] = Glyph(184)
		self.buffer[(self.x, self.y+self.h)] = Glyph(212)
		self.buffer[(self.x+self.w, self.y+self.h)] = Glyph(190)

	def print(self, string, x, y, wrap = True):
		offset = 0
		glyphs = GlyphString(string)
		for glyph in glyphs:
			if wrap:
				position = (self.x + x + (offset % self.w), self.y + y + (offset // self.w))
				self.buffer[position] = glyph
			else:
				position = (self.x + x + offset, self.y + y)
				self.buffer[position] = glyph
				if offset + 1 > self.w: break
			offset += 1
			if offset // self.w > self.h: break

	def draw_glyph_sequence(self, glyphs, x, y, wrap = True):
		offset = 0
		for glyph in glyphs:
			if wrap:
				position = (self.x + x + (offset % self.w), self.y + y + (offset // self.w))
				self.buffer[position] = glyph
			else:
				position = (self.x + x + offset, self.y + y)
				self.buffer[position] = glyph
				if offset + 1 > self.w: break
			offset += 1
			if offset // self.w > self.h: break

class SingleSelectMenu(Widget):
	def __init__(self, x, y, w, h, title, options, pointer = 0):
		self.title = title
		self.options = options
		self.pointer = pointer
		super().__init__(x, y, w, h)

	def draw(self):
		self.fill()
		self.frame()
		self.print(self.title, 0, 0, wrap = False)
		for i in range(len(self.options)):
			arrow = '\x1a'
			string = f"|{arrow if i == self.pointer else ' '}" + self.options[i]
			self.print(string, 1, i+1, wrap = False)

class ListBox(Widget):
	def __init__(self, x, y, w, h, title, entries = []):
		self.title = title
		self.entries = entries
		super().__init__(x, y, w, h)

	def draw(self):
		self.fill()
		self.frame()
		self.print(self.title, 0, 0, wrap = False)
		for i in range(len(self.entries)):
			self.print(self.entries[i], 1, i+1, wrap = False)

class Shoutbox(Widget):
	def __init__(self, x, y, w, h):
		self.shouts = ['', '', '', '', '']
		super().__init__(x, y, w, h)

	def add_shout(self, shout):
		self.shouts.append(shout)

	def draw(self):
		self.fill()
		for i in range(5):
			shout = self.shouts[-1-i]
			self.print(shout, 0, 4-i, wrap = False)

class Pointer(Widget):
	def __init__(self, x, y):
		super().__init__(x, y, 1, 1)

	def nudge(self, direction):
		x, y = direction
		self.x += x
		self.y += y

	def draw(self):
		self.buffer.clear()
		self.buffer[(self.x, self.y)] = Glyph(' ', bg=(255, 0, 0))