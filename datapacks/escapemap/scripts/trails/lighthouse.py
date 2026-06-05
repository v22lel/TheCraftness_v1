TRAIL_ID = "lighthouse"
TRAIL_PATH = "super_secrets/lighthouse"

USE_AUTO_DENSITY = True
USE_ADVANCED = True
USE_SMOOTH_APPROXIMATION = True
SMOOTHING_AMOUNT = 0.75
FINAL_DELAY = 0
TICKS_PER_PARTICLE = 0.25
MIN_SAMPLES_PER_SEGMENT = 2
MAX_SAMPLES_PER_SEGMENT = 24
SAMPLES_PER_SEGMENT = 16
SAMPLES_PER_SEGMENT_ADVANCED = [
    12,
    16,
    10,
    10,
    8,
    8,

    12,
    8,
    10,
    5,
    5,

    10,
    12,
    12,
    10,
    6,
    6,
    4,
    6,
    6,
    4,
    6,

    6,
    2
]

SAMPLES_PER_SEGMENT_ADVANCED = [i * 2 for i in SAMPLES_PER_SEGMENT_ADVANCED]

CONTROL_POINTS = [
    (-38, -39, -19),
    (-45, -25, -7),
    (-50, -4, -3),
    (-51, 3, -14),
    (-54, -2, -26),
    (-55, -11, -22),
    (-56, -14, -13),
    (-62, -25, -2),
    (-71, -32, -7),
    (-84, -40, -8),
    (-92, -42, -6),
    (-100, -39, -5),
    (-106, -27, 2),
    (-101, -15, 17),
    (-90, -9, 29),
    (-81, -14, 36),
    (-79, -22, 40),
    (-84, -27, 41),
    (-89, -25, 43),
    (-91, -20, 45),
    (-88, -16, 49),
    (-83, -15, 52),
    (-76, -19, 60),
    (-72, -27, 64),
    (-72, -29.5, 64)
]

CONTROL_POINTS = [(x + 0.5, y + 0.5, z + 0.5) for (x, y, z) in CONTROL_POINTS]