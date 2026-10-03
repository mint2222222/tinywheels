#!/usr/bin/env python3
"""Tiny Wheels - a tiny sakura-and-snow racer that runs in your terminal.

Usage:  tinywheels            start racing
        tinywheels --help     show this help
        tinywheels --test     run a quick self-check

Controls:
  Up / W       speed up
  Down / S     brake
  Left / A     steer left
  Right / D    steer right
  Space        handbrake: throw the car into a drift (DRIFT mode)
  1            pick 3 LAPS mode (on the title screen)
  2            pick INFINITE mode (on the title screen)
  3            pick DRIFT mode (on the title screen)
  4            open the GARAGE to choose your car (on the title screen)
  Enter        play again on a new random track (after you finish)
  M            back to the title screen
  Q / Esc      quit (Esc in the garage just goes back)

3 LAPS: race 3 laps as fast as you can.
INFINITE: the road never ends. You start with 40 seconds; every red torii gate
is a checkpoint that adds time. Score points for distance (double while
drifting = steering hard at speed) and for jumps. Drive until time runs out!

DRIFT: a downhill mountain pass through a pine and sakura forest. Hold
Space and steer to throw the tail out, keep steering + gas to hold the
drift, steer the other way to straighten up. Points build up while you
slide and count when you straighten out cleanly; link drifts for a combo
(up to x5). Hit the guardrail and you lose the drift you were in.

GARAGE: you start with the AE86. Unlock more iconic Japanese cars with easy
challenges: Mazda RX-7 FD, Honda NSX, Toyota Supra MK4, Nissan Skyline
GT-R R34 and Subaru Impreza WRX. The garage shows how to get each one.

Day turns into night and back every 3 minutes. Past 20,000 points in
INFINITE, convenience stores (konbini) start showing up along the road.
Yellow-black stripes are ramps (jump!). Lanterns, rocks and pines
slow you down, and so does the deep snow.
Your records are saved in ~/.local/share/tinywheels/
"""
import json, math, os, random, re, select, signal, sys, termios, time, tty

# ---------------- colors ("r;g;b") ----------------
SKY      = "190;205;238"
SUN      = "225;65;80"
FUJI     = "100;110;155"
SNOW_CAP = "248;250;255"
FAR_SNOW = "228;234;246"
SNOW     = ["242;245;251", "222;230;243"]   # snowy ground, light / dark stripes
RUMBLE   = ["205;35;50", "245;245;245"]     # red / white road edge
ROAD     = ["98;100;115", "90;92;106"]
LANE     = "240;240;240"
RAMP     = ["250;200;40", "45;45;45"]       # yellow / black = jump here!
FINISH   = ["250;250;250", "25;25;25"]
TRUNK    = "72;54;58"                       # dark grey-brown sakura bark
BLOSSOM  = ["232;150;182", "248;188;208", "255;221;233"]  # deep / mid / pale pink
TORII    = "210;40;40"
TORII_TOP = "45;30;30"
STONE    = ["150;150;155", "115;115;122"]  # lantern stone, light / dark
GLOW     = "255;200;90"                     # lantern light
ROCK     = ["120;115;125", "95;92;100"]
PINE     = "35;95;60"
PETALS   = ["255;190;215", "250;150;190"]
FLAKE    = "255;255;255"
SHADOW   = "150;155;175"
SMOKE    = "235;235;240"
PAGODA   = "78;80;112"
WOOD     = "125;85;62"
ROOF     = "62;58;75"
WINDOW   = "255;205;120"                    # warm window light
VEND     = "225;60;70"
VEND_LIT = "205;235;255"
DRINKS   = ["60;120;220", "240;160;40", "60;170;90", "200;50;60"]
PAPER    = "240;85;55"                      # paper lanterns (chochin)
STRING   = "60;45;45"
MOON     = "250;245;215"
STAR     = "255;255;235"
HEADLIGHT = (1.0, 0.93, 0.75)              # warm white light the headlights add (r, g, b)
TAILGLOW  = (1.0, 0.12, 0.08)              # red glow around the taillights
BRAKE_LIGHT = "255;80;80"                      # brake lights (brighter red)
BEAM_LEN = 15000                            # how far the headlights reach
STORE    = "242;242;236"                    # konbini: white walls...
STRIPES  = ["245;135;30", "0;140;85", "225;35;45"]   # ...with orange / green / red stripes
STORE_LIT = "235;245;255"                   # bright shop windows
SHELF    = "175;185;205"
# The car: a white-and-black "panda" AE86 hatchback, seen from behind
CAR = {"w": "245;245;245", "k": "35;40;60", "r": "220;30;40", "o": "255;150;40",
       "b": "15;15;20", "p": "230;230;210", "t": "45;45;45"}
CAR_ART = [                      # one letter per pixel, "." = see-through
    "....wwwwwwww....",
    "...wkkkkkkkkw...",
    "..wkkkkkkkkkkw..",
    ".wwwwwwwwwwwwww.",
    "wLLLLLLLLLLLLLLw",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbppppbbbbbb",
    "tt............tt",
    "tt............tt",
]
# DRIFT mode's camera is closer, so the car there is drawn with more detail:
# from behind, turned a little, and fully sideways (nose to the right; flipped for the left)
DRIFT_REAR = [
    ".......WWWWWWWWWWWW.......",
    "......wwkkkkkkkkkkww......",
    ".....wwkgkkkkkkkkkkww.....",
    "....wwkkkgkkkkkkkkkkww....",
    "...BbbbbbbbbbbbbbbbbbbB...",
    "..wwwwwwwwwwwwwwwwwwwwww..",
    ".wwLLLLLLLLLLLLLLLLLLLLww.",
    ".wwLLLLLLLLLLLLLLLLLLLLww.",
    ".bbbbbbbbbbppppbbbbbbbbbb.",
    ".bbbbbbbbbbppppbbbbbbbbbb.",
    ".BBBBBBBBBBBBBBBBBBBBBBBB.",
    ".tttt................tttt.",
    ".tttt................tttt.",
]
DRIFT_HALF = [   # turned a little: nose to the right
    "......WWWWWWWWWWWWWW........",
    ".....wwkkkkkkkkkkkwsgg......",
    "....wwkgkkkkkkkkkkwsggg.....",
    "...wwkkkgkkkkkkkkkwskkks....",
    "..BbbbbbbbbbbbbbbbBsssssss..",
    ".wwwwwwwwwwwwwwwwwwsssssssy.",
    ".wLLLLLLLLLLLLLLLLwssssssss.",
    ".wLLLLLLLLLLLLLLLLwssssssss.",
    ".bbbbbbbbppppbbbbbbBBBBBBBo.",
    ".bbbbbbbbppppbbbbbbbbbbbbbb.",
    ".BBBBBBBBBBBBBBBBBBbbbtmmtb.",
    ".tttt..........tttt..tmmt...",
    ".tttt..........tttt...tt....",
]
DRIFT_SIDE = [   # fully sideways: nose to the right
    "......WWWWWWWWWWWWWWWWW...........",
    ".....wwkkkkkkkkkwsgggggSggggs.....",
    "....wwkgkkkkkkkkwsggggkSkgggks....",
    "...wwkkkgkkkkkkkwskkkkkSkkkkkksB..",
    "..BbbbbbbbbbbbbbBssssssssssssssWWW",
    ".wwwwwwwwwwwwwwwwssssssssssssssssy",
    ".wLLLLLLLLLLLLLLwsssssssssmmssssss",
    ".wLLLLLLLLLLLLLLwssssssssssssssssS",
    ".bbbbbbbppbbbbbbbBBBBBBBBBBBBBBBBo",
    ".bbbbbbbppbbbbbbbbbbbbbbbbbbbbbbbb",
    ".BBBBBBBBBBBBBBBBbbtmmtbbbbbbtmmtb",
    ".tttt.......tttt..tmmt......tmmt..",
    ".tttt.......tttt...tt........tt...",
]
CAR.update({"W": "255;255;255", "s": "198;200;210", "S": "160;163;176", "g": "88;104;136",
            "B": "52;52;60", "m": "170;173;182", "y": "255;245;200"})   # highlight, shade, glass shine, trim, rims
CAR_SHADOW = "38;40;48"


