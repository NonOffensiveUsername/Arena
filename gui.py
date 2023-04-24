from threading import Thread
from structs import *
import sdl
from collections import ChainMap

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
		self.frame_buffer = ChainMap({}, {})
		self.widgets = []
		self.events = []

		self.isInitialized = True

		while not self.window.quit:
			self.events += self.window.poll()

	@property
	def base(self):
		return self.frame_buffer.maps[-1]

	@base.setter
	def base(self, value):
		if type(value) != dict: raise TypeError(f"Frame buffer base expected dictionary, received {type(value)}")
		self.frame_buffer.maps[-1] = value

	@property
	def entity_layer(self):
		return self.frame_buffer[-2]

	@entity_layer.setter
	def entity_layer(self, value):
		if type(value) != dict: raise TypeError(f"Frame buffer entity layer expected dictionary, receieved {type(value)}")
		self.frame_buffer.maps[-2] = value

	def register(self, widget):
		self.widgets.append(widget)
		self.frame_buffer.maps.insert(0, widget.buffer)

	def pop_widget(self):
		if len(self.widgets) > 0:
			self.frame_buffer.maps.pop(0)
			return self.widgets.pop()

	def draw(self):
		self.window.flush()
		for widget in self.widgets:
			widget.draw()
		for coord in self.frame_buffer:
			glyph = self.frame_buffer[coord]
			self.window.print_glyph(glyph.code, *coord, glyph.fg, glyph.bg)
		self.window.update()