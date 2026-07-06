from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin, sqrt, floor, ceil
from pathlib import Path


# ============================================================
# Output config
# ============================================================

NAMESPACE = "escapemap"
FUNCTION_ROOT = "laser"

OUT_FILE = Path("scripts/output/generated_lasers.mcscript")


def function_path(local_path: str) -> str:
    local_path = local_path.strip("/")
    root = FUNCTION_ROOT.strip("/")

    if root:
        return f"{root}/{local_path}"

    return local_path


def call_function(local_path: str) -> str:
    return f"/function {NAMESPACE}:{function_path(local_path)}"


def schedule_function(local_path: str, delay_ticks: int) -> str:
    return f"/schedule function {NAMESPACE}:{function_path(local_path)} {delay_ticks}t"


def cancel_function(local_path: str) -> str:
    return f"/schedule clear {NAMESPACE}:{function_path(local_path)}"


def emit_function(local_path: str, commands: list[str]) -> str:
    local_path = local_path.strip("/")
    body = "\n".join(commands)
    return f"#file: ./{local_path}\n{body}\n"


PARTS = [
    "laser_body",
    "laser_piston",
    "laser_flap1",
    "laser_flap2",
    "laser_laser",
    "laser_spout",
]

MOVING_UP_PARTS = [
    "laser_piston",
    "laser_laser",
    "laser_spout",
]

AIMING_PARTS = [
    "laser_laser",
    "laser_spout",
]


# ============================================================
# Animation config
# ============================================================

TICKS_PER_SECOND = 20

# Blockbench units -> Minecraft blocks.
# 16 Blockbench units = 1 block.
BB_UNIT = 1.0 / 16.0

BOX_SIZE_BLOCKS = 3.0
BOX_HALF = BOX_SIZE_BLOCKS / 2.0

# Assumption:
# laser model spans:
# x = -1.5 .. +1.5
# y =  0.0 .. +3.0
# z = -1.5 .. +1.5
#
# If your model origin differs, edit these pivots.
PIVOT_FLAP1 = (0.0, BOX_HALF - BB_UNIT, -BOX_HALF + BB_UNIT)  # north top edge
PIVOT_FLAP2 = (0.0, BOX_HALF - BB_UNIT, BOX_HALF - BB_UNIT)   # south top edge

AIM_PIVOT_Y_OFFSET_BLOCKS = BB_UNIT * 14.0
PIVOT_AIM_BASE = (0.0, AIM_PIVOT_Y_OFFSET_BLOCKS, 0.0)

FLAP_ROTATION_DEGREES = 247.5
FLAP1_AXIS = "x"
FLAP2_AXIS = "x"

# These signs are the most likely to make the flaps open away from each other.
# Swap signs if they fold inward.
FLAP1_SIGN = -1.0
FLAP2_SIGN = 1.0

FLAP_SUBSTEPS = 200
PITCH_SUBSTEPS = 120

FLAP_DURATION_SECONDS = 30.0

UP_MOVE_BB_UNITS = 41.0
UP_DURATION_SECONDS = 30.0

PITCH_ROTATION_DEGREES = 90.0
PITCH_DELAY_SECONDS = 2.5
PITCH_DURATION_SECONDS = 20.0

Z_PULL_BB_UNITS = 10.0
Z_PULL_DELAY_SECONDS = 2.5
Z_PULL_DURATION_SECONDS = 10.0

SPOUT_EXTRA_Z_BB_UNITS = -6.0
SPOUT_EXTRA_Z_DELAY_SECONDS = 2.5
SPOUT_EXTRA_Z_DURATION_SECONDS = 10.0

# After preset animation, you said the laser/spout should be considered:
# yaw 180, pitch 0.
BASE_AIM_YAW_DEGREES = 180.0
BASE_AIM_PITCH_DEGREES = 0.0

# Rotation sign conventions for final aiming.
# Change these if yaw/pitch appears mirrored.
YAW_SIGN = 1.0
PITCH_SIGN = 1.0
CUSTOM_ROTATION_FIX = -1.0


