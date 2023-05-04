from ctypes import *
from collections import namedtuple
import os
import struct

ROW_HEIGHT = 16
COLUMN_WIDTH = 8
#SCALE_FACTOR = 2

COLOR_KEY = 0x00FF00FF

# See SDL_WindowEvent in SDL_events.h for struct details
# This will never use more than 30 bytes but the padding is required because
# the event struct is a union with a max length of 56 bytes.
EVENT_STRUCT_FORMAT = "IIIBBxxiiHIxxxxxxxxxxxxxxxxxxxxxxxx"

class KeyEvent:
	# Magic numbers from SDL
	KEYMOD_SHIFT = 0x0001 | 0x0002
	KEYMOD_CTRL  = 0x0040 | 0x0080
	KEYMOD_ALT   = 0x0100 | 0x0200

	CODES_TO_SYMS = {
		27: "escape",
		13: "enter",
		79: "right",
		80: "left",
		81: "down",
		86: "up",
		89: "down_left",
		90: "down",
		91: "down_right",
		92: "left",
		94: "right",
		95: "up_left",
		96: "up",
		97: "up_right",
	}

	def __init__(self, scancode, keycode, keymod):
		self.scancode = scancode
		self.keycode = keycode
		self.keymod = keymod

	def __repr__(self):
		out = str(self.scancode) + " " + str(self.keycode)
		if self.shift: out += " +SHIFT"
		if self.ctrl: out += " +CTRL"
		if self.alt: out += " +ALT"
		return out

	@property
	def shift(self):
		return self.keymod & KeyEvent.KEYMOD_SHIFT

	@property
	def ctrl(self):
		return self.keymod & KeyEvent.KEYMOD_CTRL

	@property
	def alt(self):
		return self.keymod & KeyEvent.KEYMOD_ALT

	@property
	def symbol(self):
		if 32 < self.keycode < 0x110000:
			return chr(self.keycode)
		if self.keycode in KeyEvent.CODES_TO_SYMS:
			return KeyEvent.CODES_TO_SYMS[self.keycode]
		return self.scancode

# Tell windows we're DPI aware to prevent stretching and blurring
try:
	windll.shcore.SetProcessDpiAwareness(True)
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
dll.SDL_SetColorKey(glyph_sheet, 1, COLOR_KEY)

# May have to grab color format from SDL for portability
def rgb_to_int(rgb):
	return rgb[2] + 0x100 * rgb[1] + 0x10000 * rgb[0]

# Struct for passing coordinates to SDL functions
# This should never be required outside this file
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
		self.width = w // COLUMN_WIDTH
		self.height = h // ROW_HEIGHT

	def flush(self, color = 0x00000000):
		# Color format is 32 bit ARGB
		dll.SDL_FillRect(self.surface, None, color)

	# This should be the only place the window is actually updated
	def update(self):
		dll.SDL_UpdateWindowSurface(self.window)

	# char is the position of the desired character in the code page as an integer
	# can be retrieved from Glyph objects with .code()
	def print_glyph(self, char, x, y, fg = (255, 255, 255), bg = (0, 0, 0)):
		src_rect = SDL_Rect(char % 32 * 8, char // 32 * 16, 8, 16)
		dst_rect = SDL_Rect(x * COLUMN_WIDTH, y * ROW_HEIGHT, 8, 16)
		dll.SDL_FillRect(self.surface, dst_rect, rgb_to_int(bg))
		dll.SDL_SetSurfaceColorMod(glyph_sheet, *fg)
		dll.SDL_UpperBlit(glyph_sheet, src_rect, self.surface, dst_rect)
		# This is the only place blits happen so no need to reset the color mod every time

	def poll(self):
		event_queue = []
		while dll.SDL_PollEvent(byref(self.event)):
			field = self.event.raw[0] + self.event.raw[1] * 0x100
			if field == 0x300:
				e = KeyEvent(*struct.unpack(EVENT_STRUCT_FORMAT, self.event)[5:-1])
				event_queue.append(e)
			elif field == 0x100:
				self.quit = True
		return event_queue