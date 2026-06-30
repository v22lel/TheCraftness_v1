from pathlib import Path

# ============================================================
# Configuration
# ============================================================

NAMESPACE = "escapemap"
OUT_FILE = Path("scripts/output/faucet.mcscript")

# Coordinates where the faucet base will be placed
FAUCET_X = -177.5
FAUCET_Y = -37
FAUCET_Z = 68.2

# Directional configuration (0.0 = South, 90.0 = West, 180.0 = North, 270.0 = East)
FACING_YAW = 180.0

# The exact, fully-qualified function name to invoke on turn callback
CALLBACK_FUNCTION = f"{NAMESPACE}:puzzles/desert/faucet_controller/onrotate"

# Vertical offset from bottom up for the item_display handle
HANDLE_Y_OFFSET = 2.2

# Interaction box placement and properties
INTERACTION_Y_OFFSET = 1.6 # Height offset to elevate interaction box to top
INTERACTION_WIDTH = 0.5
INTERACTION_HEIGHT = 0.2

# How many degrees the handle rotates per click
ROTATION_PER_CLICK = 2.0

# Custom Item Components (Minecraft 1.21.4 style)
COMPONENT_BASE = f'{{"minecraft:item_model": "{NAMESPACE}:faucet_base"}}'
COMPONENT_HANDLE = f'{{"minecraft:item_model": "{NAMESPACE}:faucet_handle"}}'

# Item checked in mainhand
HANDLE_ITEM_ID = "minecraft:paper"
# Precise match definition component for 1.21.4 item checks
ITEM_PREDICATE = f"{HANDLE_ITEM_ID}[minecraft:item_model=\"{NAMESPACE}:faucet_handle\"]"

# ============================================================
# Code Generation Logic
# ============================================================

def emit_function(name: str, body: list[str]) -> str:
    commands = "\n".join(body)
    return f"#file: ./{name}\n{commands}\n\n"

def generate_faucet_logic() -> str:
    chunks = []

    # Pre-calculated structural vertical coordinates
    handle_y = FAUCET_Y + HANDLE_Y_OFFSET
    interaction_y = FAUCET_Y + INTERACTION_Y_OFFSET
    actual_faucet_y = FAUCET_Y + 0.5

    # 1. SPAWN FUNCTION
    spawn_cmds = [
        f"/kill @e[tag=escapemap_faucet_base]",
        f"/kill @e[tag=escapemap_faucet_handle]",
        f"/kill @e[tag=faucet_interaction]",
        f"// Spawn Faucet Base facing specified orientation",
        f"'summon minecraft:item_display {FAUCET_X:.3f} {actual_faucet_y:.3f} {FAUCET_Z:.3f} {{Rotation:[{FACING_YAW}f,0f],Tags:[\"faucet_part\",\"escapemap_faucet_base\"],item:{{id:\"minecraft:paper\",count:1,components:{COMPONENT_BASE}}},item_display:\"fixed\",brightness:{{block:15,sky:15}}}}'",
        f"// Spawn Interaction Zone elevated near the physical handle location",
        f"'summon minecraft:interaction {FAUCET_X:.3f} {interaction_y:.3f} {FAUCET_Z:.3f} {{Tags:[\"faucet_interaction\"],width:{INTERACTION_WIDTH}f,height:{INTERACTION_HEIGHT}f}}'"
    ]
    chunks.append(emit_function("faucet/spawn", spawn_cmds))

    # 2. ATTACH HANDLE FUNCTION
    attach_cmds = [
        f"// Clear 1 specific custom paper model handle item out of the active main hand",
        f"// Spawns the separate handle display matching the base facing orientation",
        f"'execute as @p if items entity @s weapon.mainhand {ITEM_PREDICATE} run summon minecraft:item_display {FAUCET_X:.3f} {handle_y:.3f} {FAUCET_Z:.3f} {{Rotation:[{FACING_YAW}f,0f],Tags:[\"faucet_part\",\"escapemap_faucet_handle\"],item:{{id:\"minecraft:paper\",count:1,components:{COMPONENT_HANDLE}}},item_display:\"fixed\",brightness:{{block:15,sky:15}}}}'",
        f"// Set target state flags",
        f"'execute as @p if items entity @s weapon.mainhand {ITEM_PREDICATE} run tag @e[tag=escapemap_faucet_base,limit=1] add handle_attached'",
        f"'execute as @p if items entity @s weapon.mainhand {ITEM_PREDICATE} run title @s actionbar {{\"text\":\"Handle fixed onto the faucet.\",\"color\":\"blue\"}}'",
        f"'execute as @p if items entity @s weapon.mainhand {ITEM_PREDICATE} run clear @s {ITEM_PREDICATE} 1'"
    ]
    chunks.append(emit_function("faucet/attach_handle", attach_cmds))

    # 3. TICKING INTERACTION HANDLER
    tick_cmds = [
        f"// Evaluate clicks based on interaction block component presence",
        f"'execute as @e[tag=faucet_interaction,nbt={{interaction:{{}}}}] at @s as @e[tag=escapemap_faucet_base,tag=!handle_attached,limit=1] run function {NAMESPACE}:faucet/attach_handle'",
        f"'execute as @e[tag=faucet_interaction,nbt={{interaction:{{}}}}] at @s if entity @e[tag=escapemap_faucet_base,tag=handle_attached,limit=1] run function {NAMESPACE}:faucet/rotate_handle'",
        f"// Purge structural interaction entry to capture future events",
        f"'execute as @e[tag=faucet_interaction,nbt={{interaction:{{}}}}] run data remove entity @s interaction'"
    ]
    chunks.append(emit_function("faucet/main_tick", tick_cmds))

    # 4. ROTATE HANDLE EXECUTION
    rotate_cmds = [
        f"'execute as @e[tag=escapemap_faucet_handle,limit=1] at @s run tp @s ~ ~ ~ ~{ROTATION_PER_CLICK} ~'",
        f"// Global external callback signal execution",
        f"/function {CALLBACK_FUNCTION}"
    ]
    chunks.append(emit_function("faucet/rotate_handle", rotate_cmds))

    # 5. KILL / CLEANUP FUNCTION
    kill_cmds = [
        f"/kill @e[tag=escapemap_faucet_base]",
        f"/kill @e[tag=escapemap_faucet_handle]",
        f"/kill @e[tag=faucet_interaction]"
    ]
    chunks.append(emit_function("faucet/kill", kill_cmds))

    return "".join(chunks)

def main() -> None:
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(generate_faucet_logic(), encoding="utf-8")
    print(f"Generated flat interaction faucet framework with yaw facing tracking: {OUT_FILE}")

if __name__ == "__main__":
    main()