# ============================================================
# Laser instances
# ============================================================

@dataclass(frozen=False)
class LaserInstance:
    laser_id: str
    x: float
    y: float
    z: float

    target_yaw_degrees: float
    target_pitch_degrees: float

    aim_yaw_delay_seconds: float
    aim_yaw_duration_seconds: float
    aim_yaw_substeps: int

    aim_pitch_delay_seconds: float
    aim_pitch_duration_seconds: float
    aim_pitch_substeps: int

    def fix(self):
        self.x += 0.5
        self.y += 2.5
        self.z += 0.5


# from block under center of thingy
CASTLE_LASER = LaserInstance(
        laser_id="castle",
        x=-163,
        y=-13,
        z=-50,
        target_yaw_degrees=-92.7 * CUSTOM_ROTATION_FIX,
        target_pitch_degrees=-8.8 * CUSTOM_ROTATION_FIX,

        aim_yaw_delay_seconds=2.5,
        aim_yaw_duration_seconds=17.5,
        aim_yaw_substeps=120,

        aim_pitch_delay_seconds=2.5,
        aim_pitch_duration_seconds=2.5,
        aim_pitch_substeps=30,
)

DESERT_LASER = LaserInstance(
    laser_id="desert",
    x=-169,
    y=-35,
    z=31,
    target_yaw_degrees=-112.8 * CUSTOM_ROTATION_FIX,
    target_pitch_degrees=-13.3 * CUSTOM_ROTATION_FIX,

    aim_yaw_delay_seconds=2.5,
    aim_yaw_duration_seconds=15,
    aim_yaw_substeps=100,

    aim_pitch_delay_seconds=2.5,
    aim_pitch_duration_seconds=5,
    aim_pitch_substeps=50,
)

LIGHTHOUSE_LASER = LaserInstance(
    laser_id="lighthouse",
    x=-88,
    y=-37,
    z=-50,
    target_yaw_degrees=-94.3 * CUSTOM_ROTATION_FIX,
    target_pitch_degrees=-23.0 * CUSTOM_ROTATION_FIX,

    aim_yaw_delay_seconds=2.5,
    aim_yaw_duration_seconds=12.5,
    aim_yaw_substeps=125,

    aim_pitch_delay_seconds=2.5,
    aim_pitch_duration_seconds=7.5,
    aim_pitch_substeps=75,
)

LASER = LIGHTHOUSE_LASER
LASER.fix()


# ============================================================
# Math helpers
# ============================================================

Vec3 = tuple[float, float, float]
Quat = tuple[float, float, float, float]  # x, y, z, w


def seconds(value: float) -> int:
    return round(value * TICKS_PER_SECOND)


def v_add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def q_norm(q: Quat) -> Quat:
    x, y, z, w = q
    length = sqrt(x * x + y * y + z * z + w * w)
    if length == 0:
        return (0.0, 0.0, 0.0, 1.0)
    return (x / length, y / length, z / length, w / length)


def q_axis(axis: str, degrees: float) -> Quat:
    half = radians(degrees) / 2.0
    s = sin(half)
    c = cos(half)

    if axis == "x":
        return q_norm((s, 0.0, 0.0, c))
    if axis == "y":
        return q_norm((0.0, s, 0.0, c))
    if axis == "z":
        return q_norm((0.0, 0.0, s, c))

    raise ValueError(f"Unsupported axis: {axis}")


def q_mul(a: Quat, b: Quat) -> Quat:
    ax, ay, az, aw = a
    bx, by, bz, bw = b

    return q_norm((
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    ))


def q_rotate_vec(q: Quat, v: Vec3) -> Vec3:
    x, y, z, w = q
    vx, vy, vz = v

    # Optimized quaternion-vector rotation.
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)

    rx = vx + w * tx + (y * tz - z * ty)
    ry = vy + w * ty + (z * tx - x * tz)
    rz = vz + w * tz + (x * ty - y * tx)

    return (rx, ry, rz)


