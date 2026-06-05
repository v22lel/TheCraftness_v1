# Updated data structure: Each joint now has its snap position
# and an array of particle positions that represent the path up to that joint.
JOINTS = [
    {
        "joint": (-34, -33, -36),
        "path": [
            (-34, -34, -33), (-33, -33, -33), (-32, -33, -33), (-31, -32, -34),
            (-31, -32, -35), (-30, -31, -36), (-30, -31, -37), (-30, -31, -38),
            (-31, -32, -39), (-32, -32, -40), (-33, -33, -41), (-34, -34, -41),
            (-35, -35, -41), (-36, -36, -40), (-37, -37, -39), (-38, -37, -38),
            (-38, -37, -37), (-38, -37, -36), (-38, -36, -35), (-37, -35, -34)
        ]
    },
    {
        "joint": (-35, -34, -33),
        "path": [
            (-35, -34, -33), (-35, -34, -32), (-35, -34, -31), (-37, -35, -33),
            (-37, -35, -32)
        ]
    },
    {
        "joint": (-36, -35, -31),
        "path": [
            (-35, -34, -30), (-36, -34, -29), (-37, -35, -29), (-38, -36, -31),
            (-38, -36, -30)
        ]
    },
    {
        "joint": (-37, -35, -29),
        "path": [
            (-37, -35, -28), (-37, -35, -27), (-39, -36, -29), (-40, -37, -28)
        ]
    },
    {
        "joint": (-38, -36, -27),
        "path": [
            (-38, -36, -26), (-39, -36, -26), (-41, -38, -27)
        ]
    },
    {
        "joint": (-40, -37, -26),
        "path": [
            (-40, -37, -25), (-41, -38, -24), (-42, -39, -26), (-43, -40, -25),
            (-43, -40, -24)
        ]
    },
    {
        "joint": (-42, -39, -24),
        "path": [
            (-41, -38, -23), (-42, -39, -22), (-44, -41, -23), (-44, -41, -22)
        ]
    },
    {
        "joint": (-42, -39, -22),
        "path": [
            (-42, -39, -21), (-42, -39, -20), (-44, -41, -21), (-44, -41, -20)
        ]
    },
    {
        "joint": (-42, -39, -20),
        "path": [
            (-42, -39, -19), (-44, -41, -19), (-44, -41, -18)
        ]
    },
    {
        "joint": (-42, -39, -18),
        "path": [
            (-41, -38, -18), (-43, -40, -17), (-42, -39, -16)
        ]
    },
    {
        "joint": (-41, -38, -17),
        "path": [
            (-40, -37, -18), (-39, -36, -17), (-39, -36, -16), (-39, -36, -15),
            (-40, -37, -15), (-41, -38, -15)
        ]
    }
]

CURSOR_DISTANCE = 53
PARTICLE = "minecraft:dust{color:[0.15,1.0,0.2],scale:2}"

out = []

# ============================================================
# RESET
# ============================================================

out.append("#file: ./outline/reset")
out.append("")

out.append("/kill @e[tag=ep_joint]")
out.append("/kill @e[tag=ep_cursor]")
out.append("")

for i, data in enumerate(JOINTS):
    x, y, z = data["joint"] # Extract the main joint position for summoning
    out.append(
        f'/summon armor_stand {x} {y} {z} {{Invisible:1b,Marker:1b,NoGravity:1b,Tags:["ep_joint","ep_joint_{i}"]}}'
    )
    out.append(
        f'/scoreboard players set @e[tag=ep_joint_{i},limit=1] ep_index {i}'
    )

out.append("")

out.append(
    '/summon armor_stand 0 0 0 {Invisible:1b,Marker:1b,NoGravity:1b,Tags:["ep_cursor"]}'
)
out.append(
    '/scoreboard players set @e[tag=ep_cursor,limit=1] ep_progress 0'
)

out.append("")
out.append("")

# ============================================================
# TICK
# ============================================================

out.append("#file: ./outline/tick")
out.append("")

# Move cursor to crosshair
out.append(f'/execute as @e[tag=ep_cursor] at @p run tp @s ^ ^ ^{CURSOR_DISTANCE}')
out.append(f'/execute as @e[tag=ep_cursor] at @s run tp @s @e[tag=ep_joint,limit=1,sort=nearest]')

out.append("")

# Snap logic
for i in range(len(JOINTS)):
    if i > 0:
        out.append(
            f'/execute as @e[tag=ep_cursor,scores={{ep_progress={i}}}] at @s '
            f'if entity @e[tag=ep_joint_{i-1},distance=..1] '
            f'run scoreboard players set @s ep_progress {i-1}'
        )

    if i < len(JOINTS) - 1:
        out.append(
            f'/execute as @e[tag=ep_cursor,scores={{ep_progress={i}}}] at @s '
            f'if entity @e[tag=ep_joint_{i+1},distance=..1] '
            f'run scoreboard players set @s ep_progress {i+1}'
        )

out.append("")

# Draw solved line (Iterates through all nested path particles)
for i, data in enumerate(JOINTS):
    for (px, py, pz) in data["path"]:
        out.append(
            f'/execute if score @e[tag=ep_cursor,limit=1] ep_progress matches {i}.. '
            f'run particle {PARTICLE} {px} {py} {pz} 0.3 0.3 0.3 0 1 force'
        )

with open("outline.mcscript", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("outline.mcscript generated")