from entity import Entity, EntityContainer
import entity
from tile import Tile, TileContainer
from structs import *
from gui import Interface
from menu import Menu
import tilemappings
import util
import loader
import time

mat_dict = loader.load_materials()
tiles = loader.load_map(mat_dict, "map")

#tiles.construct_opacity_grid()

# Creating test player entity
player = Entity("Player", (5, 5), mat_dict["flesh"])
player.display_tile = Glyph("@", (255, 0, 0), (0, 0, 0))
player.is_player = True
feloid = entity.RandomWalker("Feloid Wanderer", (17, 8), mat_dict["flesh"])
feloid.display_tile = Glyph("f", (255, 130, 20), (0, 0, 0))
feloid.speed = 0.5
kobold = entity.Chaser("Kobold Chaser", (15, 6), mat_dict["flesh"])
kobold.display_tile = Glyph('k', (102, 68, 0), (0, 0, 0))
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

def update_UI():
	# Build intermediate render object from tile map and add player
	intermediate_grid = tiles.map(tilemappings.visual_map_func)
	for e in entities.contents:
		intermediate_grid[e.position] = e.display_tile
	# Send our intermediate grid off to be rendered
	UI.render_grid(intermediate_grid)

# Main loop

ui_mode = Mode.MAIN
current_menu = None

update_UI()

current_time = time.time()
tick_rate = 1/60
while UI.is_alive():
	current_time = time.time()

	if len(UI.events) > 0:
		event = UI.events.pop(0)
		key = event
		if key == 'p': break

		if ui_mode == Mode.MAIN:
			do_process = False
			if key in move_binds:
				do_process = player.move(tiles, move_binds[key])
			elif key == 's':
				player.delay = 10
				do_process = True
			elif key == 'c':
				ui_mode = Mode.MENU
				current_menu = Menu("cast_menu", "Cast Spell:", ['Fireball', 'Invisibility', 'Heal'])
				# Execution will run off to the next if block, we clear the current event so it isn't used as input in the created menu
				event = None

			if do_process:
				process_start = time.time()
				entities.process(tiles)
				UI.add_announcement("Processed entities in " + str(time.time() - process_start))
			
		if ui_mode == Mode.MENU:
			if event: # Event could be None
				if key == 'a':
					ui_mode = Mode.MAIN
				elif key == 'j':
					current_menu.pointer += 1
				elif key == 'k':
					current_menu.pointer -= 1
			UI.set_text(str(current_menu))

		if ui_mode == Mode.MAIN:
			update_UI()
	else:
		time.sleep(tick_rate - (time.time() - current_time))