def yaw_pitch_quat(yaw_degrees: float, pitch_degrees: float) -> Quat:
    q_yaw = q_axis("y", yaw_degrees * YAW_SIGN)
    q_pitch = q_axis("x", pitch_degrees * PITCH_SIGN)

    # For Minecraft-style yaw then pitch, this order is usually the useful one.
    # If yaw becomes local-axis weirdness, swap to q_mul(q_yaw, q_pitch).
    return q_mul(q_pitch, q_yaw)


def pivot_translation(pivot: Vec3, rotation: Quat, extra_translation: Vec3 = (0.0, 0.0, 0.0)) -> Vec3:
    # Rotation around pivot:
    # final_position = R * point + (pivot - R * pivot) + extra_translation
    rotated_pivot = q_rotate_vec(rotation, pivot)
    return v_add(v_sub(pivot, rotated_pivot), extra_translation)


def fmt_float(value: float) -> str:
    if abs(value) < 0.0000005:
        value = 0.0
    return f"{value:.6f}f"


def fmt_vec3(v: Vec3) -> str:
    return f"[{fmt_float(v[0])},{fmt_float(v[1])},{fmt_float(v[2])}]"


def fmt_quat(q: Quat) -> str:
    q = q_norm(q)
    return f"[{fmt_float(q[0])},{fmt_float(q[1])},{fmt_float(q[2])},{fmt_float(q[3])}]"


def transform_nbt(
        translation: Vec3 = (0.0, 0.0, 0.0),
        rotation: Quat = (0.0, 0.0, 0.0, 1.0),
        scale: Vec3 = (1.0, 1.0, 1.0),
) -> str:
    return (
        "{"
        f"translation:{fmt_vec3(translation)},"
        f"scale:{fmt_vec3(scale)},"
        f"left_rotation:{fmt_quat(rotation)},"
        "right_rotation:[0.000000f,0.000000f,0.000000f,1.000000f]"
        "}"
    )


def merge_transform_command(selector: str, duration_ticks: int, translation: Vec3, rotation: Quat) -> str:
    return (
        f"/data merge entity {selector} "
        "{"
        "start_interpolation:-1,"
        f"interpolation_duration:{duration_ticks},"
        f"transformation:{transform_nbt(translation=translation, rotation=rotation)}"
        "}"
    )


def part_selector(laser_id: str, part: str) -> str:
    return f'@e[type=minecraft:item_display,tag={laser_id},tag={part},limit=1]'


def part_model(part: str) -> str:
    return f'{NAMESPACE}:{part}'


def wrap_degrees(degrees: float) -> float:
    return (degrees + 180.0) % 360.0 - 180.0


def q_conjugate(q: Quat) -> Quat:
    x, y, z, w = q
    return (-x, -y, -z, w)


def q_inverse(q: Quat) -> Quat:
    # Unit quaternions only, which is true here because q_norm is used.
    return q_conjugate(q_norm(q))


def shortest_quat_to_target(current: Quat, target: Quat) -> Quat:
    # q and -q represent the same rotation, but interpolation may take the long way.
    # Force the target to be on the same quaternion hemisphere as current.
    dot = (
            current[0] * target[0]
            + current[1] * target[1]
            + current[2] * target[2]
            + current[3] * target[3]
    )

    if dot < 0.0:
        target = (-target[0], -target[1], -target[2], -target[3])

    return q_norm(target)


def pivot_translation_with_local_offset(
        pivot: Vec3,
        rotation: Quat,
        base_translation: Vec3 = (0.0, 0.0, 0.0),
        local_offset: Vec3 = (0.0, 0.0, 0.0),
) -> Vec3:
    # Entity transform:
    # final_point = R * point + translation
    #
    # To rotate around a pivot and also keep a local part offset:
    # translation = pivot - R*pivot + base_translation + R*local_offset
    rotated_pivot = q_rotate_vec(rotation, pivot)
    rotated_offset = q_rotate_vec(rotation, local_offset)

    return v_add(
        v_add(v_sub(pivot, rotated_pivot), base_translation),
        rotated_offset,
    )


