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
import random
import sys
from collections import deque

mat_dict = loader.load_materials()
template_dict = loader.load_templates()
Entity.DEFAULT_MAT = mat_dict["flesh"]
feature_dict = loader.load_features(mat_dict)
map_name = "map"
if len(sys.argv) > 1: map_name = sys.argv[1]
tiles, entity_blueprint = loader.load_map(mat_dict, feature_dict, map_name)

entities = EntityContainer()
entities.tiles = tiles

for pos in entity_blueprint:
	templates = entity_blueprint[pos]['templates']
	new_entity = Actor.from_template(templates[0], pos, *[template_dict[template] for template in templates])
	entities.add_entity(new_entity)
	for held_item in entity_blueprint[pos].get('held', []):
		item = Entity.from_template(held_item, None, template_dict[held_item])
		new_entity.get(item)
		entities.add_entity(item)

tiles.entities = entities

DEBUG = True

if DEBUG:

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

# TODO: Clean up fps tracking code
# srsly this is a mess
fps_label = widget.Label(0, 0, "")
UI.register(fps_label)
last_frame_time = 0
last_frame_times = deque([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 10)

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
	UI.base = intermediate_grid
	secondary_grid = entities.build_grid()
	for e in entities.pop_events():
		shoutbox.add_shout(e.primary)
	UI.entity_layer = secondary_grid
	status_entries = [
		f"Name: God",
		f"HP: [r]\xEC/\xEC"
	]
	status_box.entries = status_entries
	# More messy fps tracking
	now_time = time.time()
	global last_frame_time # global ew ick kill it
	cur_fps = 1 / (now_time - last_frame_time)
	last_frame_times.append(cur_fps)
	average_fps = int(sum(last_frame_times) / 10)
	fps_label.text = "[c]" + str(average_fps)
	last_frame_time = now_time
	# /mess
	UI.draw()

TICK_RATE = 1/30
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
				entities.tick()
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
	entity_list_pointer = 0
	entity_list_length = 0
	while key := poll():
		sym = key.symbol
		if sym in move_binds:
			entity_list_pointer = 0
			direction = move_binds[sym]
			if key.shift:
				direction = util.tup_mul(direction, (5, 5))
			pointer.nudge(direction)
		elif sym == '[' or sym == '-':
			entity_list_pointer -= 1
			if entity_list_pointer < 0:
				entity_list_pointer = entity_list_length - 1
		elif sym == ']' or sym == '+':
			entity_list_pointer += 1
			if entity_list_pointer >= entity_list_length:
				entity_list_pointer = 0
		elif sym == ';':
			clang = Event(sound = "Clang!", volume = 2.0, visual_priority = False, position = (pointer.x, pointer.y))
			entities.add_event(clang)
		elif sym == 'escape':
			break
		elif sym == 'enter':
			if entity_list_length:
				entity_detail_view(entities.buckets[(pointer.x, pointer.y)][entity_list_pointer])
		target = (pointer.x, pointer.y)
		targeted_tile = tiles.get_tile(*target)
		infobox.entries = targeted_tile.build_descriptor()
		found_entities = entities.buckets[target]
		entity_list_length = len(found_entities)
		infobox.entries += [f"{i.name} [r]{i.hp}/{i.hp_max}" for i in found_entities]
		if entity_list_length:
			infobox.entries[2 + entity_list_pointer] = "[m]\x1A" + infobox.entries[2 + entity_list_pointer]
	UI.pop_widget()
	UI.pop_widget()

def entity_detail_view(entity):
	details = widget.ListBox(5, 2, 40, 10, entity.name)
	details.entries = [
		f"ST: {entity.ST} HT: {entity.HT}",
		f"DX: {entity.DX} IQ: {entity.IQ}",
		"Inventory:",
	]
	details.entries += entity.build_contents_tree()
	UI.register(details)
	while key := poll():
		sym = key.symbol
		if sym == 'escape':
			break
	UI.pop_widget()

update_UI()

# Main loop

while event := idle():
	sym = event.symbol
	if sym == 'p':
		break
	elif sym == '`':
		target = None
		while True:
			target = (random.randrange(60), random.randrange(20))
			if tiles.get_tile(*target).traversal_cost() >= 0:
				break
		z = Actor.from_template("Zombie", target, template_dict["human"], template_dict["zombie"])
		entities.add_entity(z)
	elif sym == 'space':
		pause_label = widget.Label(0, 0, "[g][B100,100,100]Paused")
		UI.register(pause_label)
		while key := poll():
			if key.symbol == 'space':
				break
			if key.symbol == '.':
				entities.tick(tiles)
		UI.pop_widget()
	elif sym == 'x':
		examine()