# ---------------- the garage: iconic Japanese cars ----------------
def shade(color, f):
    return ";".join(str(min(255, int(int(x) * f))) for x in color.split(";"))


def taillights(n, style):
    """A row of n pixels of taillights: "split" blocks, "round" pairs of round lights, or one "bar"."""
    if style == "bar":
        return "o" + "r" * (n - 2) + "o"
    side, mid = {"split": ("rrrooo", "B"), "round": ("rrwrr", "w")}[style]
    side = side[:n // 2 - 1]
    return side + mid * (n - 2 * len(side)) + side[::-1]


def add_wing(art):
    """A big rear wing: a body-colored blade with black end plates, sticking out past the car."""
    art = list(art)
    i = next(r for r, row in enumerate(art) if "Bb" in row)     # the spoiler line under the rear glass
    row, up = art[i], art[i - 1]
    a, b = row.index("B") - 1, row.index("B", row.index("B") + 1) + 1
    art[i - 1] = up[:a] + "B" + "W" * (b - a - 1) + "B" + up[b + 1:]
    art[i] = row[:a] + "B" + row[a + 1:b] + "B" + row[b + 1:]
    return art


# how: the challenge that unlocks it. test(g, progress): did this race complete it?
CARS = [
    dict(name="Toyota AE86 Trueno", paint="245;245;245", lower="15;15;20", lights="split", wing=False,
         how="", test=lambda g, p: True),
    dict(name="Mazda RX-7 FD", paint="250;200;35", lights="round", wing=True,
         how="Finish a 3 LAPS race", test=lambda g, p: g.mode == "laps"),
    dict(name="Honda NSX", paint="205;28;35", lights="bar", wing=False,
         how="Finish 5 races (any mode)", test=lambda g, p: p["races"] >= 5),
    dict(name="Toyota Supra MK4", paint="245;115;30", lights="round", wing=True,
         how="Score 3000 in INFINITE", test=lambda g, p: g.mode == "infinite" and g.result >= 3000),
    dict(name="Nissan Skyline GT-R R34", paint="35;85;200", lights="round", wing=True,
         how="Score 2000 in DRIFT", test=lambda g, p: g.mode == "drift" and g.result >= 2000),
    dict(name="Subaru Impreza WRX", paint="30;55;150", lights="split", wing=True, rims="215;175;55",
         how="Get a x3 combo in DRIFT", test=lambda g, p: g.mode == "drift" and g.max_combo >= 3),
]
for car in CARS:
    def make(art, wing, car=car):
        out = []
        for row in art:
            if "L" in row:
                a, n = row.index("L"), row.count("L")
                row = row[:a] + taillights(n, car["lights"]) + row[a + n:]
            out.append(row)
        return add_wing(out) if wing else out
    car["art"] = make(CAR_ART, False)                  # small car for 3 LAPS / INFINITE
    car["rear"], car["half"], car["side"] = (make(a, car["wing"]) for a in (DRIFT_REAR, DRIFT_HALF, DRIFT_SIDE))
    paint = car["paint"]
    car["pal"] = dict(CAR, w=paint, W=shade(paint, 1.12), s=shade(paint, 0.82), S=shade(paint, 0.66),
                      b=car.get("lower") or shade(paint, 0.45), m=car.get("rims", CAR["m"]))
LOCKED = {ch: "30;30;40" for ch in CAR}              # a locked car is just a dark shape


def draw_car(px, art, pal, x0, y0, cs, h, braking=False):
    for r, line in enumerate(art):
        for c, ch in enumerate(line):
            if ch != ".":
                color = BRAKE_LIGHT if ch == "r" and braking else pal[ch]
                rect(px, x0 + c * cs, x0 + (c + 1) * cs, y0 + r * cs, y0 + (r + 1) * cs, color, h)
SMOKE2   = "208;208;215"

# Things that make their own light. Everything else gets darker (and bluer) at night.
GLOWS = {GLOW, WINDOW, VEND_LIT, PAPER, MOON, STAR, *DRINKS, CAR["r"], CAR["o"], CAR["y"], BRAKE_LIGHT, STORE_LIT, SHELF}

# Two looks for the world: the snowy sakura road, and the green mountain pass of DRIFT mode
SNOWY  = dict(sky=SKY, far=FAR_SNOW, ground=SNOW, edges=[(1.12, RUMBLE)], road=ROAD, lane=LANE)
FOREST = dict(sky="150;198;240", far="72;118;78", ground=["86;150;70", "74;136;62"],
              edges=[(1.16, ["128;118;100", "118;108;92"]), (1.04, ["240;240;235"] * 2)],   # gravel, white line
              road=["72;74;82", "66;68;76"], lane="235;235;225")
MOUNT_FAR, MOUNT_NEAR = "120;160;165", "62;108;72"
PINE_DARK = "25;72;45"
RAIL, RAIL_POST = "215;215;210", "150;150;145"

# ---------------- day and night ----------------
DAY_LENGTH = 180   # seconds for one full day + night
# Light over the day: (time of day 0..1, red, green, blue). 0.0 = midnight, 0.5 = noon.
LIGHT = [(0.0, .22, .26, .45), (0.18, .22, .26, .45), (0.25, .85, .65, .72), (0.32, 1, 1, 1),
         (0.68, 1, 1, 1), (0.76, 1, .7, .52), (0.84, .45, .38, .6), (0.9, .22, .26, .45), (1.0, .22, .26, .45)]
STARS = [(random.random(), random.random() ** 2 * 0.85) for _ in range(70)]


def light_at(tod):
    for (t0, *a), (t1, *b) in zip(LIGHT, LIGHT[1:]):
        if tod <= t1:
            p = (tod - t0) / (t1 - t0)
            return [x + (y - x) * p for x, y in zip(a, b)]
    return LIGHT[-1][1:]


def tree_shape(rng):
    """One sakura: a few branches and a wide, fluffy crown made of blossom clusters."""
    clusters = []
    for _ in range(10):
        a = rng.uniform(-1, 1)
        clusters.append((a * 750, -1500 + a * a * 550 + rng.uniform(-150, 250), rng.uniform(250, 400)))
    clusters.sort(key=lambda c: -c[1])     # lowest first, so the top clusters are drawn on top
    branches = [(rng.uniform(-650, -250), rng.uniform(-1300, -1000)),
                (rng.uniform(250, 650), rng.uniform(-1300, -1000)), (rng.uniform(-150, 150), -1450)]
    return clusters, branches


TREE_SHAPES = [tree_shape(random.Random(k)) for k in range(8)]

# ---------------- world settings (tweak these!) ----------------
SEG       = 200          # length of one road segment
ROAD_W    = 2000         # half the road width
CAM_H     = 1000         # camera height
DEPTH     = 0.84         # field of view
DRAW      = 180          # how many segments ahead we draw
PLAYER_Z  = 1000         # how far in front of the camera the car is
MAX_SPEED = SEG * 60     # top speed (world units per second)
ACCEL     = MAX_SPEED / 5
BRAKE     = MAX_SPEED
DECEL     = MAX_SPEED / 5
OFF_DECEL = MAX_SPEED / 2    # deep snow slows you down...
OFF_LIMIT = MAX_SPEED / 4    # ...to this speed
CENTRIFUGAL = 0.25           # how hard curves push you outwards
GRAVITY   = 4000
JUMP_V    = 2200
LAPS      = 3
FPS       = 30
DATA_DIR = os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"), "tinywheels")
START_TIME = 40          # infinite mode: seconds on the clock at the start
CHECKPOINT = 350         # infinite mode: a torii checkpoint every this many segments
DRIFT_LEN = 3600         # drift mode: length of the mountain course, in segments
KONBINI_SCORE = 20000    # infinite mode: konbini stores start to appear after this score
CHECKPOINT_TIME = 11     # infinite mode: seconds added by the first checkpoint (later ones give less)


# ---------------- random track ----------------
def ease_in(a, b, p):    return a + (b - a) * p * p
def ease_out(a, b, p):   return a + (b - a) * (1 - (1 - p) ** 2)
def ease_inout(a, b, p): return a + (b - a) * (0.5 - math.cos(p * math.pi) / 2)


def add_piece(g, n_in, n_hold, n_out, c, dy, deco=True):
    """Add one stretch of road (curve c, going up/down by dy) with trees, maybe a ramp, and obstacles.
    A track is a list of segments; each has a curve, a height, a kind and some sprites."""
    total = n_in + n_hold + n_out
    ramp = random.randrange(total - 4) if deco and g.mode != "drift" and random.random() < 0.25 else -9
    for k in range(total):
        if k < n_in:            cv = ease_in(0, c, k / n_in)
        elif k < n_in + n_hold: cv = c
        else:                   cv = ease_out(c, 0, (k - n_in - n_hold) / n_out)
        i = len(g.curve)
        g.curve.append(cv)
        g.ys.append(ease_inout(g.y_end, g.y_end + dy, k / total))
        g.kind.append("ramp" if ramp <= k < ramp + 4 else "")
        spr = []
        if g.mode == "drift":                                # mountain pass: guardrails and forest
            if i % 2 == 0:
                spr += [(-1.2, "rail", 0), (1.2, "rail", 0)]
            for side in (-1, 1):
                if random.random() < 0.55:
                    spr.append((side * random.uniform(1.5, 4.5), "pine" if random.random() < 0.65 else "tree",
                                random.random()))
            if random.random() < 1 / 200:
                spr.append((random.choice([-1, 1]) * 1.6, "vending", 0))
            g.sprites.append(spr)
            continue
        if random.random() < 0.35:                          # sakura trees
            spr.append((random.choice([-1, 1]) * random.uniform(1.4, 3.5), "tree", random.random()))
        if i % 40 == 20:                                     # stone lanterns line the road
            spr += [(-1.35, "lantern", 0), (1.35, "lantern", 0)]
        if random.random() < 1 / 90:
            spr.append((random.choice([-1, 1]) * random.uniform(2.8, 4.5), "house", 0))
        if random.random() < 1 / 150:
            spr.append((random.choice([-1, 1]) * 1.6, "vending", 0))
        if g.konbini and random.random() < 1 / 250:
            spr.append((random.choice([-1, 1]) * 2.6, "konbini", 0))
        if i % 300 in (150, 158, 166):                       # festival lanterns over the road
            spr.append((0, "chochin", 0))
        if g.mode == "infinite" and i % CHECKPOINT == 0 and i:
            g.kind[i] = "finish"
            spr.append((0, "torii", 0))
        elif deco and not g.kind[i] and random.random() < 1 / 45:
            spr.append((random.uniform(-0.75, 0.75), "obstacle", random.randrange(3)))
        g.sprites.append(spr)
    g.y_end += dy


def random_piece(g):
    n = random.choice([10, 25, 40])
    c = random.choice([0, 0, 2, 3, 5]) * random.choice([-1, 1])
    dy = 0 if random.random() < 0.4 else random.uniform(-25, 25) * SEG - g.y_end
    add_piece(g, n, random.choice([15, 30, 50]), n, c, dy)


def drift_piece(g):
    """Mountain pass: sharp corners and hairpins, short straights between them, going downhill."""
    n = random.choice([8, 15, 25])
    add_piece(g, n, random.choice([10, 20, 35]), n, random.choice([3, 4, 5, 6, 7]) * random.choice([-1, 1]),
              -random.uniform(0, 12) * SEG)
    add_piece(g, 0, random.choice([5, 15, 30]), 0, 0, -random.uniform(0, 5) * SEG)


def grow(g):
    """Infinite mode: keep building road just ahead of the car."""
    # ponytail: old road is never thrown away (~1 MB per 10 min of driving); trim it if you drive for days
    while len(g.curve) < g.pos / SEG + DRAW + 20:
        random_piece(g)


# ---------------- game state ----------------
class Game:
    def __init__(self, mode=None, tod=0.3):   # mode: None = title menu, "laps", "infinite" or "drift"
        self.mode = mode
        self.tod = tod               # time of day, 0..1 (0.3 = morning)
        self.pos = self.x = self.speed = 0.0
        self.konbini = False         # infinite mode: unlocked at KONBINI_SCORE
        self.braking = False
        self.curve, self.ys, self.kind, self.sprites = [], [], [], []
        self.y_end = 0.0
        add_piece(self, 0, 40, 0, 0, 0, deco=False)            # straight start
        self.kind[4] = self.kind[5] = "finish"
        self.sprites[4].append((0, "torii", 0))
        if mode == "infinite":
            self.length = math.inf
            grow(self)
        elif mode == "drift":
            while len(self.curve) < DRIFT_LEN:
                drift_piece(self)
            self.finish_seg = len(self.curve)
            add_piece(self, 0, DRAW + 20, 0, 0, 0)               # road after the finish line
            self.kind[self.finish_seg] = self.kind[self.finish_seg + 1] = "finish"
            self.sprites[self.finish_seg].append((0, "torii", 0))
            self.length = math.inf
        else:
            while len(self.curve) < 1400:
                random_piece(self)
            add_piece(self, 25, 25, 25, 0, -self.y_end)          # come back down to height 0
            add_piece(self, 0, 10, 0, 0, 0, deco=False)
            self.length = len(self.curve) * SEG
        self.jump_h = self.vz = self.air_t = 0.0
        self.clock = -3.0            # negative = countdown "3, 2, 1"
        self.laps = []               # finished lap times
        self.score = 0.0             # infinite mode
        self.time_left = START_TIME  # infinite mode
        self.checkpoints = 0
        self.done = False
        self.result = None           # final time (laps) or score (infinite)
        self.bonk = 0.0              # >0 right after hitting something
        self.msg, self.msg_t = "", 0.0
        self.sky = 0.0               # background scroll
        self.records = load_records(mode)  # best first
        self.steer = 0               # -1 left, 0 straight, 1 right
        self.drifting = False
        self.slip = 0.0              # drift mode: how sideways the car is, -1..1 (+ = nose to the right)
        self.pending = 0.0           # drift mode: points of the drift you're in right now
        self.combo = 1               # drift mode: multiplier for drifts linked together
        self.calm = 0.0              # drift mode: seconds since the last drift
        self.max_combo = 1           # drift mode: best combo this run
        self.car = CARS[load_progress()["car"]]
        self.garage = None           # title menu: which car the garage shows (None = garage closed)
        self.new_cars = []           # cars unlocked by this race
        snow = mode != "drift"       # no snow on the mountain pass, only petals
        self.parts = [[random.random(), random.random(), random.uniform(-0.03, 0.03),
                       random.uniform(0.05, 0.12) if i % 2 or not snow else random.uniform(0.1, 0.22),
                       random.choice(PETALS) if i % 2 or not snow else FLAKE, random.uniform(0, 6.3)]
                      for i in range(160 if snow else 90)]   # [x, y, drift, fall speed, color, wobble], x/y in 0..1


SCORED = ("infinite", "drift")   # modes where a higher number is better


def records_file(mode):
    return os.path.join(DATA_DIR, {"infinite": "infinite.txt", "drift": "drift.txt"}.get(mode, "records.txt"))


def load_records(mode):
    """Laps: times, lowest first. Infinite and drift: scores, highest first."""
    if mode is None:
        return []
    try:
        with open(records_file(mode)) as f:
            return sorted((float(t) for t in f.read().split()), reverse=mode in SCORED)
    except (OSError, ValueError):
        return []


def load_progress():
    """Which cars you have, which one you drive, and how many races you finished."""
    try:
        with open(os.path.join(DATA_DIR, "progress.json")) as f:
            p = json.load(f)
    except (OSError, ValueError):
        p = {}
    p.setdefault("car", 0)
    p.setdefault("unlocked", [0])
    p.setdefault("races", 0)
    if p["car"] not in p["unlocked"] or not 0 <= p["car"] < len(CARS):
        p["car"] = 0
    return p


def save_progress(p):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "progress.json"), "w") as f:
        json.dump(p, f)