def relative_offset_after_rotation(
        pivot: Vec3,
        base_translation_at_start: Vec3,
        preset_rotation: Quat,
        new_rotation: Quat,
) -> Vec3:
    # Convert the current translated state into a point relative to the pivot,
    # undo the preset pivot translation, rotate the resulting offset by the
    # delta rotation, then restore it as a translation.
    preset_pivot_translation = pivot_translation(
        pivot=pivot,
        rotation=preset_rotation,
        extra_translation=UP_TRANSLATION,
    )

    local_from_preset = v_sub(base_translation_at_start, preset_pivot_translation)

    delta_rotation = q_mul(new_rotation, q_inverse(preset_rotation))
    rotated_local = q_rotate_vec(delta_rotation, local_from_preset)

    new_pivot_translation = pivot_translation(
        pivot=pivot,
        rotation=new_rotation,
        extra_translation=UP_TRANSLATION,
    )

    return v_add(new_pivot_translation, rotated_local)


def aim_yaw_delta(instance: LaserInstance) -> float:
    return wrap_degrees(instance.target_yaw_degrees - BASE_AIM_YAW_DEGREES)


def aim_pitch_delta(instance: LaserInstance) -> float:
    return instance.target_pitch_degrees - BASE_AIM_PITCH_DEGREES


def yaw_aim_rotation(instance: LaserInstance, t: float) -> Quat:
    yaw = aim_yaw_delta(instance) * t * YAW_SIGN
    return q_mul(q_axis("y", yaw), PRESET_AIM_ROTATION)


def yaw_final_rotation(instance: LaserInstance) -> Quat:
    return yaw_aim_rotation(instance, 1.0)


def pitch_aim_rotation(instance: LaserInstance, t: float) -> Quat:
    yaw = aim_yaw_delta(instance) * YAW_SIGN
    pitch = aim_pitch_delta(instance) * t * PITCH_SIGN

    q_yaw = q_axis("y", yaw)
    q_pitch = q_axis("x", pitch)

    # Mechanism-style order:
    # preset pitch first, then local pitch adjustment, then yaw base.
    # This prevents the laser from rolling while aiming.
    return q_mul(q_yaw, q_mul(q_pitch, PRESET_AIM_ROTATION))


def aim_part_base_translation(part: str) -> Vec3:
    if part == "laser_spout":
        return v_add(
            v_add(PRESET_AIM_TRANSLATION, Z_PULL_TRANSLATION),
            SPOUT_EXTRA_Z_TRANSLATION,
        )

    return v_add(PRESET_AIM_TRANSLATION, Z_PULL_TRANSLATION)


def aim_part_translation(part: str, rotation: Quat) -> Vec3:
    return relative_offset_after_rotation(
        pivot=PIVOT_AIM_BASE,
        base_translation_at_start=aim_part_base_translation(part),
        preset_rotation=PRESET_AIM_ROTATION,
        new_rotation=rotation,
    )

# ============================================================
# Preset transform states
# ============================================================

UP_TRANSLATION = (0.0, UP_MOVE_BB_UNITS * BB_UNIT, 0.0)
Z_PULL_TRANSLATION = (0.0, 0.0, Z_PULL_BB_UNITS * BB_UNIT)
SPOUT_EXTRA_Z_TRANSLATION = (0.0, 0.0, SPOUT_EXTRA_Z_BB_UNITS * BB_UNIT)

PRESET_AIM_ROTATION = q_axis("x", PITCH_ROTATION_DEGREES * PITCH_SIGN)

PRESET_AIM_TRANSLATION = pivot_translation(
    pivot=PIVOT_AIM_BASE,
    rotation=PRESET_AIM_ROTATION,
    extra_translation=UP_TRANSLATION,
)

