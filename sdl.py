from ctypes import *
import os

# Tell windows we're DPI aware to prevent stretching and blurring
try:
	windll.shcore.SetProcessDpiAwareness (True)
except:
	pass

dll = CDLL(os.path.abspath("sdl/SDL2"))

# Initialize SDL with video subsystem
if dll.SDL_Init(0x00000020) != 0:
	print("SDL is borked")

# Setting up return types for SDL functions
dll.SDL_GetError.restype = c_char_p

nullptr = POINTER(c_void_p)

dll.SDL_CreateWindow.restype = nullptr
dll.SDL_GetWindowSurface.restype = nullptr
dll.SDL_RWFromFile.restype = nullptr
dll.SDL_LoadBMP_RW.restype = nullptr

# Load font
stream = dll.SDL_RWFromFile(b"data/glyphs_8x16.bmp", b"rb")
glyph_sheet = dll.SDL_LoadBMP_RW(stream, 1)
dll.SDL_SetColorKey(glyph_sheet, 1, 0x00000000)
# This just doesn't work so I guess we simply won't free the resource???
# What could go wrong lol
# dll.SDL_RWclose(stream)

def rgb_to_int(rgb):
	return rgb[2] + 0x100 * rgb[1] + 0x10000 * rgb[0]

class SDL_Rect(Structure):
	_fields_ = [
		("x", c_int),
		("y", c_int),
		("w", c_int),
		("h", c_int),
	]

class Window():
	def __init__(self, title, x, y, w, h, flags = 0):
		self.window = dll.SDL_CreateWindow(bytes(title, 'utf-8'), x, y, w, h, flags)
		self.surface = dll.SDL_GetWindowSurface(self.window)
		# SDL code suggests that 56 bytes is the maximum size of a returned event union
		self.event = create_string_buffer(56)
		self.quit = False
		self.width = w // 8
		self.height = h // 16

	def flush(self, color = 0x00000000):
		# Color format is 32 bit ARGB
		dll.SDL_FillRect(self.surface, None, color)

	def update(self):
		dll.SDL_UpdateWindowSurface(self.window)

	def print_glyph(self, glyph, x, y, fg = (255, 255, 255), bg = (0, 0, 0)):
		char = glyph
		if type(char) != int:
			char = ord(glyph)
		src_rect = SDL_Rect(char % 32 * 8, char // 32 * 16, 8, 16)
		dst_rect = SDL_Rect(x * 8, y * 16, 8, 16)
		dll.SDL_FillRect(self.surface, dst_rect, rgb_to_int(bg))
		dll.SDL_SetSurfaceColorMod(glyph_sheet, fg[0], fg[1], fg[2])
		dll.SDL_UpperBlit(glyph_sheet, src_rect, self.surface, dst_rect)
		dll.SDL_SetSurfaceColorMod(glyph_sheet, 255, 255, 255)

	def print_string(self, string, x, y, wrap = False):
		x_offset = 0
		y_offset = 0
		z_offset = 0
		for i in range(0, len(string)):
			if wrap:
				if x + i + x_offset >= self.width:
					x_offset -= self.width
					y_offset += 1
			if string[i] == '\n':
				y_offset += 1
				x_offset = -i
			else:
				self.print_glyph(string[i], x + x_offset + i, y + y_offset)
		return y_offset

	def poll(self):
		event_queue = []
		while dll.SDL_PollEvent(byref(self.event)):
			field = self.event.raw[0] + self.event.raw[1] * 0x100
			if field == 0x300:
				event_queue.append(chr(self.event.raw[20]))
			elif field == 0x100:
				self.quit = True
		return event_queue