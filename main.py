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
template_dict = loader.load_templates()
Entity.DEFAULT_MAT = mat_dict["flesh"]
tiles = loader.load_map(mat_dict, "map")

# Test entities
player = Entity.from_template("Player", (5, 5), template_dict["demigod"], is_player = True)
feloid = entity.RandomWalker.from_template("Feloid Wanderer", (17, 8), template_dict["feloid"])
kobold = entity.Chaser.from_template("Kobold Chaser", (15, 6), template_dict["kobold"])
kobold.target = player

entities = EntityContainer()
entities.add_entity(player)
entities.add_entity(kobold)
entities.add_entity(feloid)

# Creating the UI
UI = Interface()
# Wait for the UI to finish initializing in its own thread before we interact with it
while not UI.isInitialized:
	pass

# Keys associated with movement directions
move_binds = {
	'h': (-1,  0),
	'j': ( 0,  1),
	'k': ( 0, -1),
	'l': ( 1,  0),
	'y': (-1, -1),
	'u': ( 1, -1),
	'b': (-1,  1),
	'n': ( 1,  1),
}

def update_UI():
	intermediate_grid = tiles.map(tilemappings.visual_map_func)
	for e in sorted(entities.contents, key = lambda x: x.size):
		intermediate_grid[e.position] = e.display_tile
	for e in entities.pop_events():
		UI.add_announcement(e.visual)
	UI.render_grid(intermediate_grid)

TICK_RATE = 1/60
def poll():
	cur_time = None
	while UI.is_alive():
		cur_time = time.time()
		if UI.events:
			return UI.events.pop(0)
		else:
			time.sleep(TICK_RATE - (time.time() - cur_time))
	return False

def get_dir():
	while key := poll():
		if key in move_binds:
			return move_binds[key]
		elif key == 's': break
	return None

# Main loop

ui_mode = Mode.MAIN
current_menu = None

update_UI()

while UI.is_alive():
	if len(UI.events) > 0:
		event = UI.events.pop(0)
		key = event
		if key == 'q':
			print(kobold.soul)
		if key == 'p': break

		if ui_mode == Mode.MAIN:
			if key in move_binds:
				if not player.move(tiles, move_binds[key]): continue
			elif key == 's':
				player.delay = 10
			elif key == 'c':
				ui_mode = Mode.MENU
				current_menu = Menu("cast_menu", "Cast Spell:", ['Fireball', 'Invisibility', 'Heal'])
				UI.set_text(str(current_menu))
				continue
			elif key == 'a':
				UI.add_announcement("Attack where? (dir key or s to cancel)", redraw = True)
				direction = get_dir()
				if direction:
					target = (player.position[0] + direction[0], player.position[1] + direction[1])
					e = entities.find_at(target)
					if e:
						player.send_attack(e[0])
					else:
						UI.add_announcement("Whoosh!", redraw = True)
						player.delay += 10
				else:
					UI.add_announcement("Cancelled", redraw = True)
					continue

			entities.process(tiles)
			
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