PRESET_AIM_TRANSLATION_AFTER_Z_PULL = pivot_translation_with_local_offset(
    pivot=PIVOT_AIM_BASE,
    rotation=PRESET_AIM_ROTATION,
    base_translation=UP_TRANSLATION,
    local_offset=Z_PULL_TRANSLATION,
)

PRESET_SPOUT_TRANSLATION_AFTER_EXTRA_Z = pivot_translation_with_local_offset(
    pivot=PIVOT_AIM_BASE,
    rotation=PRESET_AIM_ROTATION,
    base_translation=UP_TRANSLATION,
    local_offset=v_add(Z_PULL_TRANSLATION, SPOUT_EXTRA_Z_TRANSLATION),
)


def final_aim_state(instance: LaserInstance, part: str) -> tuple[Vec3, Quat]:
    yaw_delta = wrap_degrees(instance.target_yaw_degrees - BASE_AIM_YAW_DEGREES)
    pitch_delta = instance.target_pitch_degrees - BASE_AIM_PITCH_DEGREES

    current_rotation = PRESET_AIM_ROTATION
    aim_delta = yaw_pitch_quat(yaw_delta, pitch_delta)

    rotation = q_mul(aim_delta, current_rotation)
    rotation = shortest_quat_to_target(current_rotation, rotation)

    if part == "laser_spout":
        base_translation = v_add(
            v_add(PRESET_AIM_TRANSLATION, Z_PULL_TRANSLATION),
            SPOUT_EXTRA_Z_TRANSLATION,
        )
    else:
        base_translation = v_add(PRESET_AIM_TRANSLATION, Z_PULL_TRANSLATION)

    translation = relative_offset_after_rotation(
        pivot=PIVOT_AIM_BASE,
        base_translation_at_start=base_translation,
        preset_rotation=PRESET_AIM_ROTATION,
        new_rotation=rotation,
    )

    return translation, rotation


# ============================================================
# Function generation
# ============================================================

def summon_part(instance: LaserInstance, part: str) -> str:
    return (
        f"/summon minecraft:item_display {instance.x:.6f} {instance.y:.6f} {instance.z:.6f} "
        "{"
        f'Tags:["laser","{instance.laser_id}","{part}"],'
        "item:{"
        'id:"minecraft:paper",'
        "count:1,"
        f'components:{{"minecraft:item_model":"{part_model(part)}"}}'
        "},"
        'item_display:"fixed",'
        "brightness:{block:15,sky:15},"
        f"transformation:{transform_nbt()}"
        "}"
    )


def generate_spawn(instance: LaserInstance) -> str:
    commands = [
        f"/kill @e[tag={instance.laser_id}]",
        "",
    ]

    for part in PARTS:
        commands.append(summon_part(instance, part))

    return emit_function(f"{instance.laser_id}/spawn", commands)


def generate_reset(instance: LaserInstance) -> str:
    commands = [
        f"/function escapemap:laser/turn_off {{tag:\"{instance.laser_id}_beam\"}}",
        cancel_function(f"{instance.laser_id}/finish")
    ]

    for part in PARTS:
        commands.append(
            merge_transform_command(
                selector=part_selector(instance.laser_id, part),
                duration_ticks=0,
                translation=(0.0, 0.0, 0.0),
                rotation=(0.0, 0.0, 0.0, 1.0),
            )
        )

    return emit_function(f"{instance.laser_id}/reset", commands)


