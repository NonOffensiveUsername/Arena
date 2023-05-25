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

	soyjak = Actor.from_template("Soyjak", (29, 11), template_dict["human"])
	gun = Entity.from_template("Rifle", (21, 15), template_dict["bolt action rifle"])

	entities = EntityContainer()
	entities.add_entity(crab, soyjak, gun)

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
	intermediate_grid = tiles.map(tilemappings.visual_map_func)
	for e in entities.pop_events():
		shoutbox.add_shout(e.primary)
	UI.base = intermediate_grid
	UI.entity_layer = entities.build_grid()
	status_entries = [
		f"Name: God",
		f"HP: [r]\xEC/\xEC"
	]
	status_box.entries = status_entries
	UI.draw()

TICK_RATE = 1/100
TICKS_PER_FRAME = 1
def idle():
	cur_time = None
	while True:
		cur_time = time.time()
		update_UI()
		UI.update_queue()
		if not UI.alive: break
		if UI.events:
			return UI.events.pop(0)
		else:
			for i in range(TICKS_PER_FRAME):
				entities.tick(tiles)
			time.sleep(max(TICK_RATE - (time.time() - cur_time), 0))
	return False

def poll():
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

def examine():
	pointer = widget.Pointer(50, 10)
	infobox = widget.ListBox(60, 0, 39, 24, "Located Here:")
	UI.register(pointer)
	UI.register(infobox)
	while key := poll():
		sym = key.symbol
		if sym in move_binds:
			direction = move_binds[sym]
			if key.shift:
				direction = util.tup_mul(direction, (5, 5))
			pointer.nudge(direction)
			target = (pointer.x, pointer.y)
			found_entities = entities.buckets[target]
			infobox.entries = [f"{i.name} [r]{i.hp}/{i.hp_max}" for i in found_entities]
			targeted_tile = tiles.get_tile(*target)
			infobox.entries += targeted_tile.build_descriptor()
		elif sym == 'escape':
			break
	UI.pop_widget()
	UI.pop_widget()

update_UI()

# Main loop

while event := idle():
	sym = event.symbol
	if sym == 'p':
		break
	elif sym == 'space':
		pause_label = widget.Label(0, 0, "[g][B100,100,100]Paused")
		UI.register(pause_label)
		while key := poll():
			if key.symbol == 'space':
				break
		UI.pop_widget()
	elif sym == 'x':
		examine()