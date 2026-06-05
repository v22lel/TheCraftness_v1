# generate_trail_path.py

import math
from pathlib import Path

import matplotlib.pyplot as plt


# Config
TRAIL_ID = "treetop"

# Number of generated points between each pair of rough points.
# Higher = smoother trail, more marker entities.
USE_ADVANCED = True
FINAL_DELAY = 2
TICKS_PER_PARTICLE = 0.5
SAMPLES_PER_SEGMENT = 8
SAMPLES_PER_SEGMENT_ADVANCED = [
    8,
    8,
    8,
    8,
    8,
    8,
    8,
    3,
]

# Rough path points: x, y, z
# Put your EP endpoint first and obelisk top last.
CONTROL_POINTS = [
    (20.03, -31.00, 17.65),
    (21.03, -27.71, 19.78),
    (23.06, -25.82, 25.56),
    (20.90, -23.20, 23.87),
    (20.13, -25.45, 21.85),
    (21.69, -28.99, 24.13),
    (23.41, -26.95, 29.13),
    (25.41, -30.68, 30.66),
    (25.41, -33.00, 30.66)
]

# Global config (dont modify every run)
NAMESPACE = "escapemap"
PARTICLE_PATH = "super_secrets/particles"
TRAIL_PATH = "super_secrets/treetop"
OUTPUT_DIR = Path("scripts/output")
OUTPUT_DIR.mkdir(exist_ok=True)

def catmull_rom(p0, p1, p2, p3, t):
    """
    Catmull-Rom spline point.
    p1 and p2 are the segment endpoints.
    t is 0..1.
    """
    t2 = t * t
    t3 = t2 * t

    out = []
    for i in range(3):
        value = 0.5 * (
            (2.0 * p1[i])
            + (-p0[i] + p2[i]) * t
            + (2.0 * p0[i] - 5.0 * p1[i] + 4.0 * p2[i] - p3[i]) * t2
            + (-p0[i] + 3.0 * p1[i] - 3.0 * p2[i] + p3[i]) * t3
        )
        out.append(value)

    return tuple(out)


def generate_path(points):
    if len(points) < 2:
        raise ValueError("Need at least 2 control points.")

    segment_count = len(points) - 1

    if USE_ADVANCED:
        if len(SAMPLES_PER_SEGMENT_ADVANCED) != segment_count:
            raise ValueError(
                f"SAMPLES_PER_SEGMENT_ADVANCED must contain exactly {segment_count} values, "
                f"one for each segment between control points. Found: {len(SAMPLES_PER_SEGMENT_ADVANCED)} values instead."
            )

        samples_by_segment = SAMPLES_PER_SEGMENT_ADVANCED
    else:
        samples_by_segment = [SAMPLES_PER_SEGMENT] * segment_count

    for i, samples in enumerate(samples_by_segment):
        if not isinstance(samples, int) or samples < 1:
            raise ValueError(
                f"Invalid sample count for segment {i}: {samples}. "
                f"Each segment must have at least 1 sample."
            )

    # Duplicate ends so the curve starts and ends correctly.
    padded = [points[0]] + points + [points[-1]]

    generated = []

    for i in range(1, len(padded) - 2):
        p0 = padded[i - 1]
        p1 = padded[i]
        p2 = padded[i + 1]
        p3 = padded[i + 2]

        samples = samples_by_segment[i - 1]

        for s in range(samples):
            t = s / samples
            generated.append(catmull_rom(p0, p1, p2, p3, t))

    generated.append(points[-1])
    return generated