def generate_start(instance: LaserInstance) -> str:
    t_flap_done = seconds(FLAP_DURATION_SECONDS)
    t_up_start = t_flap_done

    t_up_done = t_up_start + seconds(UP_DURATION_SECONDS)
    t_pitch_start = t_up_done + seconds(PITCH_DELAY_SECONDS)

    t_pitch_done = t_pitch_start + seconds(PITCH_DURATION_SECONDS)
    t_z_pull_start = t_pitch_done + seconds(Z_PULL_DELAY_SECONDS)

    t_z_pull_done = t_z_pull_start + seconds(Z_PULL_DURATION_SECONDS)
    t_spout_start = t_z_pull_done + seconds(SPOUT_EXTRA_Z_DELAY_SECONDS)

    t_spout_done = t_spout_start + seconds(SPOUT_EXTRA_Z_DURATION_SECONDS)

    t_yaw_start = t_spout_done + seconds(instance.aim_yaw_delay_seconds)
    t_yaw_done = t_yaw_start + seconds(instance.aim_yaw_duration_seconds)

    t_final_pitch_start = t_yaw_done + seconds(instance.aim_pitch_delay_seconds)
    t_final_pitch_done = t_final_pitch_start + seconds(instance.aim_pitch_duration_seconds)

    commands = [
        call_function(f"{instance.laser_id}/reset"),
        call_function(f"{instance.laser_id}/step_01_flaps"),
        schedule_function(f"{instance.laser_id}/step_02_up", t_up_start),
        schedule_function(f"{instance.laser_id}/step_03_pitch", t_pitch_start),
        schedule_function(f"{instance.laser_id}/step_04_z_pull", t_z_pull_start),
        schedule_function(f"{instance.laser_id}/step_05_spout_extend", t_spout_start),
        schedule_function(f"{instance.laser_id}/step_06_yaw", t_yaw_start),
        schedule_function(f"{instance.laser_id}/step_07_pitch", t_final_pitch_start),
        schedule_function(f"{instance.laser_id}/finish", t_final_pitch_done),
    ]

    return emit_function(f"{instance.laser_id}/turn_on", commands)


def generate_step_01_flaps(instance: LaserInstance) -> str:
    commands = [
        call_function(f"{instance.laser_id}/step_01_flaps/frame_001")
    ]

    substep_duration = max(1, round(seconds(FLAP_DURATION_SECONDS) / FLAP_SUBSTEPS))

    for i in range(2, FLAP_SUBSTEPS + 1):
        delay = (i - 1) * substep_duration
        commands.append(
            schedule_function(
                f"{instance.laser_id}/step_01_flaps/frame_{i:03d}",
                delay,
            )
        )

    return emit_function(f"{instance.laser_id}/step_01_flaps", commands)


def generate_step_01_flaps_frame(instance: LaserInstance, frame: int) -> str:
    substep_duration = max(1, round(seconds(FLAP_DURATION_SECONDS) / FLAP_SUBSTEPS))

    t = frame / FLAP_SUBSTEPS

    flap1_angle = FLAP_ROTATION_DEGREES * FLAP1_SIGN * t
    flap2_angle = FLAP_ROTATION_DEGREES * FLAP2_SIGN * t

    flap1_rot = q_axis(FLAP1_AXIS, flap1_angle)
    flap2_rot = q_axis(FLAP2_AXIS, flap2_angle)

    flap1_translation = pivot_translation(PIVOT_FLAP1, flap1_rot)
    flap2_translation = pivot_translation(PIVOT_FLAP2, flap2_rot)

    commands = [
        merge_transform_command(
            selector=part_selector(instance.laser_id, "laser_flap1"),
            duration_ticks=substep_duration,
            translation=flap1_translation,
            rotation=flap1_rot,
        ),
        merge_transform_command(
            selector=part_selector(instance.laser_id, "laser_flap2"),
            duration_ticks=substep_duration,
            translation=flap2_translation,
            rotation=flap2_rot,
        ),
    ]

    return emit_function(
        f"{instance.laser_id}/step_01_flaps/frame_{frame:03d}",
        commands,
    )


def generate_step_02_up(instance: LaserInstance) -> str:
    duration = seconds(UP_DURATION_SECONDS)

    commands = []
    for part in MOVING_UP_PARTS:
        commands.append(
            merge_transform_command(
                selector=part_selector(instance.laser_id, part),
                duration_ticks=duration,
                translation=UP_TRANSLATION,
                rotation=(0.0, 0.0, 0.0, 1.0),
            )
        )

    return emit_function(f"{instance.laser_id}/step_02_up", commands)


