#!/usr/bin/env python3
"""
Generate one mcscript file for a one-use smooth two-layer shulker elevator.

This does not generate a full datapack. It writes one .mcscript file compatible
with an existing datapack/mcscript workflow.

Important path behavior:
  --path-prefix my_path/subpath

Generated mcscript chunks:
  #file: ./elevator/load
  #file: ./elevator/start
  #file: ./elevator/tick
  ...

Function calls:
  namespace:my_path/subpath/elevator/load
  namespace:my_path/subpath/elevator/start
  namespace:my_path/subpath/elevator/tick
  ...

Example:
  python gen_shulker_elevator_mcscript.py \
    --out ./scripts/elevator.mcscript \
    --namespace mypack \
    --path-prefix my_path/subpath \
    --id main \
    --x 0 --z 0 \
    --start-y 64 --end-y 84 \
    --width 5 --depth 5 \
    --scale 1 \
    --platform-block minecraft:smooth_stone \
    --tick-divisor 1

In-game:
  /function mypack:my_path/subpath/elevator/reset
  /function mypack:my_path/subpath/elevator/start

Your existing datapack should call:
  mypack:my_path/subpath/elevator/load
  mypack:my_path/subpath/elevator/tick
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable


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

    cleaned = cleaned.strip("/")

    if not cleaned:
        return ""

    return cleaned


def listener_prefix(namespace: str, path_prefix: str) -> str:
    if path_prefix:
        return f"{namespace}:{path_prefix}/elevator_listener"
    return f"{namespace}:elevator_listener"


def function_prefix(namespace: str, path_prefix: str) -> str:
    if path_prefix:
        return f"{namespace}:{path_prefix}/{GENERATED_DIR}"
    return f"{namespace}:{GENERATED_DIR}"


def block_state_nbt(block: str) -> str:
    """
    Supports simple block names like minecraft:stone.

    For block states such as minecraft:oak_slab[type=top], this makes:
      block_state:{Name:"minecraft:oak_slab",Properties:{type:"top"}}
    """
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


def block_positions(
        center_x: float,
        center_z: float,
        width: int,
        depth: int,
) -> Iterable[tuple[int, int]]:
    cx = math.floor(center_x)
    cz = math.floor(center_z)

    x0 = cx - ((width - 1) // 2)
    z0 = cz - ((depth - 1) // 2)

    for ix in range(width):
        for iz in range(depth):
            yield x0 + ix, z0 + iz


def shulker_positions(
        center_x: float,
        center_z: float,
        width: int,
        depth: int,
        spacing: float,
) -> Iterable[tuple[float, float]]:
    x0 = center_x - ((width - 1) * spacing / 2)
    z0 = center_z - ((depth - 1) * spacing / 2)

    for ix in range(width):
        for iz in range(depth):
            yield x0 + ix * spacing, z0 + iz * spacing


def set_platform_cmds(
        y: float,
        *,
        center_x: float,
        center_z: float,
        width: int,
        depth: int,
        block: str,
) -> list[str]:
    by = math.floor(y)
    return [
        f"/setblock {x} {by} {z} {block}"
        for x, z in block_positions(center_x, center_z, width, depth)
    ]


def clear_platform_cmds(
        y: float,
        *,
        center_x: float,
        center_z: float,
        width: int,
        depth: int,
) -> list[str]:
    by = math.floor(y)
    return [
        f"/setblock {x} {by} {z} minecraft:air"
        for x, z in block_positions(center_x, center_z, width, depth)
    ]


def summon_shulker_cmd(
        x: float,
        y: float,
        z: float,
        *,
        namespace: str,
        elevator_id: str,
        layer: str,
        scale: float,
        color: int,
) -> str:
    layer_tag = f"{namespace}_{elevator_id}_{layer}"
    base_tag = f"{namespace}_{elevator_id}"

    nbt = (
        "{"
        f'Tags:["{base_tag}","{layer_tag}"],'
        "NoAI:1b,"
        "Silent:1b,"
        "Invulnerable:1b,"
        "PersistenceRequired:1b,"
        "Peek:0b,"
        "AttachFace:0b,"
        f"Color:{color}b,"
        'active_effects:[{id:"minecraft:invisibility",amplifier:0b,duration:2147483647,show_particles:0b}],'
        f'attributes:[{{id:"minecraft:scale",base:{q(scale)}}}]'
        "}"
    )

    return f"/summon minecraft:shulker {q(x)} {q(y)} {q(z)} {nbt}"


def summon_display_cmd(
        x: float,
        y: float,
        z: float,
        *,
        namespace: str,
        elevator_id: str,
        block: str,
        visual_scale: float,
        visual_y_scale: float,
) -> str:
    display_tag = f"{namespace}_{elevator_id}_display"
    base_tag = f"{namespace}_{elevator_id}"

    nbt = (
        "{"
        f'Tags:["{base_tag}","{display_tag}"],'
        f"block_state:{block_state_nbt(block)},"
        "interpolation_duration:1,"
        "teleport_duration:1,"
        "transformation:{"
        f"translation:[{f(-visual_scale / 2)},{f(0)},{f(-visual_scale / 2)}],"
        f"scale:[{f(visual_scale)},{f(visual_y_scale)},{f(visual_scale)}],"
        "left_rotation:[0f,0f,0f,1f],"
        "right_rotation:[0f,0f,0f,1f]"
        "}"
        "}"
    )

    return f"/summon minecraft:block_display {q(x)} {q(y)} {q(z)} {nbt}"


def make_player_nudge_cmds(
        *,
        center_x: float,
        center_z: float,
        y_min: float,
        y_max: float,
        width: int,
        depth: int,
        margin: float,
) -> list[str]:
    min_x = center_x - width / 2 - margin
    min_z = center_z - depth / 2 - margin
    max_x = center_x + width / 2 + margin
    max_z = center_z + depth / 2 + margin

    min_y = min(y_min, y_max) - 2
    max_y = max(y_min, y_max) + 4

    dx = max_x - min_x
    dy = max_y - min_y
    dz = max_z - min_z

    selector = (
        f"@a[x={q(min_x)},y={q(min_y)},z={q(min_z)},"
        f"dx={q(dx)},dy={q(dy)},dz={q(dz)}]"
    )

    return [f"/execute as {selector} at @s run tp @s ~ ~0.1 ~"]


def make_mcscript(args: argparse.Namespace) -> str:
    ns = args.namespace
    eid = args.id
    path_prefix = args.path_prefix

    func = function_prefix(ns, path_prefix)

    listener = listener_prefix(ns, path_prefix)
    listener_start_cmds = [f"/function {listener}/start"] if args.call_listeners else []
    listener_end_cmds = [f"/function {listener}/end"] if args.call_listeners else []

    obj = f"{ns}_{eid}"
    base_tag = f"{ns}_{eid}"

    tag_a = f"{ns}_{eid}_a"
    tag_b = f"{ns}_{eid}_b"

    display_tag = f"{ns}_{eid}_display"

    y_step = args.scale * 2
    visual_step = args.scale / 100

    # User-tested fix:
    # Previous logic under-counted by half for the actual A/B alternation.
    cycles_exact = ((args.end_y - args.start_y) / y_step) * 2

    if cycles_exact < 0:
        raise ValueError("end-y must be greater than or equal to start-y.")

    if not args.allow_overshoot and abs(cycles_exact - round(cycles_exact)) > 1e-9:
        raise ValueError(
            f"Exact stopping is impossible with start_y={args.start_y}, "
            f"end_y={args.end_y}, scale={args.scale}. "
            f"Movement quantum after A/B alternation is 2*scale/2={q(args.scale)}. "
            f"Use an end-y divisible by {q(args.scale)} from start-y, "
            f"or pass --allow-overshoot."
        )

    max_cycles = math.ceil(cycles_exact)

    if max_cycles <= 0:
        raise ValueError("Elevator height must be positive.")

    spacing = args.spacing if args.spacing is not None else args.scale

    layer_a_y = args.start_y
    layer_b_y = args.start_y - args.scale

    display_y = args.start_y + args.display_y_offset

    summon_displays: list[str] = []

    summon_a: list[str] = []
    summon_b: list[str] = []

    for x, z in shulker_positions(args.x, args.z, args.width, args.depth, spacing):
        summon_a.append(
            summon_shulker_cmd(
                x,
                layer_a_y,
                z,
                namespace=ns,
                elevator_id=eid,
                layer="a",
                scale=args.scale,
                color=args.color_a,
            )
        )
        summon_b.append(
            summon_shulker_cmd(
                x,
                layer_b_y,
                z,
                namespace=ns,
                elevator_id=eid,
                layer="b",
                scale=args.scale,
                color=args.color_b,
            )
        )

        summon_displays.append(
            summon_display_cmd(
                x,
                display_y,
                z,
                namespace=ns,
                elevator_id=eid,
                block=args.platform_block,
                visual_scale=args.display_scale,
                visual_y_scale=args.display_y_scale,
            )
        )

    platform_width = args.platform_width or args.width
    platform_depth = args.platform_depth or args.depth

    bottom_blocks = set_platform_cmds(
        args.start_y,
        center_x=args.x,
        center_z=args.z,
        width=platform_width,
        depth=platform_depth,
        block=args.platform_block,
    )

    top_blocks = set_platform_cmds(
        args.end_y,
        center_x=args.x,
        center_z=args.z,
        width=platform_width,
        depth=platform_depth,
        block=args.platform_block,
    )

    clear_bottom = clear_platform_cmds(
        args.start_y,
        center_x=args.x,
        center_z=args.z,
        width=platform_width,
        depth=platform_depth,
    )

    clear_top = clear_platform_cmds(
        args.end_y,
        center_x=args.x,
        center_z=args.z,
        width=platform_width,
        depth=platform_depth,
    )

    player_nudge = make_player_nudge_cmds(
        center_x=args.x,
        center_z=args.z,
        y_min=args.start_y,
        y_max=args.end_y,
        width=platform_width,
        depth=platform_depth,
        margin=args.player_margin,
    )

    lines: list[str] = []

    lines += [
        "# Generated shulker elevator mcscript.",
        f"# Namespace: {ns}",
        f"# Function prefix: {func}",
        f"# Generated #file base: ./{GENERATED_DIR}",
        f"# Start platform Y: {q(args.start_y)}",
        f"# End platform Y: {q(args.end_y)}",
        f"# Scale: {q(args.scale)}",
        f"# Per-cycle movement: {q(y_step)}",
        f"# Visual per-step movement: {q(visual_step)}",
        f"# Cycles: {max_cycles}",
        "",
        f"#file: ./{GENERATED_DIR}/load",
        f"/scoreboard objectives add {obj} dummy",
        f"/scoreboard players set #a {obj} 0",
        f"/scoreboard players set #b {obj} 0",
        f"/scoreboard players set #active {obj} 0",
        f"/scoreboard players set #running {obj} 0",
        f"/scoreboard players set #cycle {obj} 0",
        f"/scoreboard players set #tick {obj} 0",
        f"/scoreboard players set #do_step {obj} 0",
        f"/scoreboard players set #tick_divisor {obj} {args.tick_divisor}",
        "",
        f"#file: ./{GENERATED_DIR}/reset",
        f"/scoreboard players set #running {obj} 0",
        f"/scoreboard players set #a {obj} 0",
        f"/scoreboard players set #b {obj} 0",
        f"/scoreboard players set #active {obj} 0",
        f"/scoreboard players set #cycle {obj} 0",
        f"/scoreboard players set #tick {obj} 0",
        f"/function {func}/despawn_entities",
        *bottom_blocks,
        *clear_top,
        "",
        f"#file: ./{GENERATED_DIR}/start",
        f"/scoreboard players set #a {obj} 0",
        f"/scoreboard players set #b {obj} 0",
        f"/scoreboard players set #active {obj} 0",
        f"/scoreboard players set #cycle {obj} 0",
        f"/scoreboard players set #tick {obj} 0",
        f"/scoreboard players set #running {obj} 1",
        *listener_start_cmds,
        *clear_bottom,
        *summon_a,
        *summon_b,
        *summon_displays,
        *player_nudge,
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
        f"/execute as @e[type=minecraft:shulker,tag={tag_a}] store result entity @s Peek byte 1 run scoreboard players get #a {obj}",
        f"/execute as @e[type=minecraft:block_display,tag={display_tag}] at @s run tp @s ~ ~{q(visual_step)} ~",
        f"/execute if score #a {obj} matches 100.. run function {func}/finish_a",
        "",
        f"#file: ./{GENERATED_DIR}/step_b",
        f"/scoreboard players add #b {obj} 1",
        f"/execute as @e[type=minecraft:shulker,tag={tag_b}] store result entity @s Peek byte 1 run scoreboard players get #b {obj}",
        f"/execute as @e[type=minecraft:block_display,tag={display_tag}] at @s run tp @s ~ ~{q(visual_step)} ~",
        f"/execute if score #b {obj} matches 100.. run function {func}/finish_b",
        "",
        f"#file: ./{GENERATED_DIR}/finish_a",
        f"/execute as @e[type=minecraft:shulker,tag={tag_b}] at @s run tp @s ~ ~{q(y_step)} ~",
        f"/execute as @e[type=minecraft:shulker,tag={tag_a},limit=1] at @s run function {func}/nudge_players",
        f"/execute as @e[type=minecraft:shulker,tag={tag_a}] run data merge entity @s {{Peek:0b,AttachFace:0b}}",
        f"/scoreboard players set #a {obj} 0",
        f"/scoreboard players set #active {obj} 1",
        f"/scoreboard players add #cycle {obj} 1",
        f"/execute if score #cycle {obj} matches {max_cycles}.. run function {func}/arrive_top",
        "",
        f"#file: ./{GENERATED_DIR}/finish_b",
        f"/execute as @e[type=minecraft:shulker,tag={tag_a}] at @s run tp @s ~ ~{q(y_step)} ~",
        f"/execute as @e[type=minecraft:shulker,tag={tag_b},limit=1] at @s run function {func}/nudge_players",
        f"/execute as @e[type=minecraft:shulker,tag={tag_b}] run data merge entity @s {{Peek:0b,AttachFace:0b}}",
        f"/scoreboard players set #b {obj} 0",
        f"/scoreboard players set #active {obj} 0",
        f"/scoreboard players add #cycle {obj} 1",
        f"/execute if score #cycle {obj} matches {max_cycles}.. run function {func}/arrive_top",
        "",
        f"#file: ./{GENERATED_DIR}/nudge_players",
        *player_nudge,
        "",
        f"#file: ./{GENERATED_DIR}/arrive_top",
        f"/scoreboard players set #running {obj} 0",
        *top_blocks,
        *player_nudge,
        *listener_end_cmds,
        f"/execute as @e[type=minecraft:shulker,tag={base_tag}] run data merge entity @s {{Peek:0b,AttachFace:0b}}",
        f"/function {func}/despawn_entities",
        "",
        f"#file: ./{GENERATED_DIR}/despawn_entities",
        f"/execute as @e[tag={base_tag}] at @s run tp @s {q(args.despawn_x)} {q(args.despawn_y)} {q(args.despawn_z)}",
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
    ]

    return "\n".join(lines) + "\n"


def write_script(args: argparse.Namespace) -> None:
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(make_mcscript(args), encoding="utf-8")

    func = function_prefix(args.namespace, args.path_prefix)

    print(f"Wrote mcscript file: {out}")
    print()
    print("Generated mcscript #file chunks are under:")
    print(f"  ./{GENERATED_DIR}/load")
    print(f"  ./{GENERATED_DIR}/reset")
    print(f"  ./{GENERATED_DIR}/start")
    print(f"  ./{GENERATED_DIR}/tick")
    print()
    print("Function calls use:")
    print(f"  {func}/load")
    print(f"  {func}/reset")
    print(f"  {func}/start")
    print(f"  {func}/tick")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--out",
        required=True,
        help="Filesystem path where the generated .mcscript source should be written.",
    )

    parser.add_argument(
        "--namespace",
        required=True,
        type=safe_name,
        help="Datapack namespace, for example mypack.",
    )

    parser.add_argument(
        "--path-prefix",
        default="",
        type=safe_function_path,
        help=(
            "Function path prefix before /elevator. Example: my_path/subpath. "
            "Function calls become namespace:my_path/subpath/elevator/start. "
            "The #file chunks remain ./elevator/start."
        ),
    )

    parser.add_argument("--id", default="main", type=safe_name)

    parser.add_argument("--x", type=float, required=True)
    parser.add_argument("--z", type=float, required=True)

    parser.add_argument("--start-y", type=float, required=True)
    parser.add_argument("--end-y", type=float, required=True)

    parser.add_argument(
        "--width",
        type=int,
        required=True,
        help="Number of shulkers/displays on X. Also used as default platform width.",
    )

    parser.add_argument(
        "--depth",
        type=int,
        required=True,
        help="Number of shulkers/displays on Z. Also used as default platform depth.",
    )

    parser.add_argument(
        "--platform-width",
        type=int,
        default=None,
        help="Optional block-platform width. Defaults to --width.",
    )

    parser.add_argument(
        "--platform-depth",
        type=int,
        default=None,
        help="Optional block-platform depth. Defaults to --depth.",
    )

    parser.add_argument(
        "--platform-block",
        default="minecraft:smooth_stone",
        help=(
            "Block used for the start/end platforms and block_display visuals. "
            "Examples: minecraft:stone, minecraft:oak_planks, minecraft:oak_slab[type=top]."
        ),
    )

    parser.add_argument("--scale", type=float, default=1.0)

    parser.add_argument(
        "--spacing",
        type=float,
        default=None,
        help="Spacing between shulkers/displays. Defaults to scale.",
    )

    parser.add_argument(
        "--tick-divisor",
        type=int,
        default=1,
        help="1 = every tick, 2 = every other tick, 3 = every third tick, etc.",
    )

    parser.add_argument(
        "--player-margin",
        type=float,
        default=0.5,
        help="Extra x/z margin around the platform for player nudging.",
    )

    parser.add_argument(
        "--display-y-offset",
        type=float,
        default=1.0,
        help="Visual platform offset above each shulker position.",
    )

    parser.add_argument(
        "--display-scale",
        type=float,
        default=1.0,
        help="X/Z scale of each block_display visual tile.",
    )

    parser.add_argument(
        "--display-y-scale",
        type=float,
        default=0.08,
        help="Y thickness of each block_display visual tile.",
    )

    parser.add_argument("--color-a", type=int, default=10)
    parser.add_argument("--color-b", type=int, default=11)

    parser.add_argument(
        "--allow-overshoot",
        action="store_true",
        help="Allow final cycle to pass end-y if height is not divisible by scale.",
    )

    parser.add_argument(
        "--despawn-x",
        type=float,
        default=0,
        help="X coordinate where shulkers/displays are teleported before being killed.",
    )

    parser.add_argument(
        "--despawn-y",
        type=float,
        default=-512,
        help="Y coordinate where shulkers/displays are teleported before being killed.",
    )

    parser.add_argument(
        "--despawn-z",
        type=float,
        default=0,
        help="Z coordinate where shulkers/displays are teleported before being killed.",
    )

    parser.add_argument(
        "--call-listeners",
        action="store_true",
        help=(
            "Call namespace:<path-prefix>/elevator_listener/start when the elevator starts "
            "and namespace:<path-prefix>/elevator_listener/end when it arrives."
        ),
    )

    args = parser.parse_args()

    if args.width <= 0 or args.depth <= 0:
        raise ValueError("width and depth must be positive.")

    if args.platform_width is not None and args.platform_width <= 0:
        raise ValueError("platform-width must be positive.")

    if args.platform_depth is not None and args.platform_depth <= 0:
        raise ValueError("platform-depth must be positive.")

    if args.scale <= 0:
        raise ValueError("scale must be positive.")

    if args.spacing is not None and args.spacing <= 0:
        raise ValueError("spacing must be positive.")

    if args.tick_divisor <= 0:
        raise ValueError("tick-divisor must be positive.")

    if args.player_margin < 0:
        raise ValueError("player-margin cannot be negative.")

    if args.display_scale <= 0:
        raise ValueError("display-scale must be positive.")

    if args.display_y_scale <= 0:
        raise ValueError("display-y-scale must be positive.")

    if not (0 <= args.color_a <= 15 and 0 <= args.color_b <= 15):
        raise ValueError("Shulker colors must be 0..15.")

    return args


def main() -> None:
    args = parse_args()
    write_script(args)


if __name__ == "__main__":
    main()