def write_mcscript(path_points):
    lines = [
        "#file: ./trail/load",
        f"var {TRAIL_ID}_trail @a = 0",
        "",
        "#file: ./trail/tick",
        f"if ({TRAIL_ID}_trail @p >= 1) {{",
        f"    {TRAIL_ID}_trail @a += 1",
        "}"
    ]

    for i in range(len(path_points)):
        start_tick = int(i * TICKS_PER_PARTICLE) + 1
        end_tick = int(start_tick + TICKS_PER_PARTICLE) - 1

        if start_tick >= end_tick:
            tick_match = str(start_tick)
        else:
            tick_match = f"{start_tick}..{end_tick}"

        lines.append(
            f"/execute if score @p {TRAIL_ID}_trail matches {tick_match} "
            f"at @e[type=minecraft:marker,tag=ss_trail_{TRAIL_ID}_{i},limit=1] "
            f"run function {NAMESPACE}:{PARTICLE_PATH}/head"
        )

    final_start = int(len(path_points) * TICKS_PER_PARTICLE) + 1
    final_end = final_start + FINAL_DELAY

    lines += [
        "",
        f"/execute if score @p {TRAIL_ID}_trail matches {final_start}..{final_end} at @e[type=minecraft:marker,tag=ss_trail_{TRAIL_ID}_end,limit=1] run function {NAMESPACE}:{PARTICLE_PATH}/end",
        "",
        f"/execute if score @p {TRAIL_ID}_trail matches {final_end}.. at @e[type=minecraft:marker,tag=ss_trail_{TRAIL_ID}_end,limit=1] run function {NAMESPACE}:{TRAIL_PATH}/trail/end",
        "",
        "#file: ./trail/run",
        f"{TRAIL_ID}_trail @a = 1",
        "",
        "#file: ./trail/end",
        f"{TRAIL_ID}_trail @a = 0",
        "/execute at @e[type=minecraft:marker,tag=ss_trail_treetop_end,limit=1] run particle minecraft:sonic_boom ~ ~ ~ 0 0 0 0 1 force",
        "/execute at @e[type=minecraft:marker,tag=ss_trail_treetop_end,limit=1] run particle minecraft:end_rod ~ ~ ~ 0.6 0.9 0.6 0.04 120 force",
        "/execute at @e[type=minecraft:marker,tag=ss_trail_treetop_end,limit=1] run playsound minecraft:block.beacon.activate master @a[distance=..64] ~ ~ ~ 0.9 1.6",
        "",
        "#file: ./trail/reset",
        "",
        f"/kill @e[tag=ss_trail_{TRAIL_ID}]",
        f"/kill @e[tag=ss_trail_{TRAIL_ID}_end]"
    ]

    for i, (x, y, z) in enumerate(path_points):
        lines.append(
            f'/summon minecraft:marker {x:.3f} {y:.3f} {z:.3f} '
            f'{{Tags:["ss_trail_{TRAIL_ID}","ss_trail_{TRAIL_ID}_{i}"]}}'
        )

    x, y, z = path_points[-1]
    lines.append("")
    lines.append(
        f'/summon minecraft:marker {x:.3f} {y:.3f} {z:.3f} '
        f'{{Tags:["ss_trail_{TRAIL_ID}","ss_trail_{TRAIL_ID}_end"]}}'
    )

    output_path = OUTPUT_DIR / f"trail.mcscript"
    output_path.write_text("\n".join(lines), encoding="utf-8")

    return output_path

def write_preview(control_points, path_points):
    xs = [p[0] for p in path_points]
    ys = [p[1] for p in path_points]
    zs = [p[2] for p in path_points]

    cxs = [p[0] for p in control_points]
    cys = [p[1] for p in control_points]
    czs = [p[2] for p in control_points]

    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")

    ax.plot(xs, zs, ys, label="generated path")
    ax.scatter(cxs, czs, cys, marker="o", label="control points")

    ax.set_xlabel("X")
    ax.set_ylabel("Z")
    ax.set_zlabel("Y")
    ax.legend()

    output_path = OUTPUT_DIR / f"{TRAIL_ID}_preview.png"
    plt.savefig(output_path, dpi=180)
    plt.close(fig)

    return output_path


# ----------------------------
# MAIN
# ----------------------------

def main():
    path_points = generate_path(CONTROL_POINTS)

    tick_file = write_mcscript(path_points)
    preview_file = write_preview(CONTROL_POINTS, path_points)

    print(f"Generated {len(path_points)} path points.")
    print(f"File:    {tick_file}")
    print(f"Preview image:    {preview_file}")


if __name__ == "__main__":
    main()