def finish(g, value):
    g.done, g.result = True, value
    g.records = sorted(g.records + [value], reverse=g.mode in SCORED)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(records_file(g.mode), "w") as f:
        f.write("\n".join(f"{t:.3f}" for t in g.records) + "\n")
    p = load_progress()                                 # did this race unlock a new car?
    p["races"] += 1
    for i, car in enumerate(CARS):
        if i not in p["unlocked"] and car["test"](g, p):
            p["unlocked"].append(i)
            g.new_cars.append(car["name"])
    save_progress(p)


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def show(g, v):
    """A record as text: a time for laps, a score for infinite and drift."""
    return str(int(v)) if g.mode in SCORED else fmt(v)


def say(g, text):
    g.msg, g.msg_t = text, 1.0


def update(g, dt, keys, t):
    if g.mode == "infinite":
        grow(g)
    N = len(g.curve)
    pct = g.speed / MAX_SPEED
    seg = int((g.pos + PLAYER_Z) // SEG) % N
    steer = ("right" in keys) - ("left" in keys) if not g.done else 0

    for p in g.parts:            # falling petals and snow
        p[0] = (p[0] + (p[2] + 0.03 * math.sin(t * 1.5 + p[5]) + (p[0] - 0.5) * pct * 0.8 - steer * pct * 0.15) * dt) % 1
        p[1] += (p[3] + pct * 0.25) * dt
        if p[1] > 1:
            p[0], p[1] = random.random(), 0
    g.steer = steer
    g.sky += g.curve[seg] * pct * dt * 0.02
    g.bonk = max(0.0, g.bonk - dt)
    g.msg_t = max(0.0, g.msg_t - dt)
    g.tod = (g.tod + dt / DAY_LENGTH) % 1

    if g.mode is None:
        return                   # title menu: just let it snow
    if not g.done:
        g.clock += dt
    if g.clock < 0:
        return                   # still counting down

    air = g.jump_h > 0
    if g.mode == "drift":
        hand = "drift" in keys and not g.done
        if hand and steer and pct > 0.3:
            g.slip += steer * dt * 2.5                       # handbrake + steer: kick the tail out
        elif steer * g.slip > 0 and "up" in keys:
            g.slip += (steer * 0.4 - g.slip * 0.6) * dt      # gas + steer into it: hold the drift
        else:
            g.slip -= g.slip * dt * (3.0 if steer * g.slip < 0 else 1.2)   # counter-steer or let go: grip back
        g.slip = max(-1.0, min(1.0, g.slip))
        g.x += (steer * 2.5 * (1 - 0.6 * abs(g.slip)) + g.slip * 2.2) * dt * pct   # the nose pulls you in
        g.x -= dt * 2 * pct * pct * g.curve[seg] * CENTRIFUGAL * 1.6               # corners push you out
        g.speed -= (abs(g.slip) * 0.15 + (0.3 if hand else 0)) * MAX_SPEED * dt   # sliding costs speed
    else:
        g.x += steer * dt * 2.5 * pct * (0.4 if air else 1)
        g.x -= dt * 2 * pct * pct * g.curve[seg] * CENTRIFUGAL
    if "up" in keys and not g.done:     g.speed += ACCEL * dt
    elif "down" in keys and not g.done: g.speed -= BRAKE * dt
    else:                               g.speed -= DECEL * dt
    if abs(g.x) > 1 and not air and g.speed > OFF_LIMIT:
        g.speed -= OFF_DECEL * dt
    g.x = max(-3.0, min(3.0, g.x))
    g.speed = max(0.0, min(MAX_SPEED, g.speed))
    g.braking = "down" in keys and not g.done
    if g.mode == "drift":
        g.drifting = abs(g.slip) > 0.2 and g.speed > MAX_SPEED * 0.3 and abs(g.x) <= 1
    else:
        g.drifting = bool(steer) and g.speed > MAX_SPEED * 0.6 and abs(g.x) <= 1 and not air

    if air or g.vz > 0:          # flying through the air
        g.air_t += dt
        g.jump_h += g.vz * dt
        g.vz -= GRAVITY * dt
        if g.jump_h <= 0:
            g.jump_h = g.vz = 0.0
            if g.mode == "infinite" and not g.done:
                bonus = int(g.air_t * 100)
                g.score += bonus
                say(g, f"JUMP +{bonus}")
            g.air_t = 0.0

    if g.mode == "infinite" and not g.done:
        g.score += g.speed * dt / SEG * (2 if g.drifting else 1)   # 1 point per segment, x2 drifting
        g.time_left -= dt
        if g.score >= KONBINI_SCORE and not g.konbini:      # unlock konbini, and put one just ahead
            g.konbini = True
            g.sprites[int(g.pos // SEG) + DRAW - 5].append((2.6, "konbini", 0))
            say(g, "KONBINI AHEAD!")
        if g.time_left <= 0:
            g.time_left = 0.0
            finish(g, int(g.score))

    if g.mode == "drift" and not g.done:
        if g.drifting:
            g.pending += abs(g.slip) * (g.speed / MAX_SPEED) * 400 * dt
            g.calm = 0.0
        else:
            g.calm += dt
            if g.pending and g.calm > 0.4:                   # drift finished cleanly: bank the points
                pts = int(g.pending * g.combo)
                g.score += pts
                say(g, f"+{pts}" + (f"  x{g.combo}" if g.combo > 1 else ""))
                if g.pending > 150:
                    g.combo = min(5, g.combo + 1)
                    g.max_combo = max(g.max_combo, g.combo)
                g.pending = 0.0
            if g.calm > 4:
                g.combo = 1
        if abs(g.x) > 1.12:                                  # hit the guardrail
            g.x = math.copysign(1.1, g.x)
            if g.bonk == 0:
                say(g, "CRASH! drift lost" if g.pending else "CRASH!")
                g.speed, g.slip, g.bonk, g.pending, g.combo = g.speed * 0.5, 0.0, 0.8, 0.0, 1
        if g.pos + PLAYER_Z >= g.finish_seg * SEG:           # finish line
            g.score += int(g.pending * g.combo)
            g.pending = 0.0
            finish(g, int(g.score))

    # move, and check every segment we drove over (fast cars can skip one per frame)
    start = int((g.pos + PLAYER_Z) // SEG)
    g.pos += g.speed * dt
    for a in range(start, int((g.pos + PLAYER_Z) // SEG) + 1):
        s = a % N
        if g.kind[s] == "ramp" and g.jump_h == 0 and g.vz <= 0 and g.speed > MAX_SPEED * 0.2:
            g.vz = JUMP_V * g.speed / MAX_SPEED
        for sx, what, _ in g.sprites[s]:
            if what == "torii" and a > start and g.mode == "infinite" and not g.done:
                bonus = max(5.0, CHECKPOINT_TIME - g.checkpoints * 0.2)
                g.time_left += bonus
                g.checkpoints += 1
                say(g, f"CHECKPOINT +{bonus:.0f}s")
            elif g.jump_h or g.bonk:
                continue
            elif what in ("obstacle", "lantern", "vending") and abs(g.x - sx) < 0.33:
                g.speed, g.bonk = min(g.speed, MAX_SPEED * 0.3), 0.8
                say(g, "BONK!")
            elif what == "tree" and abs(g.x - sx) < 0.25:
                g.speed, g.bonk = min(g.speed, MAX_SPEED * 0.1), 0.8
                say(g, "BONK!")

    if g.pos >= g.length:        # crossed the finish line
        g.pos -= g.length
        if not g.done:
            g.laps.append(g.clock - sum(g.laps))
            if len(g.laps) == LAPS:
                finish(g, g.clock)


# ---------------- drawing ----------------
def span(row, a, b, color):
    """Paint pixels a..b of one row (clipped to the screen)."""
    a, b = max(0, int(a)), min(len(row), int(b))
    if b > a:
        row[a:b] = [color] * (b - a)


def rect(px, x0, x1, y0, y1, color, clip):
    for r in range(max(0, int(y0)), min(clip, int(y1))):
        span(px[r], x0, x1, color)


def circle(px, cx, cy, r, color, clip, stretch=1.0, cap=None):
    for row in range(max(0, int(cy - r)), min(clip, int(cy + r))):
        d = (row - cy) / r
        half = stretch * r * math.sqrt(max(0.0, 1 - d * d))
        span(px[row], cx - half, cx + half, cap if cap and d < -0.55 else color)


def line(px, x0, y0, x1, y1, half, color, clip):
    """A thick line, drawn row by row (good for steep lines like branches)."""
    for r in range(max(0, int(min(y0, y1))), min(clip, int(max(y0, y1)) + 1)):
        x = x0 + (x1 - x0) * (r - y0) / (y1 - y0) if y1 != y0 else x0
        span(px[r], x - half, x + half + 1, color)


def background(w, h, horizon, sky, tod, dark, th):
    px = [[th["sky"]] * w for _ in range(horizon)] + [[th["far"]] * w for _ in range(h - horizon)]
    mh = horizon * 0.55                                   # Mt. Fuji height
    fx = ((0.35 - sky) % 1.5 - 0.25) * w
    if dark > 0.4:                                        # stars (a few twinkle off each frame)
        for x, y in STARS:
            if random.random() < 0.97:
                px[int(y * horizon)][int(((x - sky * 0.3) % 1) * w)] = STAR
    p = (tod - 0.2) / 0.65                                # sun: rises at 0.2, sets at 0.85
    if 0 < p < 1:
        circle(px, ((0.1 + 0.8 * p - sky * 0.5) % 1.5 - 0.25) * w,
               horizon * (1 - 0.85 * math.sin(p * math.pi)), horizon * 0.15, SUN, horizon)
    q = ((tod - 0.8) % 1) / 0.45                          # moon: rises at 0.8, sets at 0.25
    if q < 1:
        mx, my, mr = ((0.1 + 0.8 * q - sky * 0.5) % 1.5 - 0.25) * w, horizon * (1 - 0.8 * math.sin(q * math.pi)), horizon * 0.09
        circle(px, mx, my, mr, MOON, horizon)
        circle(px, mx + mr * 0.5, my - mr * 0.2, mr * 0.85, th["sky"], horizon)    # take a bite: crescent moon
    if th is FOREST:                                      # layers of green mountains, near ones scroll faster
        for color, low, amp, speed in ((MOUNT_FAR, 0.25, 0.4, 0.5), (MOUNT_NEAR, 0.08, 0.3, 1.0)):
            for c in range(w):
                u = (c / w + sky * speed) * 6.28
                top = horizon * (1 - low - amp * (0.5 + 0.3 * math.sin(u * 1.3 + speed) + 0.15 * math.sin(u * 4.1)))
                for r in range(max(0, int(top)), horizon):
                    px[r][c] = color
        return px
    bx, th, wd = ((0.8 - sky) % 1.5 - 0.25) * w, horizon * 0.06, horizon * 0.12   # far-away pagoda
    rect(px, bx - 0.5, bx + 0.5, horizon - 6.5 * th, horizon - 5 * th, PAGODA, horizon)
    for k in range(5):
        y, f = horizon - (k + 1) * th, 1 - k * 0.13
        rect(px, bx - wd * f, bx + wd * f, y, y + th * 0.35, PAGODA, horizon)
        rect(px, bx - wd * f * 0.55, bx + wd * f * 0.55, y + th * 0.35, y + th, PAGODA, horizon)
    for row in range(max(0, int(horizon - mh)), horizon):
        d = (row - (horizon - mh)) / mh
        half = mh * 2 * (0.1 + d)
        span(px[row], fx - half, fx + half, SNOW_CAP if d < 0.3 else FUJI)
    return px


def draw_pine(px, cx, gy, s, clip, size, snow):
    """A pine tree: trunk and 3 tiers of branches (darker underneath), maybe with snow on top."""
    rect(px, cx - 60 * size * s, cx + 60 * size * s, gy - 250 * size * s, gy, TRUNK, clip)
    for k in range(3):
        top, tall, wide = gy - (1300 - k * 300) * size * s, 500 * size * s, (220 + k * 70) * size * s
        for row in range(max(0, int(top)), min(clip, int(top + tall))):
            d = (row - top) / tall
            span(px[row], cx - wide * d, cx + wide * d, SNOW_CAP if snow and d < 0.3 else PINE if d < 0.65 else PINE_DARK)


def draw_sprite(px, what, v, cx, gy, s, clip):
    """cx, gy = screen spot where the sprite touches the ground, s = pixels per world unit."""
    if what == "tree":                             # sakura: trunk, branches, fluffy blossom clusters
        clusters, branches = TREE_SHAPES[int(v * len(TREE_SHAPES))]
        rect(px, cx - 75 * s, cx + 75 * s, gy - 700 * s, gy, TRUNK, clip)
        for bx, by in branches:
            line(px, cx, gy - 650 * s, cx + bx * s, gy + by * s, 40 * s, TRUNK, clip)
        for k, (dx, dy, r) in enumerate(clusters):
            low = k < len(clusters) // 2           # lower clusters are in shadow: deeper pink
            circle(px, cx + dx * s, gy + dy * s, r * s, BLOSSOM[0] if low else BLOSSOM[1], clip, 1.15,
                   BLOSSOM[1] if low else BLOSSOM[2])
    elif what == "house":                          # little wooden house with warm windows
        rect(px, cx - 600 * s, cx + 600 * s, gy - 700 * s, gy, WOOD, clip)
        for wx in (-380, 180):
            rect(px, cx + wx * s, cx + (wx + 200) * s, gy - 520 * s, gy - 280 * s, WINDOW, clip)
        rect(px, cx - 70 * s, cx + 70 * s, gy - 480 * s, gy, ROOF, clip)
        top, tall = gy - 1150 * s, 450 * s
        for row in range(max(0, int(top)), min(clip, int(top + tall))):
            d = (row - top) / tall
            span(px[row], cx - (350 + 450 * d) * s, cx + (350 + 450 * d) * s, SNOW_CAP if d < 0.45 else ROOF)
    elif what == "konbini":                        # Japanese convenience store
        rect(px, cx - 900 * s, cx + 900 * s, gy - 880 * s, gy, STORE, clip)
        rect(px, cx - 920 * s, cx + 920 * s, gy - 930 * s, gy - 880 * s, SNOW_CAP, clip)
        for k, col in enumerate(STRIPES):
            rect(px, cx - 900 * s, cx + 900 * s, gy - (860 - k * 55) * s, gy - (805 - k * 55) * s, col, clip)
        for x1, x2 in ((-830, -140), (140, 830)):                 # big bright windows with shelves
            rect(px, cx + x1 * s, cx + x2 * s, gy - 620 * s, gy - 120 * s, STORE_LIT, clip)
            for y in (470, 320):
                rect(px, cx + x1 * s, cx + x2 * s, gy - y * s, gy - (y - 25) * s, SHELF, clip)
                for k in range(5):
                    x = x1 + 60 + k * (x2 - x1 - 120) / 5
                    rect(px, cx + x * s, cx + (x + 50) * s, gy - (y + 90) * s, gy - y * s, DRINKS[k % 4], clip)
        rect(px, cx - 90 * s, cx + 90 * s, gy - 620 * s, gy, SHELF, clip)          # glass door
        rect(px, cx - 70 * s, cx + 70 * s, gy - 600 * s, gy, STORE_LIT, clip)
    elif what == "vending":                        # Japanese drink vending machine
        rect(px, cx - 170 * s, cx + 170 * s, gy - 700 * s, gy, VEND, clip)
        rect(px, cx - 130 * s, cx + 130 * s, gy - 640 * s, gy - 330 * s, VEND_LIT, clip)
        for k, col in enumerate(DRINKS):
            rect(px, cx + (-110 + k * 60) * s, cx + (-70 + k * 60) * s, gy - 560 * s, gy - 460 * s, col, clip)
        rect(px, cx - 100 * s, cx + 100 * s, gy - 200 * s, gy - 120 * s, STRING, clip)
        rect(px, cx - 180 * s, cx + 180 * s, gy - 740 * s, gy - 700 * s, SNOW_CAP, clip)
    elif what == "chochin":                        # a string of paper lanterns across the road
        u = ROAD_W * s
        for side in (-1, 1):
            rect(px, cx + side * 1.35 * u - 40 * s, cx + side * 1.35 * u + 40 * s, gy - 1900 * s, gy, STRING, clip)
        steps = max(2, int(2.7 * u))
        for k in range(steps + 1):
            t = k / steps
            x, y = cx + (2 * t - 1) * 1.35 * u, gy - (1900 - 350 * (1 - (2 * t - 1) ** 2)) * s
            if k % (steps // 8 or 1) == 0 and 0 < k < steps:
                rect(px, x - 70 * s, x + 70 * s, y, y + 200 * s, PAPER, clip)
            rect(px, x, x + 1, y, y + 1, STRING, clip)
    elif what == "lantern" or (what == "obstacle" and v == 0):    # stone lantern (toro)
        for x1, y1, y2, color in [(250, 0, 120, STONE[1]), (90, 120, 500, STONE[0]),
                                  (220, 500, 580, STONE[1]), (170, 580, 800, STONE[0]),
                                  (80, 620, 760, GLOW), (320, 800, 900, STONE[1]),
                                  (300, 900, 940, SNOW_CAP), (60, 940, 1000, STONE[1])]:
            rect(px, cx - x1 * s, cx + x1 * s, gy - y2 * s, gy - y1 * s, color, clip)
    elif what == "obstacle" and v == 1:            # snowy rocks
        ground = min(clip, int(gy))
        circle(px, cx - 60 * s, gy - 150 * s, 330 * s, ROCK[0], ground, 1.2, SNOW_CAP)
        circle(px, cx + 260 * s, gy - 60 * s, 180 * s, ROCK[1], ground, 1.2, SNOW_CAP)
    elif what == "obstacle":                       # little snowy pine tree
        draw_pine(px, cx, gy, s, clip, 1, True)
    elif what == "pine":                           # tall forest pine (drift mode)
        draw_pine(px, cx, gy, s, clip, 1.6 + 1.2 * v, False)
    elif what == "rail":                           # guardrail: a post and a piece of rail
        rect(px, cx - 25 * s, cx + 25 * s, gy - 330 * s, gy, RAIL_POST, clip)
        rect(px, cx - 230 * s, cx + 230 * s, gy - 330 * s, gy - 230 * s, RAIL, clip)
    elif what == "torii":
        u = ROAD_W * s
        for side in (-1, 1):
            rect(px, cx + side * 1.3 * u - 110 * s, cx + side * 1.3 * u + 110 * s, gy - 2300 * s, gy, TORII, clip)
        rect(px, cx - 1.5 * u, cx + 1.5 * u, gy - 1950 * s, gy - 1800 * s, TORII, clip)
        rect(px, cx - 1.6 * u, cx + 1.6 * u, gy - 2350 * s, gy - 2200 * s, TORII, clip)
        rect(px, cx - 1.75 * u, cx + 1.75 * u, gy - 2500 * s, gy - 2350 * s, TORII_TOP, clip)


def render(g, w, h):
    """Draw one frame and return it as a single string. h is in pixels (2 per text row)."""
    N = len(g.curve)
    horizon = int(h * 0.45)
    P = h * 0.65                                    # projection scale
    base, frac = int(g.pos // SEG), (g.pos % SEG) / SEG
    y0, y1 = g.ys[base % N], g.ys[(base + 1) % N]
    th = FOREST if g.mode == "drift" else SNOWY
    cam_h = CAM_H * (0.8 if g.mode == "drift" else 1)      # drift-cam: a bit lower
    cam_y = y0 + (y1 - y0) * frac + cam_h + g.jump_h
    cam_x = g.x * ROAD_W
    light = light_at(g.tod)
    dark = max(0.0, min(1.0, (0.85 - sum(light) / 3) / 0.5))     # 0 = day, 1 = night
    px = background(w, h, horizon, g.sky, g.tod, dark, th)
    tinted, lit = {}, {}                            # color caches for this frame

    def lighten(c, amount, color):
        """Pixel color c, lit by the time of day plus `amount` (0..1) of a lamp's light."""
        key = (c, int(amount * 12), color)
        if key not in lit:
            q = key[1] / 12
            rgb = c.split(";")
            v = c if c in GLOWS else ";".join(str(min(255, int(int(x) * (l + k * q))))
                                              for x, l, k in zip(rgb, light, color))
            lit[key] = tinted[v] = v               # already lit: don't darken it again later
        return lit[key]

    maxy = h                                        # rows below this are already drawn
    x, dx = 0.0, -g.curve[base % N] * frac
    seen = []
    for n in range(DRAW):                           # road, from near to far
        i = (base + n) % N
        zn = n * SEG - frac * SEG
        zf = zn + SEG
        sn, sf = DEPTH * P / max(zn, 1), DEPTH * P / zf
        yn = horizon + sn * (cam_y - g.ys[i])
        yf = horizon + sf * (cam_y - g.ys[(i + 1) % N])
        cn, cf = w / 2 + sn * (x - cam_x), w / 2 + sf * (x + dx - cam_x)
        hn, hf = sn * ROAD_W, sf * ROAD_W
        if zn > 600:
            seen.append((i, sn, cn, yn, maxy))
        x, dx = x + dx, dx + g.curve[i]
        if yf >= maxy or yn <= yf:
            continue                                # hidden behind a hill
        stripe = (i // 3) % 2
        k = g.kind[i]
        road = RAMP[i % 2] if k == "ramp" else FINISH[i % 2] if k == "finish" else th["road"][stripe]
        top = max(0, math.ceil(yf))
        for r in range(top, min(maxy, math.ceil(yn))):
            t = (yn - r) / (yn - yf)
            c, hw = cn + (cf - cn) * t, hn + (hf - hn) * t
            row = [th["ground"][stripe]] * w
            for f, colors in th["edges"]:
                span(row, c - hw * f, c + hw * f, colors[stripe])
            span(row, c - hw, c + hw, road)
            if stripe and not k:
                span(row, c - hw * 0.03, c + hw * 0.03, th["lane"])
            px[r] = row
        maxy = top

    for i, s, c, gy, clip in reversed(seen):        # trees, obstacles, gates: far to near
        for sx, what, v in g.sprites[i]:
            draw_sprite(px, what, v, c + s * sx * ROAD_W, gy, s, clip)

    if dark > 0.05:     # headlights: two warm beams straight ahead, fading with distance
        for r in range(horizon + 1, h):
            z = DEPTH * P * (cam_h + g.jump_h) / (r - horizon)    # how far away this row is
            if not PLAYER_Z * 0.9 < z < BEAM_LEN:
                continue
            fade, sc, half = 1.3 * (1 - z / BEAM_LEN) * dark, DEPTH * P / z, 400 + z * 0.16
            row = px[r]
            for c in range(max(0, int(w / 2 - (350 + half) * sc)), min(w, int(w / 2 + (350 + half) * sc) + 1)):
                x = (c - w / 2) / sc                                # sideways distance, world units
                i = min(1.0, fade * min(1.0, max(0.0, 1 - ((x + 350) / half) ** 2) + max(0.0, 1 - ((x - 350) / half) ** 2)))
                if i > 0.04:
                    row[c] = lighten(row[c], i, HEADLIGHT)

    for p in g.parts:
        r, col = int(p[1] * h), int(p[0] * w)
        if 0 <= r < h:
            span(px[r], col, col + (2 if p[4] != FLAKE else 1), p[4])

    if g.garage is not None:                        # garage: show off a car, slowly turning around
        car = CARS[g.garage]
        art = [car["rear"], car["half"], car["side"], car["half"]][int(time.monotonic() / 0.9) % 4]
        if int(time.monotonic() / 3.6) % 2:
            art = [row[::-1] for row in art]
        cs = max(1, round(w / 45))
        x0, y0 = w // 2 - len(art[0]) * cs // 2, int(h * 0.92) - len(art) * cs
        circle(px, w / 2, y0 + len(art) * cs, 1.6 * cs, CAR_SHADOW, h, len(art[0]) * 0.55 / 1.6)
        unlocked = g.garage in load_progress()["unlocked"]
        draw_car(px, art, car["pal"] if unlocked else LOCKED, x0, y0, cs, h)
        return finish_frame(px, w, h, tinted, light)
    art, cs = g.car["art"], max(1, round(w / 90))  # the car: from behind, or turning when drifting
    if g.mode == "drift":
        art = g.car["rear"] if abs(g.slip) < 0.15 else g.car["half"] if abs(g.slip) < 0.45 else g.car["side"]
        if g.slip < 0:
            art = [row[::-1] for row in art]        # nose to the left: mirror it
        cs = max(1, round(w / 85))
    aw = len(art[0]) * cs
    lift = int(g.jump_h / 40)
    bounce = random.randint(0, 1) if abs(g.x) > 1 and g.speed > 0 and not lift else 0
    x0 = w // 2 - aw // 2 - int(g.slip * 4 * cs)  # the tail swings out to the side
    y0 = h - len(art) * cs - 2 - lift - bounce
    if lift:
        rect(px, x0, x0 + aw, h - 3, h - 1, SHADOW, h)
    elif g.mode == "drift":
        circle(px, x0 + aw / 2, h - 2.5 * cs, 1.6 * cs, CAR_SHADOW, h, aw * 0.55 / (1.6 * cs))   # shadow
        if g.drifting:                              # round clouds of tire smoke from the back wheels
            back = (x0, x0 + aw * 0.65) if g.slip > 0 else (x0 + aw * 0.35, x0 + aw)
            for _ in range(14):
                circle(px, random.uniform(*back), h - 2 - random.uniform(0, 6) * cs,
                       random.uniform(1.5, 3.5) * cs, random.choice((SMOKE, SMOKE2)), h)
    elif g.drifting:                                # drift smoke from the tires
        for _ in range(8):
            sx = x0 + random.choice([0, aw]) + random.uniform(-3, 3) * cs
            sy = h - 3 - random.uniform(0, 3) * cs
            rect(px, sx - cs, sx + cs, sy - cs, sy, SMOKE, h)
    draw_car(px, art, g.car["pal"], x0, y0, cs, h, g.braking)
    glow = max(dark, 0.5 if g.braking else 0) * (1.5 if g.braking else 1)
    if glow > 0.05:     # red glow around the taillights (bigger when braking)
        rad = (3.5 if g.braking else 2.5) * cs
        rows = [r for r, line in enumerate(art) if "r" in line]
        lights = art[rows[0]]
        ty = y0 + (rows[0] + len(rows) / 2) * cs
        spots = [c + (len(lights[c:]) - len(lights[c:].lstrip("r"))) / 2       # middle of each red light
                 for c in range(len(lights)) if lights[c] == "r" and (c == 0 or lights[c - 1] != "r")]
        for tx in (x0 + c * cs for c in spots):
            for r in range(max(0, int(ty - rad)), min(h, int(ty + rad) + 1)):
                for c in range(max(0, int(tx - rad)), min(w, int(tx + rad) + 1)):
                    d = math.hypot(c - tx, r - ty) / rad
                    if d < 1:
                        px[r][c] = lighten(px[r][c], min(1.0, (1 - d) ** 2 * glow * 0.8), TAILGLOW)
    return finish_frame(px, w, h, tinted, light)


def finish_frame(px, w, h, tinted, light):
    """Turn the pixels into one string of colored "▀" characters."""
    def tint(c):                                    # every color: darkened for the time of day
        if c not in tinted:
            r, gr, b = c.split(";")
            tinted[c] = c if c in GLOWS else f"{int(int(r) * light[0])};{int(int(gr) * light[1])};{int(int(b) * light[2])}"
        return tinted[c]

    out = []                                        # 2 pixel rows -> 1 text row of "▀"
    for r in range(h // 2):
        row, last = [f"\x1b[{r + 1};1H"], None
        for top, bot in zip(px[2 * r], px[2 * r + 1]):
            if (top, bot) != last:
                row.append(f"\x1b[38;2;{tint(top)}m\x1b[48;2;{tint(bot)}m")
                last = (top, bot)
            row.append("▀")
        out.append("".join(row))
    return "".join(out)


def hud(g, cols, rows):
    style = "\x1b[0;1;38;2;255;255;255;48;2;160;35;70m"

    def center(row, text):
        return f"\x1b[{row};{max(1, (cols - len(text)) // 2)}H{style} {text} "

    kmh = int(g.speed / MAX_SPEED * 180)
    best = show(g, g.records[0]) if g.records else "--"
    mid = rows // 3
    if g.garage is not None:
        bar = f" GARAGE   car {g.garage + 1} of {len(CARS)}"
    elif g.mode is None:
        bar = f" TINY WHEELS   car: {g.car['name']}"
    elif g.mode == "drift":
        now = g.clock if g.done else max(0.0, g.clock)
        done = min(100, int(100 * (g.pos + PLAYER_Z) / (g.finish_seg * SEG)))
        bar = (f" DRIFT SCORE {int(g.score)}   COMBO x{g.combo}   TIME {fmt(now)}   BEST {best}"
               f"   {kmh:3d} km/h   COURSE {done}%")
    elif g.mode == "infinite":
        bar = (f" SCORE {int(g.score)}   TIME LEFT {g.time_left:4.1f}   CHECKPOINTS {g.checkpoints}"
               f"   BEST {best}   {kmh:3d} km/h" + ("   DRIFT x2" if g.drifting else ""))
    else:
        lap = min(len(g.laps) + 1, LAPS)
        now = g.clock if g.done else max(0.0, g.clock)
        bar = f" LAP {lap}/{LAPS}   TIME {fmt(now)}   BEST {best}   {kmh:3d} km/h"
    s = f"\x1b[1;1H{style}{bar[:cols].ljust(cols)}"

    if g.garage is not None:
        car, p = CARS[g.garage], load_progress()
        s += center(3, car["name"].upper() if g.garage in p["unlocked"] else "? ? ?")
        status = ("DRIVING THIS ONE" if g.garage == p["car"] else "Enter = drive this car"
                  if g.garage in p["unlocked"] else "LOCKED - " + car["how"])
        s += center(5, status)
        s += center(rows - 1, "<- -> = look around    Enter = choose    m = back")
    elif g.mode is None:
        s += center(mid, "T I N Y   W H E E L S")
        s += center(mid + 2, "1 = 3 LAPS      fastest time wins     ")
        s += center(mid + 3, "2 = INFINITE    drive on, score points")
        s += center(mid + 4, "3 = DRIFT       mountain pass, drift! ")
        s += center(mid + 5, "4 = GARAGE      choose your car       ")
        s += center(mid + 7, "q = quit")
    elif g.clock < 0:
        s += center(mid, str(math.ceil(-g.clock)))
        if g.records:                              # the records list, best first
            s += center(mid + 2, "   RECORDS   ")
            for n, v in enumerate(g.records[:max(0, min(10, rows - mid - 3))]):
                s += center(mid + 3 + n, f"{n + 1:2d}.  {show(g, v):>8}")
    elif g.clock < 1 and not g.done:
        s += center(mid, "GO!")
    if g.msg_t and not g.done:
        s += center(mid + 2, g.msg)
    if g.pending and not g.done:
        s += center(mid + 4, f"DRIFT {int(g.pending)}" + (f"  x{g.combo}" if g.combo > 1 else ""))
    if g.done:
        place = g.records.index(g.result) + 1
        if g.mode == "drift":
            s += center(mid, "FINISH!")
            s += center(mid + 2, f"Drift score: {int(g.result)}    Time: {fmt(g.clock)}")
        elif g.mode == "infinite":
            s += center(mid, "TIME UP!")
            s += center(mid + 2, f"Score: {int(g.result)}    Checkpoints: {g.checkpoints}")
        else:
            s += center(mid, "FINISHED!")
            s += center(mid + 2, "Laps: " + "  ".join(fmt(t) for t in g.laps))
        s += center(mid + 4, "NEW RECORD!" if place == 1 else f"Place #{place} of {len(g.records)}   Best: {best}")
        for n, name in enumerate(g.new_cars):
            s += center(mid + 6 + n, f"NEW CAR UNLOCKED: {name}!")
        s += center(mid + 7 + len(g.new_cars), "Enter = play again    m = menu    q = quit")
    return s + "\x1b[0m"


# ---------------- keyboard ----------------
KEY_RE = re.compile(rb"\x1b\[\?\d+u|\x1b\[(\d*)(?:;(\d*)(?::(\d+))?)?([A-Za-z~])|\x1bO([A-D])|([\s\S])")
LETTERS = {"w": "up", "s": "down", "a": "left", "d": "right", "q": "quit", "\x1b": "esc",
           "\x03": "quit", "\r": "enter", "\n": "enter", " ": "drift", "1": "laps", "2": "infinite", "3": "touge",
           "4": "garage", "m": "menu"}
ARROWS = {"A": "up", "B": "down", "C": "right", "D": "left"}
HELD = {"up", "down", "left", "right", "drift"}     # keys that count while you hold them


def parse(data):
    """Turn raw terminal bytes into (key, event) pairs. Event 1 = press, 2 = repeat, 3 = release.
    ("kitty", 1) means the terminal speaks the kitty keyboard protocol (it tells us about releases)."""
    out = []
    for m in KEY_RE.finditer(data):
        num, mods, ev, final, ss3, ch = m.groups()
        if m.group(0).startswith(b"\x1b[?"):
            out.append(("kitty", 1))
            continue
        if ch is not None:
            name = LETTERS.get(ch.decode("latin1").lower())
        elif ss3:
            name = ARROWS[ss3.decode()]
        elif final == b"u":
            code = int(num or 0)
            name = "quit" if code == 99 and (int(mods or 1) - 1) & 4 else LETTERS.get(chr(code).lower())
        else:
            name = ARROWS.get(final.decode())
        if name:
            out.append((name, int(ev or 1)))
    return out


def main():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    for sig in (signal.SIGTERM, signal.SIGHUP):     # closed or killed: still clean up the terminal
        signal.signal(sig, lambda *_: sys.exit(0))
    tty.setcbreak(fd)
    # alternate screen, hide cursor, ask for the kitty keyboard protocol, ask if it worked
    sys.stdout.write("\x1b[?1049h\x1b[?25l\x1b[>11u\x1b[?u")
    sys.stdout.flush()
    g, kitty, held = Game(), False, {}
    try:
        last = time.monotonic()
        while True:
            now = time.monotonic()
            dt, last = min(0.1, now - last), now
            pressed = set()
            while select.select([fd], [], [], 0)[0]:
                for name, ev in parse(os.read(fd, 1024)):
                    if name == "kitty":
                        kitty = True
                    elif name in HELD:
                        if ev == 1:
                            pressed.add(name)                # (the garage uses single presses)
                        if ev == 3:
                            held.pop(name, None)
                        elif kitty:
                            held[name] = math.inf          # held until the release event
                        else:   # old-style terminal: no releases, so guess with a timer
                            held[name] = now + (0.12 if held.get(name, 0) > now else 0.5)
                    elif ev != 3:
                        pressed.add(name)
            if "quit" in pressed or ("esc" in pressed and g.garage is None):
                break
            if g.garage is not None:                       # in the garage
                p = load_progress()
                if "left" in pressed or "right" in pressed:
                    g.garage = (g.garage + (1 if "right" in pressed else -1)) % len(CARS)
                elif "enter" in pressed and g.garage in p["unlocked"]:
                    p["car"] = g.garage
                    save_progress(p)
                    g.car, g.garage = CARS[g.garage], None
                elif pressed & {"menu", "esc"}:
                    g.garage = None
            elif g.mode is None and "garage" in pressed:
                g.garage = load_progress()["car"]
            elif g.mode is None and pressed & {"laps", "infinite", "touge", "enter"}:
                mode = "infinite" if "infinite" in pressed else "drift" if "touge" in pressed else "laps"
                g = Game(mode, g.tod)
            elif "menu" in pressed:
                g = Game(None, g.tod)
            elif "enter" in pressed and g.done:
                g = Game(g.mode, g.tod)
            update(g, dt, {k for k, t in held.items() if t > now}, now)

            cols, rows = os.get_terminal_size()
            if cols < 40 or rows < 12:
                frame = "\x1b[0m\x1b[2J\x1b[1;1HPlease make the terminal bigger."
            else:
                frame = render(g, cols, rows * 2) + hud(g, cols, rows)
            sys.stdout.write(frame)                     # one write per frame = no flicker
            sys.stdout.flush()
            time.sleep(max(0.0, 1 / FPS - (time.monotonic() - now)))
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[<u\x1b[0m\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def selftest():
    global DATA_DIR
    import tempfile
    DATA_DIR = tempfile.mkdtemp()                   # don't touch the real records
    g = Game("laps")
    assert abs(g.ys[-1] - g.ys[0]) < SEG, "track must come back to its start height"
    assert parse(b"\x1b[A") == [("up", 1)]
    assert parse(b"\x1b[1;1:3D") == [("left", 3)]
    assert parse(b"\x1b[119;1:3u") == [("up", 3)]
    assert parse(b"\x1b[?11u") == [("kitty", 1)]
    assert parse(b"q") == [("quit", 1)] and parse(b"\x1b[27u") == [("esc", 1)]
    for car in CARS:                                # every car's pictures are proper rectangles
        for art in (car["art"], car["rear"], car["half"], car["side"]):
            assert len({len(row) for row in art}) == 1 and all(ch in car["pal"] for row in art for ch in row if ch != "."), car["name"]
    t0 = time.perf_counter()
    for i in range(300):                            # drive full speed for 10 seconds
        update(g, 1 / 30, {"up"}, i / 30)
        frame = render(g, 200, 100)
    assert frame.count("▀") == 200 * 50
    for tod in (0.0, 0.25, 0.5, 0.8):               # night, dawn, noon, sunset all draw fine
        g.tod = tod
        assert render(g, 200, 100).count("▀") == 200 * 50
    assert g.pos > 0 and g.clock > 0
    g = Game("infinite")                            # infinite: road keeps growing, score adds up
    for i in range(3000):
        update(g, 1 / 30, {"up"}, i / 30)
    assert len(g.curve) > g.pos / SEG + DRAW and g.score > 0 and g.checkpoints > 0, (g.score, g.checkpoints)
    if g.done:
        assert load_records("infinite") == [g.result]
    print(f"ok - score {int(g.score)}, {g.checkpoints} checkpoints, done={g.done}")
    k = Game("infinite"); k.clock, k.score = 1, KONBINI_SCORE
    update(k, 0.1, {"up"}, 0)
    assert k.konbini and any(w == "konbini" for spr in k.sprites for _, w, _ in spr)
    k.tod, k.braking = 0.0, True
    assert render(k, 200, 100).count("▀") == 200 * 50
    print("ok - konbini shows up at 20000 points, night lights draw fine")
    d = Game("drift"); d.clock = 0.1                  # drift: a simple bot drives the mountain pass
    for i in range(4000):
        seg = int((d.pos + PLAYER_Z) // SEG)
        curve = d.curve[seg + 8]                        # look a bit ahead
        keys = {"up"}
        if abs(curve) > 2:
            keys.add("right" if curve > 0 else "left")
            if abs(d.slip) < 0.3 and d.speed > MAX_SPEED * 0.5:
                keys.add("drift")
        if d.x > 0.8: keys.discard("right")
        if d.x < -0.8: keys.discard("left")
        update(d, 1 / 30, keys, i / 30)
        if d.done:
            break
    assert d.score > 0 and d.done, (d.score, d.done, d.pos / SEG)
    assert render(d, 200, 100).count("▀") == 200 * 50
    d.done, d.pending, d.bonk, d.x = False, 500.0, 0.0, 1.3     # hitting the guardrail loses the drift
    update(d, 1 / 30, set(), 0)
    assert d.pending == 0 and d.combo == 1 and abs(d.x) <= 1.12
    p = load_progress()                             # the drift run above unlocked cars; laps unlocks the RX-7
    assert 0 in p["unlocked"] and 1 not in p["unlocked"] and p["races"] >= 2
    lp = Game("laps"); lp.clock, lp.laps, lp.speed, lp.pos = 70.0, [23.0, 23.0], MAX_SPEED, lp.length - 50
    update(lp, 1 / 30, set(), 0)
    assert lp.done and "Mazda RX-7 FD" in lp.new_cars and 1 in load_progress()["unlocked"]
    m = Game(); m.garage = 2                         # garage draws a locked car (NSX needs 5 races)
    assert render(m, 200, 100).count("▀") == 200 * 50 and "LOCKED" in hud(m, 200, 50)
    m.garage = 1
    assert "Enter = drive" in hud(m, 200, 50)
    print(f"ok - drift bot finished the pass with {int(d.score)} points in {fmt(d.clock)}")
    print(f"ok - {(time.perf_counter() - t0) / 300 * 1000:.1f} ms per frame, track {len(g.curve)} segments")


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
    elif "--test" in sys.argv:
        selftest()
    else:
        main()
