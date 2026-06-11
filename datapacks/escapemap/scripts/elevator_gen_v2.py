#!/usr/bin/env python3
"""
Generate an mcscript file for a multi-station, bidirectional shulker elevator.
Tracks current station state and handles transitions dynamically with pre-peek handoffs.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


GENERATED_DIR = "elevator"


def q(n: float) -> str:
    if abs(n - round(n)) < 1e-9:
        return str(int(round(n)))
    return f"{n:.6f}".rstrip("0").rstrip(".")


def f(n: float) -> str:
    return q(n) + "f"


def safe_name(value: str) -> str:
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-. "
    lowered = value.lower()
    cleaned = "".join(c if c in allowed else "_" for c in lowered)
    cleaned = cleaned.replace(" ", "_").strip("._-")
    if not cleaned:
        raise ValueError("Name/id became empty after sanitizing.")
    return cleaned


def safe_function_path(value: str) -> str:
    value = value.replace("\\", "/").strip()
    if value.endswith(".mcscript"):
        value = value[:-9]
    if value.endswith(".mcfunction"):
        value = value[:-11]
    value = value.strip("/")

    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-/."
    lowered = value.lower()
    cleaned = "".join(c if c in allowed else "_" for c in lowered)
    while "//" in cleaned:
        cleaned = cleaned.replace("//", "/")
    return cleaned.strip("/")


def block_state_nbt(block: str) -> str:
    block = block.strip()
    if "[" not in block:
        return f'{{Name:"{block}"}}'

    name, raw_props = block.split("[", 1)
    raw_props = raw_props.rstrip("]")
    props: list[str] = []
    for part in raw_props.split(","):
        key, value = part.split("=", 1)
        props.append(f'{key.strip()}:"{value.strip()}"')
    return f'{{Name:"{name.strip()}",Properties:{{{",".join(props)}}}}}'


def make_player_nudge_cmds(
        *,
        center_x: float,
        center_z: float,
        y_bottom: float,
        y_top: float,
        tiles: list[dict[str, Any]],
        margin: float,
) -> list[str]:
    rel_xs = [t["rel_x"] for t in tiles]
    rel_zs = [t["rel_z"] for t in tiles]

    min_x = center_x + min(rel_xs) - margin
    max_x = center_x + max(rel_xs) + 1.0 + margin
    min_z = center_z + min(rel_zs) - margin
    max_z = center_z + max(rel_zs) + 1.0 + margin

    y_min = y_bottom - 2
    y_max = y_top + 4
    dx = max_x - min_x
    dy = y_max - y_min
    dz = max_z - min_z

    selector = f"@a[x={q(min_x)},y={q(y_min)},z={q(min_z)},dx={q(dx)},dy={q(dy)},dz={q(dz)}]"
    return [f"/execute as {selector} at @s run tp @s ~ ~0.1 ~"]


def make_mcscript(config: dict[str, Any]) -> str:
    ns = safe_name(config["namespace"])
    eid = safe_name(config["id"])
    path_prefix = safe_function_path(config.get("path_prefix", ""))

    func = f"{ns}:{path_prefix}/{GENERATED_DIR}" if path_prefix else f"{ns}:{GENERATED_DIR}"
    listener = f"{ns}:{path_prefix}/elevator_listener" if path_prefix else f"{ns}:elevator_listener"

    listener_start_cmds = [f"/function {listener}/start"] if config.get("call_listeners") else []
    listener_end_cmds = [f"/function {listener}/end"] if config.get("call_listeners") else []

    obj = f"{ns}_{eid}"
    base_tag = f"{ns}_{eid}"
    tag_a = f"{ns}_{eid}_a"
    tag_b = f"{ns}_{eid}_b"
    display_tag = f"{ns}_{eid}_display"

    scale = float(config.get("scale", 1.0))
    center_x = float(config["x"])
    center_z = float(config["z"])
    tiles = config["tiles"]
    player_margin = float(config.get("player_margin", 0.5))
    display_y_offset = float(config.get("display_y_offset", 1.0))

    stations = config["stations"]
    if len(stations) < 2:
        raise ValueError("You must define at least two stations in the config.")

    all_ys = [float(s["y"]) for s in stations]
    global_min_y = min(all_ys)
    global_max_y = max(all_ys)

    display_scale_y = config.get("display_y_scale", 0.08)
    trns_y = -display_scale_y

    shulker_nbt = lambda l, c: f'{{Tags:["{base_tag}","{base_tag}_{l}"],NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,Peek:0b,AttachFace:0b,Color:{c}b,active_effects:[{{id:"minecraft:invisibility",amplifier:0b,duration:2147483647,show_particles:0b}}],attributes:[{{id:"minecraft:scale",base:{q(scale)}}}]}}'
    display_nbt = lambda block: f'{{Tags:["{base_tag}","{display_tag}"],block_state:{block_state_nbt(block)},interpolation_duration:1,teleport_duration:1,transformation:{{translation:[{f(-scale/2)},{f(trns_y)},{f(-scale/2)}],scale:[{f(config.get("display_scale", 1.0))},{f(display_scale_y)},{f(config.get("display_scale", 1.0))}],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}}}'

    summon_base_entities = []
    summon_displays = []
    for tile in tiles:
        rx, rz, block = float(tile["rel_x"]), float(tile["rel_z"]), tile["block"]
        ex, ez = center_x + rx + 0.5, center_z + rz + 0.5

        summon_base_entities.append(f"/summon minecraft:shulker {q(ex)} ~ {q(ez)} {shulker_nbt('a', config.get('color_a', 14))}")
        summon_base_entities.append(f"/summon minecraft:shulker {q(ex)} ~-{q(scale)} {q(ez)} {shulker_nbt('b', config.get('color_b', 15))}")
        summon_displays.append(f"/summon minecraft:block_display {q(ex)} ~{q(display_y_offset)} {q(ez)} {display_nbt(block)}")

    player_nudge = make_player_nudge_cmds(center_x=center_x, center_z=center_z, y_bottom=global_min_y, y_top=global_max_y, tiles=tiles, margin=player_margin)

    lines = [
        f"#file: ./{GENERATED_DIR}/load",
        f"/scoreboard objectives add {obj} dummy",
        f"/scoreboard players set #running {obj} 0",
        f"/scoreboard players set #tick_divisor {obj} {config.get('tick_divisor', 1)}",
        f"/scoreboard players set #current_station {obj} 0",
        "",
        f"#file: ./{GENERATED_DIR}/reset",
        f"/scoreboard players set #running {obj} 0",
        f"/function {func}/despawn_entities",
        f"/scoreboard players set #current_station {obj} 0",
        f"/function {func}/place_station_0_blocks",
    ]

    for idx, station in enumerate(stations):
        if idx == 0:
            continue
        lines.extend([
            f"/function {func}/clear_station_{idx}_blocks",
        ])

    lines.extend([""])

    # Generate Block Placement and Clearing files per station
    for idx, station in enumerate(stations):
        sy = float(station["y"])
        set_cmds, clear_cmds = [], []
        for tile in tiles:
            rx, rz, block = float(tile["rel_x"]), float(tile["rel_z"]), tile["block"]
            bx, bz = math.floor(center_x + rx), math.floor(center_z + rz)
            set_cmds.append(f"/setblock {bx} {math.floor(sy)} {bz} {block}")
            clear_cmds.append(f"/setblock {bx} {math.floor(sy)} {bz} minecraft:air")

        lines.extend([
            f"#file: ./{GENERATED_DIR}/place_station_{idx}_blocks",
            *set_cmds,
            "",
            f"#file: ./{GENERATED_DIR}/clear_station_{idx}_blocks",
            *clear_cmds,
            ""
        ])

    # Named Station Triggers
    for idx, station in enumerate(stations):
        sname = safe_name(station["name"])
        lines.extend([
            f"#file: ./{GENERATED_DIR}/go_to_{sname}",
            f"/execute if score #running {obj} matches 0 unless score #current_station {obj} matches {idx} run scoreboard players set #target_station {obj} {idx}",
            f"/execute if score #running {obj} matches 0 unless score #current_station {obj} matches {idx} run function {func}/prepare_trip",
            ""
        ])

    # Transition handling engine
    lines.extend([
        f"#file: ./{GENERATED_DIR}/prepare_trip",
        f"/scoreboard players set #running {obj} 1",
        *listener_start_cmds,
    ])

    # Calculate directions FIRST before making clearing calls or summoning setup blocks
    for idx_from, st_from in enumerate(stations):
        for idx_to, st_to in enumerate(stations):
            if idx_from == idx_to:
                continue
            y_from = float(st_from["y"])
            y_to = float(st_to["y"])
            dist = abs(y_to - y_from)
            cycles_needed = math.ceil((dist / (scale * 2)) * 2)
            dsign = 1 if y_to > y_from else -1

            lines.extend([
                f"/execute if score #current_station {obj} matches {idx_from} if score #target_station {obj} matches {idx_to} run scoreboard players set #dir_sign {obj} {dsign}",
                f"/execute if score #current_station {obj} matches {idx_from} if score #target_station {obj} matches {idx_to} run scoreboard players set #max_cycles {obj} {cycles_needed}"
            ])

    # Clear blocks at the current departure station
    for idx, station in enumerate(stations):
        lines.append(f"/execute if score #current_station {obj} matches {idx} run function {func}/clear_station_{idx}_blocks")

    # Summon layout relative to current station Y coordinates
    for idx, station in enumerate(stations):
        sy = float(station["y"])
        lines.extend([
            f"/execute if score #current_station {obj} matches {idx} run execute positioned {q(center_x)} {q(sy)} {q(center_z)} run function {func}/summon_entities"
        ])

    lines.extend([
        f"/function {func}/calculate_distance",
        *player_nudge,
        "",
        f"#file: ./{GENERATED_DIR}/summon_entities",
        *summon_base_entities,
        *summon_displays,
        f"/execute if score #dir_sign {obj} matches -1 as @e[type=minecraft:shulker,tag={base_tag}] at @s run tp @s ~ ~-1.0 ~",
        # PRE-PEEK INITIALIZATION: Set both starting layers to Peek: 100b instantly when preparing downward trips
        f"/execute if score #dir_sign {obj} matches -1 run data merge entity @e[type=minecraft:shulker,tag={base_tag},limit=1] {{Peek:100b}}",
        f"/execute if score #dir_sign {obj} matches -1 as @e[type=minecraft:shulker,tag={base_tag}] run data merge entity @s {{Peek:100b}}",
        "",
        f"/function {func}/calculate_distance",
    ])

    lines.extend([
        f"/scoreboard players set #a {obj} 0",
        f"/scoreboard players set #b {obj} 0",
        f"/scoreboard players set #active {obj} 0",
        f"/scoreboard players set #cycle {obj} 0",
        f"/scoreboard players set #tick {obj} 0",
        "",
        f"#file: ./{GENERATED_DIR}/tick",
        f"/execute if score #running {obj} matches 1 run function {func}/force_attach_face",
        f"/scoreboard players set #do_step {obj} 0",
        f"/execute if score #running {obj} matches 1 run scoreboard players add #tick {obj} 1",
        f"/execute if score #running {obj} matches 1 if score #tick {obj} >= #tick_divisor {obj} run scoreboard players set #do_step {obj} 1",
        f"/execute if score #do_step {obj} matches 1 run scoreboard players set #tick {obj} 0",
        f"/execute if score #do_step {obj} matches 1 if score #active {obj} matches 0 run function {func}/step_a",
        f"/execute if score #do_step {obj} matches 1 if score #active {obj} matches 1 run function {func}/step_b",
        "",
        f"#file: ./{GENERATED_DIR}/force_attach_face",
        f"/execute as @e[type=minecraft:shulker,tag={base_tag}] run data merge entity @s {{AttachFace:0b}}",
        "",
        f"#file: ./{GENERATED_DIR}/step_a",
        f"/scoreboard players add #a {obj} 1",

        # UP
        f"/execute if score #dir_sign {obj} matches 1 as @e[type=minecraft:shulker,tag={tag_a}] store result entity @s Peek byte 1 run scoreboard players get #a {obj}",

        # DOWN
        f"/scoreboard players set #peek_tmp {obj} 100",
        f"/execute if score #dir_sign {obj} matches -1 run scoreboard players operation #peek_tmp {obj} -= #a {obj}",
        f"/execute if score #dir_sign {obj} matches -1 as @e[type=minecraft:shulker,tag={tag_a}] store result entity @s Peek byte 1 run scoreboard players get #peek_tmp {obj}",

        f"/execute if score #dir_sign {obj} matches 1 run execute as @e[type=minecraft:block_display,tag={display_tag}] at @s run tp @s ~ ~{q(scale / 100)} ~",
        f"/execute if score #dir_sign {obj} matches -1 run execute as @e[type=minecraft:block_display,tag={display_tag}] at @s run tp @s ~ ~-{q(scale / 100)} ~",

        f"/execute if score #a {obj} matches 100.. run function {func}/finish_a",
        "",
        f"#file: ./{GENERATED_DIR}/step_b",
        f"/scoreboard players add #b {obj} 1",

        # UP
        f"/execute if score #dir_sign {obj} matches 1 as @e[type=minecraft:shulker,tag={tag_b}] store result entity @s Peek byte 1 run scoreboard players get #b {obj}",

        # DOWN
        f"/scoreboard players set #peek_tmp {obj} 100",
        f"/execute if score #dir_sign {obj} matches -1 run scoreboard players operation #peek_tmp {obj} -= #b {obj}",
        f"/execute if score #dir_sign {obj} matches -1 as @e[type=minecraft:shulker,tag={tag_b}] store result entity @s Peek byte 1 run scoreboard players get #peek_tmp {obj}",

        f"/execute if score #dir_sign {obj} matches 1 run execute as @e[type=minecraft:block_display,tag={display_tag}] at @s run tp @s ~ ~{q(scale / 100)} ~",
        f"/execute if score #dir_sign {obj} matches -1 run execute as @e[type=minecraft:block_display,tag={display_tag}] at @s run tp @s ~ ~-{q(scale / 100)} ~",

        f"/execute if score #b {obj} matches 100.. run function {func}/finish_b",
        "",
        f"#file: ./{GENERATED_DIR}/finish_a",
        f"/execute if score #dir_sign {obj} matches 1 run execute as @e[type=minecraft:shulker,tag={tag_b}] at @s run tp @s ~ ~{q(scale * 2)} ~",
        f"/execute if score #dir_sign {obj} matches -1 run execute as @e[type=minecraft:shulker,tag={tag_a}] at @s run tp @s ~ ~-{q(scale * 2)} ~",
        f"/execute as @e[type=minecraft:shulker,tag={tag_a},limit=1] at @s run function {func}/nudge_players",

        # HANDOFF CHANGE: Going UP clears peek to 0. Going DOWN sets peek to 100 immediately upon dropping!
        f"/execute if score #dir_sign {obj} matches 1 as @e[type=minecraft:shulker,tag={tag_a}] run data merge entity @s {{Peek:0b,AttachFace:0b}}",
        f"/execute if score #dir_sign {obj} matches -1 as @e[type=minecraft:shulker,tag={tag_a}] run data merge entity @s {{Peek:100b,AttachFace:0b}}",

        f"/scoreboard players set #a {obj} 0",
        f"/scoreboard players set #active {obj} 1",
        f"/scoreboard players add #cycle {obj} 1",
        f"/execute if score #cycle {obj} >= #max_cycles {obj} run function {func}/arrive",
        "",
        f"#file: ./{GENERATED_DIR}/finish_b",
        f"/execute if score #dir_sign {obj} matches 1 run execute as @e[type=minecraft:shulker,tag={tag_a}] at @s run tp @s ~ ~{q(scale * 2)} ~",
        f"/execute if score #dir_sign {obj} matches -1 run execute as @e[type=minecraft:shulker,tag={tag_b}] at @s run tp @s ~ ~-{q(scale * 2)} ~",
        f"/execute as @e[type=minecraft:shulker,tag={tag_b},limit=1] at @s run function {func}/nudge_players",

        # HANDOFF CHANGE: Going UP clears peek to 0. Going DOWN sets peek to 100 immediately upon dropping!
        f"/execute if score #dir_sign {obj} matches 1 as @e[type=minecraft:shulker,tag={tag_b}] run data merge entity @s {{Peek:0b,AttachFace:0b}}",
        f"/execute if score #dir_sign {obj} matches -1 as @e[type=minecraft:shulker,tag={tag_b}] run data merge entity @s {{Peek:100b,AttachFace:0b}}",

        f"/scoreboard players set #b {obj} 0",
        f"/scoreboard players set #active {obj} 0",
        f"/scoreboard players add #cycle {obj} 1",
        f"/execute if score #cycle {obj} >= #max_cycles {obj} run function {func}/arrive",
        "",
        f"#file: ./{GENERATED_DIR}/nudge_players",
        *player_nudge,
        "",
        f"#file: ./{GENERATED_DIR}/arrive",
        f"/scoreboard players set #running {obj} 0",
        f"/scoreboard players operation #current_station {obj} = #target_station {obj}",
    ])

    for idx, station in enumerate(stations):
        lines.append(f"/execute if score #current_station {obj} matches {idx} run function {func}/place_station_{idx}_blocks")

    lines.extend([
        *player_nudge,
        *listener_end_cmds,
        f"/execute as @e[type=minecraft:shulker,tag={base_tag}] run data merge entity @s {{Peek:0b,AttachFace:0b}}",
        f"/function {func}/despawn_entities",
        "",
        f"#file: ./{GENERATED_DIR}/despawn_entities",
        f"/execute as @e[tag={base_tag}] at @s run tp @s {q(config.get('despawn_x', 0))} {q(config.get('despawn_y', -64))} {q(config.get('despawn_z', 0))}",
        f"/kill @e[type=minecraft:shulker,tag={base_tag}]",
        f"/kill @e[type=minecraft:block_display,tag={display_tag}]",
        "",
        f"#file: ./{GENERATED_DIR}/stop",
        f"/scoreboard players set #running {obj} 0",
        f"/execute as @e[type=minecraft:shulker,tag={base_tag}] run data merge entity @s {{Peek:0b,AttachFace:0b}}",
        f"/kill @e[type=minecraft:shulker,tag={base_tag}]",
        f"/kill @e[type=minecraft:block_display,tag={display_tag}]",
        "",
        f"#file: ./{GENERATED_DIR}/cleanup",
        f"/scoreboard players set #running {obj} 0",
        f"/function {func}/despawn_entities",
    ])

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate multi-station bidirectional shulker elevators.")
    parser.add_argument("--config", required=True, help="Path to input JSON format profile.")
    parser.add_argument("--out", required=True, help="Path to output target mcscript block.")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config structure configuration at: {config_path}")

    with config_path.open("r", encoding="utf-8") as f_in:
        config = json.load(f_in)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(make_mcscript(config), encoding="utf-8")

    print(f"Generated seamless handoff downward contraction file to: {out_path}")


if __name__ == "__main__":
    main()