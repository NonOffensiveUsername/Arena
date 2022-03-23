from tkinter import *
from tkinter import ttk
from tkinter import font
from threading import Thread

class Interface(Thread):

	def __init__(self):

		Thread.__init__(self)
		self.isInitialized = False
		self.start()

	def callback(self):
		self.root.quit()
		
	def run(self):
		self.root = Tk()
		self.root.protocol("WM_DELETE_WINDOW", self.callback)
		self.root.title("Arena Pre-Alpha")

		mainFrame = ttk.Frame(self.root)
		mainFrame.bind_all('<KeyPress>', self.logEvent)
		mainFrame.grid()

		main_font = font.nametofont("TkFixedFont")
		
		self.field = Text(mainFrame, state = "normal", width = 80, height = 24, background = "black", foreground = "white")
		self.field.grid()

		self.field.insert("1.0", (" " * 80 + "\n") * 24) # Initialize text field full of spaces

		self.events = []

		self.announcements = [
			"test 1",
			"test 2",
			"test 3",
			"test 4",
			"test 5"
		]

		self.isInitialized = True

		self.root.mainloop()

	def render_grid(self, grid, width, height):
		for coord in grid:
			x = coord[0]
			y = coord[1]
			start = str(y + 1) + "." + str(x)
			end = str(y + 1) + "." + str(x + 1)
			self.field.replace(start, end, grid[coord])

	def set_text(self, text):
		pass

	def logEvent(self, event):
		self.events.append(event)

	def add_announcement(self, announcement):
		pass