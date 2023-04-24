from entity import Entity, EntityContainer
import entity
from tile import Tile, TileContainer
from structs import *
from gui import Interface
import widget
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

shoutbox = widget.Shoutbox(0, 20, 100, 5)
UI.register(shoutbox)

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
	for e in entities.pop_events():
		shoutbox.add_shout(e.primary)
	UI.base = intermediate_grid
	UI.entity_layer = entities.build_grid()
	UI.draw()

TICK_RATE = 1/60
def poll():
	update_UI()
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
		elif key == 's' or key == 'escape': break
	return None

def get_single_menu_selection(title, options):
	menu = widget.SingleSelectMenu(3, 2, 20, 15, title = title, options = options)
	UI.register(menu)
	result = None
	while key := poll():
		if key == 'j':
			menu.pointer += 1
		elif key == 'k':
			menu.pointer -= 1
		elif key == 'escape':
			break
		elif key == 'enter':
			result = menu.pointer
			break
		menu.pointer %= len(menu.options)
	UI.pop_widget()
	return result

def pick_adjacent_entity():
	neighbors = entities.get_neighbors(player)
	names = [i.name or i in neighbors]
	target = get_single_menu_selection("Target:", names)
	if target is None: return None
	return entities.contents[target]

def examine():
	pointer = widget.Pointer(*player.position)
	entity_list = widget.ListBox(75, 0, 25, 25, "Located Here:")
	UI.register(pointer)
	UI.register(entity_list)
	while key := poll():
		if key in move_binds:
			pointer.nudge(move_binds[key])
			found_entities = entities.find_at((pointer.x, pointer.y))
			entity_list.entries = [i.name for i in found_entities]
		elif key == 'escape':
			break
	UI.pop_widget()
	UI.pop_widget()

# Main loop

update_UI()

while UI.is_alive():
	key = poll()

	if key == 'grave': # debug key, effect subject to change
		UI.window.print_glyph(ord(' '), 10, 24, bg = (255, 0, 0))
		UI.window.update()
	elif key == 'escape':
		pause_option = get_single_menu_selection("Options:", ['Quit', 'Resume'])
		if pause_option == 0: break
	elif key == 'p':
		break
	elif key == 'e':
		interaction_type = get_single_menu_selection("Interact:", ['Attack', 'Pet'])
		if interaction_type is None: continue
		interaction_target = pick_adjacent_entity()
		if interaction_target is None: continue
	elif key == 'x':
		examine()
	elif key in move_binds:
		if not player.move(tiles, move_binds[key]): continue
	elif key == 's':
		player.delay = 10
	elif key == 'c':
		x = get_single_menu_selection("Cast Spell:", ['Fireball', 'Invisibility', 'Heal'])
		print(x)
	elif key == 'a':
		shoutbox.add_shout("Attack where? (dir key or s to cancel)")
		direction = get_dir()
		if direction:
			target = (player.position[0] + direction[0], player.position[1] + direction[1])
			e = entities.find_at(target)
			if e:
				player.send_attack(e[0])
			else:
				shoutbox.add_shout("Whoosh!")
				player.delay += 10
		else:
			shoutbox.add_shout("Cancelled")
			continue

	entities.process(tiles)
	update_UI()