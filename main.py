from entity import Entity, EntityContainer
import entity
from tile import Tile, TileContainer
from structs import *
from gui import Interface
from menu import Menu
import tilemappings
import util
from loader import Loader
import time

loader = Loader()
mat_dict = loader.load_materials()
tiles = loader.load_map(mat_dict)

#tiles.construct_opacity_grid()

# Creating test player entity
player = Entity("1d6", "Player", (5, 5), mat_dict["flesh"])
player.display_tile = Glyph("@", 1, 0)
player.is_player = True
feloid = entity.RandomWalker("1d4", "Feloid Wanderer", (17, 8), mat_dict["flesh"])
feloid.display_tile = Glyph("f", 5, 0)
feloid.speed = 0.5
kobold = entity.Chaser("1d4", "Kobold Chaser", (15, 6), mat_dict["flesh"])
kobold.display_tile = Glyph('k', 3, 0)
kobold.speed = 2.0
kobold.target = player

entities = EntityContainer()
entities.contents = [player, kobold, feloid]

# Creating the UI
UI = Interface()
# Wait for the UI to finish initializing in its own thread before we interact with it
while not UI.isInitialized:
	pass

# Keys associated with movement directions, to be read from file
# Input config file should have lines something like this:
# bind 'h' move -1 0
move_binds = {
	'h': (-1,  0),
	'j': ( 0,  1),
	'k': ( 0, -1),
	'l': ( 1,  0),
	'y': (-1, -1),
	'u': ( 1, -1),
	'b': (-1,  1),
	'n': ( 1,  1),
	'Right': ( 1,  0),
	'Left':  (-1,  0),
	'Up':    ( 0, -1),
	'Down':  ( 0,  1)
}

# Main loop

ui_mode = Mode.MAIN
current_menu = None
quit = False

current_time = time.time()
tick_rate = 1/60
while not quit:
	current_time = time.time()
	if len(UI.events) > 0:
		event = UI.events.pop(0)
		key = None
		try:
			key = chr(event.key_code)
		except:
			key = event.key_code
		if key == 'p': quit = True
		UI.add_announcement(str(key))

		if ui_mode == Mode.MAIN:
			do_process = False
			if key in move_binds:
				new_position = (player.position[0] + move_binds[key][0], player.position[1] + move_binds[key][1])
				if tiles.get_tile(new_position[0], new_position[1]).traversal_cost() >= 0:
					player.move(tiles, move_binds[key])
					do_process = True
			elif key == 's':
				player.delay = 10
				do_process = True
			elif key == 'c':
				ui_mode = Mode.MENU
				current_menu = Menu("cast_menu", "Cast Spell:", ['Fireball', 'Invisibility', 'Heal'])
				# Execution will run off to the next if block, we clear the current event so it isn't used as input in the created menu
				event = None

			if do_process:
				entities.process(tiles)
			
		if ui_mode == Mode.MENU:
			if event: # Event could be None
				if key == 'a':
					ui_mode = Mode.MAIN
				elif key == 'j':
					current_menu.pointer += 1
				elif key == 'k':
					current_menu.pointer -= 1
			UI.set_text(current_menu.to_string())

		if ui_mode == Mode.MAIN:
			# Build intermediate render object from tile map and add player
			intermediate_grid = tiles.map(tilemappings.testMappingFunction)
			for e in entities.contents:
				intermediate_grid[e.position] = e.display_tile
			# Send our intermediate grid off to be rendered
			UI.render_grid(intermediate_grid)
	else:
		time.sleep(tick_rate - (time.time() - current_time))