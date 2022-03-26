from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent
from threading import Thread

class Interface(Thread):

	def __init__(self):

		Thread.__init__(self)
		self.isInitialized = False
		self.daemon = True
		self.start()
		
	def run(self):

		self.console = Screen.open()
		self.console.clear()
		self.console.print_at("test", 0, 0)
		self.console.refresh()

		self.events = []
		self.announcements = [
			"Test 1",
			"Test 2",
			"Test 3",
			"test 4",
			"Test 5"
		]

		self.isInitialized = True

		while True:
			self.console.wait_for_input(86400)
			event = self.console.get_event()
			if isinstance(event, KeyboardEvent):
				self.events.append(event)

	def render_grid(self, grid):
		for coord in grid:
			x = coord[0]
			y = coord[1]
			self.console.print_at(grid[coord], x, y)
		self.console.refresh()

	def set_text(self, text):
		pass

	def add_announcement(self, announcement):
		self.announcements.append(announcement)
		self.announcements.pop(0)
		for e in range(0, 5):
			self.console.print_at(self.announcements[e].ljust(80), 0, 21 + e)
		self.console.refresh()