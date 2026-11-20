import json
import os
from pathlib import Path

MARKER_TAG = "boat_marker"
FILE_ROOT = "./docks/"
FUNCTION_ROOT = "escapemap:boat/docks/"

OUT_FILE = Path("../data/escapemap/scripts/boat/docks.mcscript")

class DockDef:
    def __init__(self, dic):
        self.name = dic["name"]
        self.marker_pos = dic["marker_pos"]
        self.boat_pos = dic["boat_pos"].split(" ")
        self.horn_distance = dic["horn_distance"]
        self.boat_distance = dic["boat_distance"]
        self.barriers = dic["barriers"]

def load_objects(directory):
    objects = []
    directory = Path(directory)

    for file in directory.glob("*.json"):
        try:
            with file.open("r", encoding="utf-8") as f:
                objects.append(DockDef(json.load(f)))
        except (json.JSONDecodeError, OSError) as e:
            print(f"Failed to read {file.name}: {e}")

    return objects

def create_function(name, content):
    return "#file: " + FILE_ROOT + name + "\n" + content + "\n\n"

tick_content = ""
reset_content = ""
use_horn_content = ""

def set_barriers(barriers):
    ret = ""
    for barrier in barriers:
        ret += "/setblock " + barrier + " barrier\n"
    return ret

def set_air(barriers):
    ret = ""
    for barrier in barriers:
        ret += "/setblock " + barrier + " air\n"
    return ret

def call_function(fn_name):
    return "/function " + FUNCTION_ROOT + fn_name + "\n"

def create_animation(dock):
    return f"""/kill @e[tag=calledBoat]
{call_function("close_all")}
/schedule clear {FUNCTION_ROOT}summon/{dock.name}
/schedule clear {FUNCTION_ROOT}particle/{dock.name}
/schedule clear {FUNCTION_ROOT}particle_post/{dock.name}
/schedule function {FUNCTION_ROOT}particle/{dock.name} 42t append
/schedule function {FUNCTION_ROOT}particle/{dock.name} 60t append
/schedule function {FUNCTION_ROOT}particle/{dock.name} 70t append
/schedule function {FUNCTION_ROOT}particle/{dock.name} 80t append
/schedule function {FUNCTION_ROOT}particle/{dock.name} 90t append
/schedule function {FUNCTION_ROOT}particle/{dock.name} 95t append
/schedule function {FUNCTION_ROOT}particle/{dock.name} 100t append
/schedule function {FUNCTION_ROOT}particle/{dock.name} 105t append
/schedule function {FUNCTION_ROOT}particle/{dock.name} 110t append
/schedule function {FUNCTION_ROOT}particle/{dock.name} 115t append
/schedule function {FUNCTION_ROOT}summon/{dock.name} 120t replace
/schedule function {FUNCTION_ROOT}particle_post/{dock.name} 125t append
/schedule function {FUNCTION_ROOT}particle_post/{dock.name} 130t append
/schedule function {FUNCTION_ROOT}complete/{dock.name} 135t append
"""

def handle_dock(dock):
    global reset_content, tick_content, use_horn_content
    name = dock.name
    content = ""

    reset_content += "//barriers for " + name + "\n"
    reset_content += set_barriers(dock.barriers)
    reset_content += "dock_state " + name + " = 0\n"

    tick_content += "//boat listener for " + name + "\n"
    tick_content += "if(dock_state " + name + " == 0) {\n"
    tick_content += "at(@a[gamemode=adventure,nbt={RootVehicle:{Entity:{id:\"minecraft:spruce_boat\"}}}]) {\n"
    tick_content += f"if('entity @e[tag={MARKER_TAG},tag={name},limit=1,distance=..{dock.boat_distance}]') {{\n"
    tick_content += set_air(dock.barriers)
    tick_content += "dock_state " + name + " = 2" + "\n"
    tick_content += "}}}\n"

    tick_content += "if(dock_state " + name + " == 2) {\n"
    tick_content += "at(@a[gamemode=adventure,nbt={RootVehicle:{Entity:{id:\"minecraft:spruce_boat\"}}}]) {\n"
    tick_content += f"if('entity @e[tag={MARKER_TAG},tag={name},limit=1,distance={dock.boat_distance}..]') {{\n"
    tick_content += set_barriers(dock.barriers)
    tick_content += "dock_state " + name + " = 0" + "\n"
    tick_content += "}}}\n"

    use_horn_content += "//horn listener for " + name + "\n"
    use_horn_content += "at(@s){\n"
    use_horn_content += f"if('entity @e[tag={MARKER_TAG},tag={name},limit=1,distance=..{dock.horn_distance}]') {{\n"
    use_horn_content += "if(dock_state " + name + " == 0) {\n"
    use_horn_content += call_function("call_boat/" + name)
    use_horn_content += "}}}\n"

    call_boat_content = create_animation(dock)
    call_boat_content += "dock_state " + name + " = 1\n"
    content += create_function("call_boat/" + name, call_boat_content)

    x, z = dock.boat_pos[0], dock.boat_pos[1]

    particle_content = f"/particle minecraft:bubble {x} -43.25 {z} 0.7 0 0.7 0.3 75 normal\n/particle minecraft:snowflake {x} -44.5 {z} 0.7 0 0.7 0.1 75 normal\n"
    content += create_function("particle/" + name, particle_content)

    post_particle_content = "/particle minecraft:bubble {x} -43 {z} 0.7 0 0.7 0.3 75 normal\n/particle minecraft:snowflake {x} -44 {z} 0.7 0 0.7 0.1 75 normal\n"
    content += create_function("post_particle/" + name, post_particle_content)

    summon_content = f"/kill @e[tag=calledBoat]\n/particle minecraft:bubble_pop {x} -43.5 {z} 1 0 1 0.2 100 normal\n/summon minecraft:spruce_boat {x} -52.286 {z} {{Motion:[0.0,3.5,0.0],Tags:[\"calledBoat\"],Invulnerable:1}}\n"
    content += create_function("summon/" + name, summon_content)

    complete_content = "dock_state " + name + " = 2\n"
    complete_content += set_air(dock.barriers)
    content += create_function("complete/" + name, complete_content)


    return content

if __name__ == "__main__":
    directory = "docks"
    objects = load_objects(directory)

    file = "var dock_state\n" #0=closed,1=opening,2=open

    print(f"Creating {len(objects)} docks...")
    for obj in objects:
        file += handle_dock(obj)

    file += create_function("tick", tick_content)
    reset_content += "/kill @e[tag=calledBoat]\n"
    file += create_function("reset", reset_content)
    file += create_function("use_horn", use_horn_content)

    file += create_function("close_all", "\n".join(["\n".join([set_barriers(obj.barriers), "dock_state " + obj.name + " = 0"]) for obj in objects]))

    OUT_FILE.write_text(file, encoding="utf-8")
