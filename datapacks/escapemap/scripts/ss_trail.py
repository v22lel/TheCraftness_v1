# generate_trail_path.py

import math
from pathlib import Path

import matplotlib.pyplot as plt


# Config
from trails.lighthouse import *

# Global config (dont modify every run)
NAMESPACE = "escapemap"
PARTICLE_PATH = "super_secrets/particles"
OUTPUT_DIR = Path("scripts/output")
OUTPUT_DIR.mkdir(exist_ok=True)

def catmull_rom(p0, p1, p2, p3, t):
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

    # Subdivision modes, checked in priority order:
    # 1. USE_AUTO_DENSITY
    # 2. USE_ADVANCED
    # 3. normal SAMPLES_PER_SEGMENT
    #
    # Expected globals:
    # USE_ADVANCED = True / False
    # USE_AUTO_DENSITY = True / False
    # SAMPLES_PER_SEGMENT_ADVANCED = [...]
    # SAMPLES_PER_BLOCK = 3.0
    # MIN_SAMPLES_PER_SEGMENT = 2
    # MAX_SAMPLES_PER_SEGMENT = 32
    #
    # Optional smoothing globals:
    # USE_SMOOTH_APPROXIMATION = True / False
    # SMOOTHING_AMOUNT = 0.55
    #
    # SMOOTHING_AMOUNT:
    # 0.0 = exact Catmull-Rom, goes through every control point
    # 1.0 = smoother approximation, only start/end guaranteed exact

    use_auto_density = globals().get("USE_AUTO_DENSITY", False)
    use_advanced = globals().get("USE_ADVANCED", False)
    use_smooth_approximation = globals().get("USE_SMOOTH_APPROXIMATION", True)

    smoothing_amount = globals().get("SMOOTHING_AMOUNT", 0.55)
    smoothing_amount = max(0.0, min(1.0, float(smoothing_amount)))

    if use_auto_density:
        samples_per_block = globals().get("SAMPLES_PER_BLOCK", 3.0)
        min_samples = globals().get("MIN_SAMPLES_PER_SEGMENT", 2)
        max_samples = globals().get("MAX_SAMPLES_PER_SEGMENT", 32)

        if samples_per_block <= 0:
            raise ValueError("SAMPLES_PER_BLOCK must be greater than 0.")

        samples_by_segment = []

        for i in range(segment_count):
            x1, y1, z1 = points[i]
            x2, y2, z2 = points[i + 1]

            distance = math.sqrt(
                (x2 - x1) ** 2
                + (y2 - y1) ** 2
                + (z2 - z1) ** 2
            )

            samples = round(distance * samples_per_block)
            samples = max(min_samples, min(max_samples, samples))
            samples_by_segment.append(samples)

    elif use_advanced:
        if len(SAMPLES_PER_SEGMENT_ADVANCED) != segment_count:
            raise ValueError(
                f"SAMPLES_PER_SEGMENT_ADVANCED must contain exactly {segment_count} values, "
                f"one for each segment between control points."
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

    def lerp(a, b, t):
        return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

    def smooth_approx_point(p0, p1, p2, p3, t):
        # Cubic uniform B-spline approximation.
        # This does not force the curve through p1/p2, which smooths the path.
        t2 = t * t
        t3 = t2 * t

        b0 = (-t3 + 3.0 * t2 - 3.0 * t + 1.0) / 6.0
        b1 = (3.0 * t3 - 6.0 * t2 + 4.0) / 6.0
        b2 = (-3.0 * t3 + 3.0 * t2 + 3.0 * t + 1.0) / 6.0
        b3 = t3 / 6.0

        return tuple(
            p0[i] * b0
            + p1[i] * b1
            + p2[i] * b2
            + p3[i] * b3
            for i in range(3)
        )

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

            exact_point = catmull_rom(p0, p1, p2, p3, t)

            if use_smooth_approximation:
                smooth_point = smooth_approx_point(p0, p1, p2, p3, t)
                point = lerp(exact_point, smooth_point, smoothing_amount)
            else:
                point = exact_point

            generated.append(point)

    generated[0] = points[0]
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
        f"    /function {NAMESPACE}:{TRAIL_PATH}/trail/check",
        "}",
        "",
        "#file: ./trail/check"
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
        f"/function {NAMESPACE}:{TRAIL_PATH}/trail/summon",
        f"{TRAIL_ID}_trail @a = 1",
        "",
        "#file: ./trail/end",
        f"/function {NAMESPACE}:{TRAIL_PATH}/trail/kill",
        f"{TRAIL_ID}_trail @a = 0",
        f"/execute at @e[type=minecraft:marker,tag=ss_trail_{TRAIL_ID}_end,limit=1] run particle minecraft:sonic_boom ~ ~ ~ 0 0 0 0 1 force",
        f"/execute at @e[type=minecraft:marker,tag=ss_trail_{TRAIL_ID}_end,limit=1] run particle minecraft:end_rod ~ ~ ~ 0.6 0.9 0.6 0.04 120 force",
        f"/execute at @e[type=minecraft:marker,tag=ss_trail_{TRAIL_ID}_end,limit=1] run playsound minecraft:block.beacon.activate master @a[distance=..64] ~ ~ ~ 0.9 1.6",
        "",
        "#file: ./trail/kill",
        f"/kill @e[tag=ss_trail_{TRAIL_ID}]",
        f"/kill @e[tag=ss_trail_{TRAIL_ID}_end]"
        "",
        "#file: ./trail/summon",
        f"/kill @e[tag=ss_trail_{TRAIL_ID}]",
        f"/kill @e[tag=ss_trail_{TRAIL_ID}_end]",
        ""
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