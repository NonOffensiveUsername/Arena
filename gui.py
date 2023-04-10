from threading import Thread
import sdl

class Interface(Thread):

	def __init__(self):

		Thread.__init__(self)
		self.isInitialized = False
		self.daemon = True
		self.start()
		
	def run(self):
		self.window = sdl.Window("test", 200, 200, 800, 400) # 100x25 glyphs
		self.window.flush()
		self.window.update()

		self.events = []
		self.announcements = [
			"Test 1",
			"Test 2",
			"Test 3",
			"test 4",
			"Test 5"
		]

		self.isInitialized = True

		while not self.window.quit:
			self.events += self.window.poll()

	def render_grid(self, grid):
		self.window.flush()
		for coord in grid:
			x = coord[0]
			y = coord[1]
			glyph = grid[coord]
			self.window.print_glyph(glyph.character, x, y, glyph.fg, glyph.bg)
		self.draw_announcements()
		self.window.update()

	def set_text(self, text):
		self.window.flush()
		self.window.print_string(text, 0, 0)
		self.window.update()

	def add_announcement(self, announcement):
		self.announcements.append(announcement)
		self.announcements.pop(0)

	def draw_announcements(self):
		for e in range(0, 5):
			self.window.print_string(self.announcements[e], 0, 20 + e)