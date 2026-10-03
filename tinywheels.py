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
  1            pick 3 LAPS mode (on the title screen)
  2            pick INFINITE mode (on the title screen)
  Enter        play again on a new random track (after you finish)
  M            back to the title screen
  Q / Esc      quit

3 LAPS: race 3 laps as fast as you can.
INFINITE: the road never ends. You start with 30 seconds; every red torii gate
is a checkpoint that adds time. Score points for distance (double while
drifting = steering hard at speed) and for jumps. Drive until time runs out!

Day turns into night and back every 3 minutes.
Yellow-black stripes are ramps (jump!). Lanterns, rocks and pines
slow you down, and so does the deep snow.
Your records are saved in ~/.local/share/tinywheels/
"""
import math, os, random, re, select, signal, sys, termios, time, tty

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
BEAM     = ["138;132;118", "130;124;112"]   # road lit by the headlights
# The car: a white-and-black "panda" AE86 hatchback, seen from behind
CAR = {"w": "245;245;245", "k": "35;40;60", "r": "220;30;40", "o": "255;150;40",
       "b": "15;15;20", "p": "230;230;210", "t": "45;45;45"}
CAR_ART = [                      # one letter per pixel, "." = see-through
    "....wwwwwwww....",
    "...wkkkkkkkkw...",
    "..wkkkkkkkkkkw..",
    ".wwwwwwwwwwwwww.",
    "wrrooowwwwooorrw",
    "bbbbbbbbbbbbbbbb",
    "bbbbbbppppbbbbbb",
    "tt............tt",
    "tt............tt",
]
# Things that make their own light. Everything else gets darker (and bluer) at night.
GLOWS = {GLOW, WINDOW, VEND_LIT, PAPER, MOON, STAR, *BEAM, *DRINKS, CAR["r"], CAR["o"]}

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
START_TIME = 30          # infinite mode: seconds on the clock at the start
CHECKPOINT = 400         # infinite mode: a torii checkpoint every this many segments
CHECKPOINT_TIME = 10     # infinite mode: seconds added by the first checkpoint (later ones give less)


# ---------------- random track ----------------
def ease_in(a, b, p):    return a + (b - a) * p * p
def ease_out(a, b, p):   return a + (b - a) * (1 - (1 - p) ** 2)
def ease_inout(a, b, p): return a + (b - a) * (0.5 - math.cos(p * math.pi) / 2)


def add_piece(g, n_in, n_hold, n_out, c, dy, deco=True):
    """Add one stretch of road (curve c, going up/down by dy) with trees, maybe a ramp, and obstacles.
    A track is a list of segments; each has a curve, a height, a kind and some sprites."""
    total = n_in + n_hold + n_out
    ramp = random.randrange(total - 4) if deco and random.random() < 0.25 else -9
    for k in range(total):
        if k < n_in:            cv = ease_in(0, c, k / n_in)
        elif k < n_in + n_hold: cv = c
        else:                   cv = ease_out(c, 0, (k - n_in - n_hold) / n_out)
        i = len(g.curve)
        g.curve.append(cv)
        g.ys.append(ease_inout(g.y_end, g.y_end + dy, k / total))
        g.kind.append("ramp" if ramp <= k < ramp + 4 else "")
        spr = []
        if random.random() < 0.35:                          # sakura trees
            spr.append((random.choice([-1, 1]) * random.uniform(1.4, 3.5), "tree", random.random()))
        if i % 40 == 20:                                     # stone lanterns line the road
            spr += [(-1.35, "lantern", 0), (1.35, "lantern", 0)]
        if random.random() < 1 / 90:
            spr.append((random.choice([-1, 1]) * random.uniform(2.8, 4.5), "house", 0))
        if random.random() < 1 / 150:
            spr.append((random.choice([-1, 1]) * 1.6, "vending", 0))
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


def grow(g):
    """Infinite mode: keep building road just ahead of the car."""
    # ponytail: old road is never thrown away (~1 MB per 10 min of driving); trim it if you drive for days
    while len(g.curve) < g.pos / SEG + DRAW + 20:
        random_piece(g)


# ---------------- game state ----------------
class Game:
    def __init__(self, mode=None, tod=0.3):   # mode: None = title menu, "laps" or "infinite"
        self.mode = mode
        self.tod = tod               # time of day, 0..1 (0.3 = morning)
        self.pos = self.x = self.speed = 0.0
        self.curve, self.ys, self.kind, self.sprites = [], [], [], []
        self.y_end = 0.0
        add_piece(self, 0, 40, 0, 0, 0, deco=False)            # straight start
        self.kind[4] = self.kind[5] = "finish"
        self.sprites[4].append((0, "torii", 0))
        if mode == "infinite":
            self.length = math.inf
            grow(self)
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
        self.parts = [[random.random(), random.random(), random.uniform(-0.03, 0.03),
                       random.uniform(0.05, 0.12) if i % 2 else random.uniform(0.1, 0.22),
                       random.choice(PETALS) if i % 2 else FLAKE, random.uniform(0, 6.3)]
                      for i in range(160)]   # [x, y, drift, fall speed, color, wobble], x/y in 0..1


def records_file(mode):
    return os.path.join(DATA_DIR, "infinite.txt" if mode == "infinite" else "records.txt")


def load_records(mode):
    """Laps: times, lowest first. Infinite: scores, highest first."""
    if mode is None:
        return []
    try:
        with open(records_file(mode)) as f:
            return sorted((float(t) for t in f.read().split()), reverse=mode == "infinite")
    except (OSError, ValueError):
        return []


def finish(g, value):
    g.done, g.result = True, value
    g.records = sorted(g.records + [value], reverse=g.mode == "infinite")
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(records_file(g.mode), "w") as f:
        f.write("\n".join(f"{t:.3f}" for t in g.records) + "\n")


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def show(g, v):
    """A record as text: a time for laps, a score for infinite."""
    return str(int(v)) if g.mode == "infinite" else fmt(v)


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
    g.x += steer * dt * 2.5 * pct * (0.4 if air else 1)
    g.x -= dt * 2 * pct * pct * g.curve[seg] * CENTRIFUGAL
    if "up" in keys and not g.done:     g.speed += ACCEL * dt
    elif "down" in keys and not g.done: g.speed -= BRAKE * dt
    else:                               g.speed -= DECEL * dt
    if abs(g.x) > 1 and not air and g.speed > OFF_LIMIT:
        g.speed -= OFF_DECEL * dt
    g.x = max(-3.0, min(3.0, g.x))
    g.speed = max(0.0, min(MAX_SPEED, g.speed))
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
        if g.time_left <= 0:
            g.time_left = 0.0
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
                bonus = max(4.0, CHECKPOINT_TIME - g.checkpoints * 0.25)
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


def background(w, h, horizon, sky, tod, dark):
    px = [[SKY] * w for _ in range(horizon)] + [[FAR_SNOW] * w for _ in range(h - horizon)]
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
        circle(px, mx + mr * 0.5, my - mr * 0.2, mr * 0.85, SKY, horizon)    # take a bite: crescent moon
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
        rect(px, cx - 60 * s, cx + 60 * s, gy - 250 * s, gy, TRUNK, clip)
        for k in range(3):
            top, tall, wide = gy - (1300 - k * 300) * s, 500 * s, (220 + k * 70) * s
            for row in range(max(0, int(top)), min(clip, int(top + tall))):
                d = (row - top) / tall
                span(px[row], cx - wide * d, cx + wide * d, SNOW_CAP if d < 0.3 else PINE)
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
    cam_y = y0 + (y1 - y0) * frac + CAM_H + g.jump_h
    cam_x = g.x * ROAD_W
    light = light_at(g.tod)
    dark = max(0.0, min(1.0, (0.85 - sum(light) / 3) / 0.5))     # 0 = day, 1 = night
    px = background(w, h, horizon, g.sky, g.tod, dark)

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
        road = RAMP[i % 2] if k == "ramp" else FINISH[i % 2] if k == "finish" else ROAD[stripe]
        top = max(0, math.ceil(yf))
        for r in range(top, min(maxy, math.ceil(yn))):
            t = (yn - r) / (yn - yf)
            c, hw = cn + (cf - cn) * t, hn + (hf - hn) * t
            row = [SNOW[stripe]] * w
            span(row, c - hw * 1.12, c + hw * 1.12, RUMBLE[stripe])
            span(row, c - hw, c + hw, road)
            if stripe and not k:
                span(row, c - hw * 0.03, c + hw * 0.03, LANE)
            px[r] = row
        maxy = top

    if dark > 0.35:                                 # headlights light up the road at night
        top = int(h * 0.58)
        for r in range(top, h):
            half, row = w * (0.05 + 0.2 * (r - top) / (h - top)), px[r]
            for c in range(max(0, int(w / 2 - half)), min(w, int(w / 2 + half))):
                if row[c] in ROAD:
                    row[c] = BEAM[row[c] == ROAD[1]]

    for i, s, c, gy, clip in reversed(seen):        # trees, obstacles, gates: far to near
        for sx, what, v in g.sprites[i]:
            draw_sprite(px, what, v, c + s * sx * ROAD_W, gy, s, clip)

    for p in g.parts:
        r, col = int(p[1] * h), int(p[0] * w)
        if 0 <= r < h:
            span(px[r], col, col + (2 if p[4] != FLAKE else 1), p[4])

    cs = max(1, round(w / 90))                      # the car
    lift = int(g.jump_h / 40)
    bounce = random.randint(0, 1) if abs(g.x) > 1 and g.speed > 0 and not lift else 0
    x0, y0 = w // 2 - len(CAR_ART[0]) * cs // 2, h - len(CAR_ART) * cs - 2 - lift - bounce
    if lift:
        rect(px, x0, x0 + len(CAR_ART[0]) * cs, h - 3, h - 1, SHADOW, h)
    elif g.drifting:                                # drift smoke from the tires
        for _ in range(8):
            sx = x0 + random.choice([0, len(CAR_ART[0]) * cs]) + random.uniform(-3, 3) * cs
            sy = h - 3 - random.uniform(0, 3) * cs
            rect(px, sx - cs, sx + cs, sy - cs, sy, SMOKE, h)
    for r, line in enumerate(CAR_ART):
        for c, ch in enumerate(line):
            if ch != ".":
                rect(px, x0 + c * cs, x0 + (c + 1) * cs, y0 + r * cs, y0 + (r + 1) * cs, CAR[ch], h)

    tinted = {}                                     # every color, darkened for the time of day

    def tint(c):
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
    if g.mode is None:
        bar = " TINY WHEELS"
    elif g.mode == "infinite":
        bar = (f" SCORE {int(g.score)}   TIME LEFT {g.time_left:4.1f}   CHECKPOINTS {g.checkpoints}"
               f"   BEST {best}   {kmh:3d} km/h" + ("   DRIFT x2" if g.drifting else ""))
    else:
        lap = min(len(g.laps) + 1, LAPS)
        now = g.clock if g.done else max(0.0, g.clock)
        bar = f" LAP {lap}/{LAPS}   TIME {fmt(now)}   BEST {best}   {kmh:3d} km/h"
    s = f"\x1b[1;1H{style}{bar[:cols].ljust(cols)}"

    if g.mode is None:
        s += center(mid, "T I N Y   W H E E L S")
        s += center(mid + 2, "1 = 3 LAPS      fastest time wins     ")
        s += center(mid + 3, "2 = INFINITE    drive on, score points")
        s += center(mid + 5, "q = quit")
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
    if g.done:
        place = g.records.index(g.result) + 1
        if g.mode == "infinite":
            s += center(mid, "TIME UP!")
            s += center(mid + 2, f"Score: {int(g.result)}    Checkpoints: {g.checkpoints}")
        else:
            s += center(mid, "FINISHED!")
            s += center(mid + 2, "Laps: " + "  ".join(fmt(t) for t in g.laps))
        s += center(mid + 4, "NEW RECORD!" if place == 1 else f"Place #{place} of {len(g.records)}   Best: {best}")
        s += center(mid + 6, "Enter = play again    m = menu    q = quit")
    return s + "\x1b[0m"


# ---------------- keyboard ----------------
KEY_RE = re.compile(rb"\x1b\[\?\d+u|\x1b\[(\d*)(?:;(\d*)(?::(\d+))?)?([A-Za-z~])|\x1bO([A-D])|([\s\S])")
LETTERS = {"w": "up", "s": "down", "a": "left", "d": "right", "q": "quit", "\x1b": "quit",
           "\x03": "quit", "\r": "enter", "\n": "enter", " ": "enter", "1": "laps", "2": "infinite", "m": "menu"}
ARROWS = {"A": "up", "B": "down", "C": "right", "D": "left"}


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
                    elif name in ARROWS.values():
                        if ev == 3:
                            held.pop(name, None)
                        elif kitty:
                            held[name] = math.inf          # held until the release event
                        else:   # old-style terminal: no releases, so guess with a timer
                            held[name] = now + (0.12 if held.get(name, 0) > now else 0.5)
                    elif ev != 3:
                        pressed.add(name)
            if "quit" in pressed:
                break
            if g.mode is None and pressed & {"laps", "infinite", "enter"}:
                g = Game("infinite" if "infinite" in pressed else "laps", g.tod)
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
    assert parse(b"q") == [("quit", 1)]
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
    print(f"ok - {(time.perf_counter() - t0) / 300 * 1000:.1f} ms per frame, track {len(g.curve)} segments")


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
    elif "--test" in sys.argv:
        selftest()
    else:
        main()
