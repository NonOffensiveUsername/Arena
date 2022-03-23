class Menu():

	def __init__(self, menu_type, title, options, pointer = 0):
		self.menu_type = menu_type
		self.title = title
		self.options = options
		self.pointer = pointer

	def to_string(self):
		out_string = self.title + "\n"
		for x in range(0, len(self.options)):
			buffer = " | >" if x == self.pointer else " |  "
			buffer += self.options[x] + "\n"
			out_string += buffer
		return out_string