def generate_step_03_pitch(instance: LaserInstance) -> str:
    commands = [
        call_function(f"{instance.laser_id}/step_03_pitch/frame_001")
    ]

    substep_duration = max(1, round(seconds(PITCH_DURATION_SECONDS) / PITCH_SUBSTEPS))

    for i in range(2, PITCH_SUBSTEPS + 1):
        delay = (i - 1) * substep_duration
        commands.append(
            schedule_function(
                f"{instance.laser_id}/step_03_pitch/frame_{i:03d}",
                delay,
            )
        )

    return emit_function(f"{instance.laser_id}/step_03_pitch", commands)


def generate_step_03_pitch_frame(instance: LaserInstance, frame: int) -> str:
    substep_duration = max(1, round(seconds(PITCH_DURATION_SECONDS) / PITCH_SUBSTEPS))

    t = frame / PITCH_SUBSTEPS

    pitch_rot = q_axis("x", PITCH_ROTATION_DEGREES * PITCH_SIGN * t)

    pitch_translation = pivot_translation(
        pivot=PIVOT_AIM_BASE,
        rotation=pitch_rot,
        extra_translation=UP_TRANSLATION,
    )

    commands = []
    for part in AIMING_PARTS:
        commands.append(
            merge_transform_command(
                selector=part_selector(instance.laser_id, part),
                duration_ticks=substep_duration,
                translation=pitch_translation,
                rotation=pitch_rot,
            )
        )

    return emit_function(
        f"{instance.laser_id}/step_03_pitch/frame_{frame:03d}",
        commands,
    )


def generate_step_04_z_pull(instance: LaserInstance) -> str:
    duration = seconds(Z_PULL_DURATION_SECONDS)

    translation = v_add(PRESET_AIM_TRANSLATION, Z_PULL_TRANSLATION)

    commands = []
    for part in AIMING_PARTS:
        commands.append(
            merge_transform_command(
                selector=part_selector(instance.laser_id, part),
                duration_ticks=duration,
                translation=translation,
                rotation=PRESET_AIM_ROTATION,
            )
        )

    return emit_function(f"{instance.laser_id}/step_04_z_pull", commands)


def generate_step_05_spout_extend(instance: LaserInstance) -> str:
    duration = seconds(SPOUT_EXTRA_Z_DURATION_SECONDS)

    translation = v_add(
        v_add(PRESET_AIM_TRANSLATION, Z_PULL_TRANSLATION),
        SPOUT_EXTRA_Z_TRANSLATION,
    )

    commands = [
        merge_transform_command(
            selector=part_selector(instance.laser_id, "laser_spout"),
            duration_ticks=duration,
            translation=translation,
            rotation=PRESET_AIM_ROTATION,
        )
    ]

    return emit_function(f"{instance.laser_id}/step_05_spout_extend", commands)


def generate_step_06_yaw(instance: LaserInstance) -> str:
    commands = [
        call_function(f"{instance.laser_id}/step_06_yaw/frame_001")
    ]

    substeps = max(1, instance.aim_yaw_substeps)
    substep_duration = max(1, round(seconds(instance.aim_yaw_duration_seconds) / substeps))

    for i in range(2, substeps + 1):
        delay = (i - 1) * substep_duration
        commands.append(
            schedule_function(
                f"{instance.laser_id}/step_06_yaw/frame_{i:03d}",
                delay,
            )
        )

    return emit_function(f"{instance.laser_id}/step_06_yaw", commands)


def generate_step_06_yaw_frame(instance: LaserInstance, frame: int) -> str:
    substeps = max(1, instance.aim_yaw_substeps)
    substep_duration = max(1, round(seconds(instance.aim_yaw_duration_seconds) / substeps))

    t = frame / substeps
    rotation = yaw_aim_rotation(instance, t)
    rotation = shortest_quat_to_target(PRESET_AIM_ROTATION, rotation)

    commands = []
    for part in AIMING_PARTS:
        commands.append(
            merge_transform_command(
                selector=part_selector(instance.laser_id, part),
                duration_ticks=substep_duration,
                translation=aim_part_translation(part, rotation),
                rotation=rotation,
            )
        )

    return emit_function(
        f"{instance.laser_id}/step_06_yaw/frame_{frame:03d}",
        commands,
    )


