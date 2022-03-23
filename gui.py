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
		self.mainFieldText = StringVar()

		mainFrame = ttk.Frame(self.root)
		mainFrame.bind_all('<KeyPress>', self.logEvent)

		main_font = font.nametofont("TkFixedFont")

		mainField = ttk.Label(mainFrame, textvariable = self.mainFieldText, font = main_font)

		mainFrame.grid(column = 0, row = 0)
		mainField.grid(column = 0, row = 0)

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
		buffer = ""
		for y in range(0, height):
			for x in range(0, width):
				if (x, y) in grid:
					buffer += grid[(x, y)]
				else:
					buffer += ' '
			buffer += "\n"
		for announcement in self.announcements:
			buffer += announcement + "\n"
		self.mainFieldText.set(buffer)

	def set_text(self, text):
		self.mainFieldText.set(text)

	def logEvent(self, event):
		self.events.append(event)

	def add_announcement(self, announcement):
		self.announcements.append(announcement)
		self.announcements.pop(0)