from entity import *
from actor import *
from tile import *
from structs import *
from gui import Interface
import widget
import tilemappings
import util
import loader
import time
import copy

mat_dict = loader.load_materials()
template_dict = loader.load_templates()
Entity.DEFAULT_MAT = mat_dict["flesh"]
feature_dict = loader.load_features(mat_dict)
tiles = loader.load_map(mat_dict, feature_dict, "map")

DEBUG = True

if DEBUG:
	# Test entities
	player = Actor.from_template("Player", (5, 5), template_dict["demigod"], is_player = True)
	player.seen = set()
	player.currently_seen = set()
	#feloid = RandomWalker.from_template("Feloid Wanderer", (17, 8), template_dict["feloid"])
	#kobold = Chaser.from_template("Kobold Chaser", (15, 6), template_dict["kobold"])
	#kobold.target = player
	#genie = Actor.from_template("Genie", (45, 10), template_dict["spirit"])
	crab = TetheredWanderer.from_template("Crab", (49, 10), template_dict["crab"])
	crab.tether = (
		(49, 10),
		(49, 11),
		(49, 12),
		(49, 13),
		(50, 10),
		(50, 11),
		(50, 12),
		(50, 13),
	)
	axe = Entity.from_template("Axe", (11, 16), template_dict["axe"])

	sack = Entity.from_template("[128,128,0]Burlap sack[w]", (4, 6), template_dict["sack"])
	stuff_in_sack = [
		Entity.from_template("Shiny pebble", None, template_dict["rock"]),
		Entity.from_template("Dull pebble", None, template_dict["rock"]),
		Entity.from_template("[128,128,0]Velvet sack[w]", None, template_dict["sack"]),
		Entity.from_template("Colorful pebble", None, template_dict["rock"]),
	]
	magic_pebble = Entity.from_template("[b]Magic pebble[w]", None, template_dict["rock"])

	for thing in stuff_in_sack:
		sack.insert(thing)

	sack._contents[2].insert(magic_pebble)

	soyjak = Actor.from_template("Soyjak", (29, 11), template_dict["human"])
	gun = Entity.from_template("Rifle", (21, 15), template_dict["bolt action rifle"])

	entities = EntityContainer()
	#entities.add_entity(player, kobold, feloid, genie, crab, axe)
	entities.add_entity(player, crab, axe, soyjak, gun)
	entities.add_entity(sack, *stuff_in_sack, magic_pebble)

	zombies = [Monster.from_template(f"Zombie {x}", (55, 11 + x), template_dict["human"], template_dict["zombie"]) for x in range(4)]
	entities.add_entity(*zombies)

	# Adding flow features to water tiles... maybe just inherently randomize fluid rendering?
	flow_glyph = UnstableGlyph(
		('~', 247),
		((255, 255, 255),),
		((0, 0, 0),)
	)
	fluid_flow = TileFeature("Flowing liquid", -1, None, char_overwrite = True, symbol = flow_glyph)
	for tile in tiles.contents:
		if tiles.contents[tile].floor_material.state == State.LIQUID:
			tiles.contents[tile].add_feature(copy.copy(fluid_flow))

	tiles.construct_opacity_grid()

UI = Interface()

shoutbox = widget.Shoutbox(0, 20, 100, 5)
UI.register(shoutbox)

status_box = widget.ListBox(60, 0, 39, 24, "Status:")
UI.register(status_box)

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
	intermediate_grid = tiles.map_visible(tilemappings.visual_map_func, player.position, player.currently_seen, player.seen)
	for e in entities.pop_events():
		shoutbox.add_shout(e.primary)
	UI.base = intermediate_grid
	UI.entity_layer = entities.build_grid_with_visibility(player.currently_seen)
	status_entries = [
		f"Name: {player.name}",
		f"HP: [r]{player.hp}/{player.hp_max}"
	]
	for grasper, grasped in player.get_held_entities():
		status_entries.append(f"{grasper.name}: {grasped.name}")
	status_box.entries = status_entries
	UI.draw()

TICK_RATE = 1/100
def poll():
	player.currently_seen = tiles.visible_from(player.position)
	player.seen = player.seen.union(player.currently_seen)
	update_UI()
	cur_time = None
	while True:
		cur_time = time.time()
		UI.update_queue()
		if not UI.alive: break
		if UI.events:
			return UI.events.pop(0)
		else:
			time.sleep(max(TICK_RATE - (time.time() - cur_time), 0))
	return False