def generate_step_07_pitch(instance: LaserInstance) -> str:
    commands = [
        call_function(f"{instance.laser_id}/step_07_pitch/frame_001")
    ]

    substeps = max(1, instance.aim_pitch_substeps)
    substep_duration = max(1, round(seconds(instance.aim_pitch_duration_seconds) / substeps))

    for i in range(2, substeps + 1):
        delay = (i - 1) * substep_duration
        commands.append(
            schedule_function(
                f"{instance.laser_id}/step_07_pitch/frame_{i:03d}",
                delay,
            )
        )

    return emit_function(f"{instance.laser_id}/step_07_pitch", commands)


def generate_step_07_pitch_frame(instance: LaserInstance, frame: int) -> str:
    substeps = max(1, instance.aim_pitch_substeps)
    substep_duration = max(1, round(seconds(instance.aim_pitch_duration_seconds) / substeps))

    t = frame / substeps

    start_rotation = yaw_final_rotation(instance)
    rotation = pitch_aim_rotation(instance, t)
    rotation = shortest_quat_to_target(start_rotation, rotation)

    commands = []
    for part in AIMING_PARTS:
        commands.append(
            merge_transform_command(
                selector=part_selector(instance.laser_id, part),
                duration_ticks=substep_duration,
                translation=aim_part_translation(part, rotation),
                rotation=rotation,
            )
        )

    return emit_function(
        f"{instance.laser_id}/step_07_pitch/frame_{frame:03d}",
        commands,
    )


def generate_finish(instance: LaserInstance) -> str:
    commands = [
        f"/function escapemap:laser/complete {{p:\"{floor(instance.x)},{ceil(instance.y + 1)},{floor(instance.z)}\",tag:\"{instance.laser_id}_beam\"}}",
    ]

    return emit_function(f"{instance.laser_id}/finish", commands)

def generate_kill(instance: LaserInstance) -> str:
    commands = [
        f"/kill @e[tag={instance.laser_id}]",
        f"/function escapemap:laser/turn_off {{tag:\"{instance.laser_id}_beam\"}}",
        cancel_function(f"{instance.laser_id}/finish")
    ]

    return emit_function(f"{instance.laser_id}/kill", commands)


def generate_instance(instance: LaserInstance) -> str:
    chunks = [
        generate_spawn(instance),
        generate_reset(instance),
        generate_kill(instance),
        generate_start(instance),
        generate_step_01_flaps(instance),
    ]

    for frame in range(1, FLAP_SUBSTEPS + 1):
        chunks.append(generate_step_01_flaps_frame(instance, frame))

    chunks += [
        generate_step_02_up(instance),
        generate_step_03_pitch(instance),
    ]

    for frame in range(1, PITCH_SUBSTEPS + 1):
        chunks.append(generate_step_03_pitch_frame(instance, frame))

    chunks += [
        generate_step_04_z_pull(instance),
        generate_step_05_spout_extend(instance),
        generate_step_06_yaw(instance),
    ]

    for frame in range(1, max(1, instance.aim_yaw_substeps) + 1):
        chunks.append(generate_step_06_yaw_frame(instance, frame))

    chunks.append(generate_step_07_pitch(instance))

    for frame in range(1, max(1, instance.aim_pitch_substeps) + 1):
        chunks.append(generate_step_07_pitch_frame(instance, frame))

    chunks.append(generate_finish(instance))

    return "\n".join(chunks)


def generate_all() -> str:
    chunks = [
        "// Auto-generated laser animation file.",
        "// Edit the Python generator, not this file.",
        "",
        generate_instance(LASER)
    ]

    return "\n".join(chunks)


def main() -> None:
    OUT_FILE.write_text(generate_all(), encoding="utf-8")
    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()