def get_dir():
	while key := poll().symbol:
		if key in move_binds:
			return move_binds[key]
		elif key == 's' or key == 'escape': break
	return None

def get_single_menu_selection(title, options):
	menu = widget.SingleSelectMenu(3, 2, 20, 15, title = title, options = options)
	UI.register(menu)
	result = None
	while key := poll().symbol:
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
	if not options: return None
	return result

def pick_adjacent_entity(prompt):
	neighbors = entities.get_within_radius(player)
	names = [i.name for i in neighbors]
	target = get_single_menu_selection(prompt, names)
	if target is None: return None
	return neighbors[target]

# Works for any list of objects with .name attributes
# Mainly entities and body parts
def pick_named_object_from_list(prompt, options):
	names = [i.name for i in options]
	target = get_single_menu_selection(prompt, names)
	if target is None: return None
	return options[target]

def examine():
	pointer = widget.Pointer(*player.position)
	infobox = widget.ListBox(60, 0, 39, 24, "Located Here:")
	UI.register(pointer)
	UI.register(infobox)
	while key := poll().symbol:
		if key in move_binds:
			pointer.nudge(move_binds[key])
			target = (pointer.x, pointer.y)
			found_entities = entities.buckets[target]
			infobox.entries = [f"{i.name} [r]{i.hp}/{i.hp_max}" for i in found_entities]
			if target in player.seen:
				targeted_tile = tiles.get_tile(*target)
				infobox.entries += targeted_tile.build_descriptor()
		elif key == 'escape':
			break
	UI.pop_widget()
	UI.pop_widget()

def show_inventory():
	inventory_items = player.build_contents_tree()
	inv_listbox = widget.ListBox(3, 2, 30, 15, "Inventory", inventory_items)
	UI.register(inv_listbox)
	while key := poll().symbol:
		if key == 'escape': break
	UI.pop_widget()

def select_inventory_item():
	inventory_items = player.build_contents_tree()
	target = get_single_menu_selection("Drop what?", inventory_items)
	if target is None: return None
	return player.contents[target]

# Main loop

player.currently_seen = tiles.visible_from(player.position)
player.seen = player.seen.union(player.currently_seen)
update_UI()

while event := poll():
	key = event.symbol

	if key == '`': # debug key, effect subject to change
		x = time.time()
		for i in range(100):
			update_UI()
		y = time.time()
		frame_time = (y - x) / 100
		print("Average time per frame: " + str(frame_time))
	elif key == 'escape':
		pause_option = get_single_menu_selection("Options:", ['Quit', 'Resume'])
		if pause_option == 0: break
	elif key == 'p':
		break
	elif key == 'e':
		interaction_type = get_single_menu_selection("Interact:", ['Attack', 'Pet'])
		if interaction_type is None: continue
		interaction_target = pick_adjacent_entity("Target:")
		if interaction_target is None: continue
	elif key == 'g':
		pick_target = pick_adjacent_entity("Pick up what?")
		if not pick_target: continue
		if player.get(pick_target):
			player.delay = 10
			shoutbox.add_shout(f"You grab the [y]{pick_target.name}")
			continue
		shoutbox.add_shout(f"Unable to pick up {pick_target.name}")
	elif key == 'x':
		examine()
	elif key in move_binds:
		if not player.move(tiles, move_binds[key]): continue
	elif key == 's':
		player.delay = 10
	elif key == '.':
		player.delay = 1
	elif key == 'c':
		x = get_single_menu_selection("Cast Spell:", ['Fireball', 'Invisibility', 'Heal'])
		print(x)
	elif key == 'a':
		shoutbox.add_shout("Attack where? (dir key or s to cancel)")
		direction = get_dir()
		if not direction:
			shoutbox.add_shout("Cancelled")
			continue
		target = (player.position[0] + direction[0], player.position[1] + direction[1])
		e = entities.buckets[target]
		if not e:
			shoutbox.add_shout("Whoosh!")
			player.delay += 10
			continue
		target = e[0]
		if len(e) > 1:
			target = pick_named_object_from_list("Attack what?", e)
		target_part = None
		if event.shift:
			target_part = pick_named_object_from_list("Which part?", target.root_part.get_part_list())
		player.send_attack(target, target_part)
	elif key == 'i':
		show_inventory()
	elif key == 'd':
		if (drop_target := select_inventory_item()) is None: continue
		player.drop(drop_target)

	entities.process(tiles)