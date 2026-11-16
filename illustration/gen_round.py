"""NICER round illustration: vector redraw of the consortium's hand-drawn badge, without lettering.

Circular frame; oblique view of an ice sheet (model mesh on its surface) flowing past mountains into
a floating shelf; layered cut face; ocean block with sub-shelf circulation; bedrock; land with a cliff;
sun, clouds, wind and surface fluxes; iceberg and research vessel. Coordinates follow the original
drawing (centre ~ (516, 512)).

Usage: python3 gen_round.py OUTDIR
"""
import math, pathlib, random, sys

OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)

CX, CY = 516.0, 512.0
R_OUT, R_IN, R_SCENE = 490.0, 462.0, 452.0
INK = "#1D2733"
SUNC, SUN_EDGE = "#F2B630", "#E0892B"
ICE_TOP, ICE_FACE = "#F3F9FD", "#CFE5F3"
SEA_TOP, SEA_RIGHT, CAVITY = "#3E8ED6", "#1F5FA8", "#1B3E86"
ROCK, ROCK_DARK = "#7A5432", "#5E3F24"
LANDG, CLIFF = "#7DB35A", "#8C8378"
MOUNT, MOUNT_DARK = "#8F96BA", "#6F769C"
WIND = "#6C8FC0"
FLUX_B, FLUX_P = "#4F7FD8", "#7E5BB8"
WARMC, COOLC = "#D9546B", "#8FB2EE"
BANDS = ["#1E4E9C", "#3F86D3", "#2C5DB5", "#58C5E8", "#3A4FA8", "#6F5BB5", "#47B1DC", "#2A5AAE", "#5C8FE0"]
OW = 3.0   # outline width


# ------------------------------------------------------------------ helpers
def P(pts, close=False):
    return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + ("Z" if close else "")


def spline(pts, n=12):
    """Catmull-Rom through pts."""
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def resample(pts, n):
    """n+1 points equally spaced in arc length along a polyline."""
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        d.append(d[-1] + math.dist(a, b))
    out, j = [], 0
    for i in range(n + 1):
        s = d[-1] * i / n
        while j < len(d) - 2 and d[j + 1] < s:
            j += 1
        f = (s - d[j]) / max(d[j + 1] - d[j], 1e-9)
        out.append((pts[j][0] + f * (pts[j + 1][0] - pts[j][0]), pts[j][1] + f * (pts[j + 1][1] - pts[j][1])))
    return out


def lerp(a, b, f):
    return (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]))


def shape(pts, fill, stroke=INK, w=OW, extra=""):
    return f'<path d="{P(pts, True)}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round"{extra}/>'


def line(pts, color=INK, w=OW, op=1.0, cap="round"):
    return (f'<path d="{P(pts)}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="{cap}" '
            f'stroke-linejoin="round" opacity="{op}"/>')


def head(tip, b, color, hw, outline=True):
    dx, dy = tip[0] - b[0], tip[1] - b[1]; L = math.hypot(dx, dy)
    nx, ny = -dy / L * hw / 2, dx / L * hw / 2
    tri = [tip, (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny)]
    return shape(tri, color, INK, 2.0) if outline else f'<path d="{P(tri, True)}" fill="{color}"/>'


def trim(pts, hl):
    acc, i = 0.0, len(pts) - 1
    while i > 0:
        seg = math.dist(pts[i], pts[i - 1])
        if acc + seg >= hl:
            f = (hl - acc) / seg
            b = (pts[i][0] + f * (pts[i - 1][0] - pts[i][0]), pts[i][1] + f * (pts[i - 1][1] - pts[i][1]))
            return pts[:i] + [b], b
        acc += seg; i -= 1
    return [pts[0]], pts[0]


def arrow(pts, color, w=6.0, both=False):
    """Cartoon arrow: ink-outlined coloured line with outlined triangular head(s)."""
    hl, hw = 2.6 * w, 3.0 * w
    body, b = trim(pts, hl)
    heads = head(pts[-1], b, color, hw)
    if both:
        rev, b0 = trim(body[::-1], hl); body = rev[::-1]
        heads += head(pts[0], b0, color, hw)
    return line(body, INK, w + 3.5) + line(body, color, w) + heads


def wavy(p0, p1, amp=6.0, lam=22.0):
    L = math.dist(p0, p1); ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    n = int(L / 1.5)
    return [(p0[0] + ux * s - uy * a, p0[1] + uy * s + ux * a)
            for s in (L * i / n for i in range(n + 1))
            for a in [amp * math.sin(2 * math.pi * s / lam) * min(1.0, (L - s) / 12, s / 6 + 0.3)]]


def curl(pts, sign=1, R=12.0, turn=1.8 * math.pi):
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    th = math.atan2(y1 - y0, x1 - x0); x, y = x1, y1; out = list(pts); done, ds = 0.0, 1.0
    while done < turn:
        k = 1.0 / (R * (1 - 0.6 * done / turn))
        th += sign * k * ds; done += k * ds
        x += math.cos(th) * ds; y += math.sin(th) * ds
        out.append((x, y))
    return out


def cloud(puffs, x0, x1, ybot, h):
    """Outlined cloud: puffs on a flat, rounded base (outline drawn under the fill)."""
    def parts(d, c):
        return ("".join(f'<circle cx="{x}" cy="{y}" r="{r + d}" fill="{c}"/>' for x, y, r in puffs)
                + f'<rect x="{x0 - d}" y="{ybot - h - d}" width="{x1 - x0 + 2 * d}" height="{h + 2 * d}" '
                  f'rx="{h / 2 + d}" fill="{c}"/>')
    return parts(OW / 2, INK) + parts(-OW / 2, "#FFFFFF")


# ------------------------------------------------------------------ geometry
# ice-sheet top surface: back edge (against mountains and land) and front edge (cut face, then shelf front)
BACK = spline([(40, 422), (95, 402), (160, 372), (235, 358), (330, 362), (420, 386), (500, 410), (560, 440),
               (640, 488), (720, 526), (786, 546)], 8)
FRONT_LEFT = spline([(40, 422), (120, 430), (210, 474), (330, 548), (450, 622), (576, 690)], 10)
SHELF_FRONT = [(576, 690), (602, 662), (640, 646), (690, 628), (700, 600), (776, 582), (786, 552), (786, 546)]
FRONT = FRONT_LEFT + SHELF_FRONT[1:]
ICE_POLY = BACK + FRONT[::-1][1:]
CLIFF_H = 28.0   # shelf-front cliff height at the far end; tapers towards the front corner


def cliff_bottom():
    n = len(SHELF_FRONT) - 2
    return [(x, y + 6 + (CLIFF_H - 6) * i / n) for i, (x, y) in enumerate(SHELF_FRONT[:-1])]

# bedrock surface; the ice rests on it up to the grounding line, then floats as a shelf
BED = spline([(30, 772), (120, 756), (210, 748), (330, 744), (430, 764), (520, 808), (590, 852),
              (640, 900), (660, 1010)], 8)
XGL = 330.0
SHELF_BASE = spline([(XGL, 744), (420, 724), (500, 708), (576, 698)], 10)
# layered cut face below FRONT_LEFT: its base follows the bed to the grounding line, then the shelf base
LAYER_BOTTOM = [(x, y + 1) for x, y in BED if x < XGL] + SHELF_BASE


def layer_face():
    top = resample(FRONT_LEFT, 120); bot = resample(LAYER_BOTTOM, 120)
    n = len(BANDS); out = []
    for i in range(n):
        f0, f1 = i / n, (i + 1) / n
        # bands thicken towards the bottom-left and bulge, as in the original
        g = lambda f, k: f ** 0.9
        a = [lerp(t, b, g(f0, k)) for k, (t, b) in enumerate(zip(top, bot))]
        c = [lerp(t, b, g(f1, k)) for k, (t, b) in enumerate(zip(top, bot))]
        out.append(shape(a + c[::-1], BANDS[i], INK, 1.8))
    return "".join(out)


def mesh():
    """Jittered triangular model mesh on the ice surface."""
    rnd = random.Random(4)
    nu, nv = 11, 4
    fr, bk = resample(FRONT, nu * 4), resample(BACK, nu * 4)
    grid = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            p = lerp(fr[i * 4], bk[i * 4], j / nv)
            if 0 < i < nu and 0 < j < nv:
                p = (p[0] + rnd.uniform(-9, 9), p[1] + rnd.uniform(-6, 6))
            row.append(p)
        grid.append(row)
    segs = []
    for j in range(nv + 1):
        for i in range(nu):
            segs.append((grid[j][i], grid[j][i + 1]))
    for j in range(nv):
        for i in range(nu + 1):
            segs.append((grid[j][i], grid[j + 1][i]))
            if i < nu:
                segs.append((grid[j][i], grid[j + 1][i + 1]) if (i + j) % 2 else (grid[j][i + 1], grid[j + 1][i]))
    return "".join(line([a, b], "#5F7385", 1.4, 0.8) for a, b in segs)


def cliff_face():
    top, bot = SHELF_FRONT[:-1], cliff_bottom()
    face = shape(top + bot[::-1], ICE_FACE, INK, 2.4)
    stripes = "".join(line([lerp(a, b, f), lerp(c, d, f)], "#A9CBE2", 1.6)
                      for a, b, c, d in zip(top, top[1:], [(x, y - 3) for x, y in bot], [(x, y - 3) for x, y in bot[1:]])
                      for f in (0.3, 0.7))
    return face + stripes


def mountains():
    out = shape([(30, 420), (70, 380), (120, 332), (150, 310), (175, 322), (205, 284), (240, 318), (270, 300),
                 (305, 322), (335, 330), (372, 334), (405, 356), (445, 392), (40, 430)], MOUNT)
    out += shape([(205, 284), (240, 318), (230, 360), (195, 352)], MOUNT_DARK, INK, 1.6)
    out += shape([(270, 300), (305, 322), (300, 360), (282, 352)], MOUNT_DARK, INK, 1.6)
    for pk in ((205, 284), (150, 310), (270, 300), (372, 334)):
        x, y = pk
        out += shape([(x, y), (x + 15, y + 15), (x + 7, y + 12), (x, y + 18), (x - 8, y + 12), (x - 14, y + 14)],
                     "#FFFFFF", INK, 1.6)
    return out


def land():
    gpoly = [(540, 440), (600, 420), (668, 428), (730, 446), (752, 462), (738, 480), (700, 492), (664, 506),
             (640, 520), (600, 480)]
    green = (f'<path d="{P(gpoly, True)}" fill="url(#landg)" stroke="{INK}" stroke-width="{OW}" '
             f'stroke-linejoin="round"/>'
             + f'<path d="{P([(640, 446), (690, 440), (722, 452), (690, 462), (650, 462)], True)}" fill="#C4DC8A" '
               f'opacity="0.7"/>'
             + "".join(line([(x, y), (x + 14, y + 1)], "#3F6B2E", 1.8, 0.85) for x, y in
                       ((610, 436), (630, 450), (660, 438), (700, 470), (720, 458), (676, 480), (612, 466),
                        (640, 492), (690, 452))))
    cliff = shape([(664, 506), (700, 492), (738, 480), (752, 462), (764, 500), (772, 548), (735, 550), (705, 534),
                   (680, 520)], CLIFF)
    cracks = line([(740, 488), (746, 520), (742, 545)], INK, 1.6) + line([(712, 500), (718, 530)], INK, 1.6)
    return green + cliff + cracks


def ocean():
    right = shape([(720, 700), (980, 570), (980, 1010), (720, 1010)], SEA_RIGHT)
    top = shape(cliff_bottom() + [(980, 576), (980, 580), (720, 700), (576, 700)], SEA_TOP)
    ripples = "".join(line(spline(r, 6), "#9CCBF2", 2.2) for r in
                      ([(660, 682), (680, 677), (698, 682)], [(722, 640), (746, 634), (770, 640)],
                       [(800, 600), (830, 594), (860, 602)], [(905, 584), (930, 580), (950, 586)],
                       [(820, 640), (845, 634), (868, 640)]))
    return right + top + ripples


def cavity():
    water = shape(SHELF_BASE + [(720, 700), (720, 1010), (XGL, 1010)], CAVITY)
    rock = (f'<path d="{P(BED + [(30, 1010)], True)}" fill="url(#rockg)" stroke="{INK}" stroke-width="{OW}" '
            f'stroke-linejoin="round"/>')
    strata = (line(spline([(60, 840), (200, 820), (330, 820), (450, 860), (540, 930)], 8), ROCK_DARK, 2.0)
              + line(spline([(80, 900), (220, 884), (360, 892), (470, 940)], 8), ROCK_DARK, 1.6, 0.7))
    marks = "".join(line([(x, y), (x + 16, y - 2)], c, 2.0, 0.8) for x, y, c in
                    ((90, 790, "#A7794C"), (170, 800, "#A7794C"), (260, 786, "#A7794C"), (380, 800, "#A7794C"),
                     (130, 860, ROCK_DARK), (300, 856, ROCK_DARK), (420, 880, ROCK_DARK), (240, 940, ROCK_DARK),
                     (110, 950, "#A7794C"), (360, 960, "#A7794C"), (500, 980, ROCK_DARK)))
    return water + rock + strata + marks


GRADS = []   # per-stroke colour gradients, collected into <defs>


def ribbon(pts, wmax, fill, c2=None, head_len=0.0, taper_in=0.12, taper_out=True, end=0.35, ow=1.6):
    """Calligraphic stroke: filled, outlined ribbon whose width swells and tapers along pts.
    end: width at the end as a fraction of wmax (if taper_out). c2: second colour for a gradient from start
    to end. head_len > 0 adds an arrowhead at the end."""
    pts = resample(pts, max(8, int(sum(math.dist(a, b) for a, b in zip(pts, pts[1:])) / 2)))
    tip = None
    if head_len:
        tip = pts[-1]; pts, _ = trim(pts, head_len)
        pts = resample(pts, len(pts) * 2)
    n = len(pts) - 1; L, R = [], []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, n)]
        dx, dy = b[0] - a[0], b[1] - a[1]; d = math.hypot(dx, dy) or 1
        t = i / n
        w = wmax * min(1.0, 0.25 + t / taper_in) * ((end + (1 - end) * (1 - t) ** 0.6) if taper_out else 1.0)
        L.append((x - dy / d * w / 2, y + dx / d * w / 2)); R.append((x + dy / d * w / 2, y - dx / d * w / 2))
    paint = fill
    if c2:
        gid = f"g{len(GRADS)}"
        GRADS.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{pts[0][0]:.0f}" '
                     f'y1="{pts[0][1]:.0f}" x2="{pts[-1][0]:.0f}" y2="{pts[-1][1]:.0f}">'
                     f'<stop offset="0" stop-color="{fill}"/><stop offset="1" stop-color="{c2}"/></linearGradient>')
        paint = f"url(#{gid})"
    out = shape(L + R[::-1], paint, INK, ow)
    if tip:
        out += head(tip, pts[-1], c2 or fill, wmax * 2.6)
    return out


def spiral(pts, sign=-1, R=14.0, turns=1.6):
    """Continue a path into a spiral that tightens towards its centre."""
    return curl(pts, sign=sign, R=R, turn=turns * 2 * math.pi)


def circulation():
    """Sub-shelf circulation after the hand-drawn original: a clockwise overturning arrow under the shelf, a pale swirl, a warm inflow that winds into
    an eddy, and a warm current rising towards the shelf."""
    cool, warm = "#A9CBF2", "#E0607A"
    return (ribbon(spline([(450, 758), (458, 738), (476, 727), (494, 723), (514, 719)], 8), 8, cool, head_len=16,
                     taper_out=False)
            + ribbon(spiral(spline([(514, 772), (540, 754), (564, 746)], 8), -1, 13, 1.25), 9, cool)
            + ribbon(spiral(spline([(496, 792), (546, 804), (592, 796)], 8), -1, 22, 1.35), 11, warm, cool)
            + ribbon(spline([(604, 818), (664, 824), (692, 790), (694, 744)], 8), 8, warm, head_len=16,
                     taper_out=False))


SUN = (640, 212, 38)


def sun():
    cx, cy, r = SUN
    rays = []
    for k in range(14):
        a = 2 * math.pi * k / 14; b = math.pi / 14
        rays.append([(cx + (r + 2) * math.cos(a - b), cy + (r + 2) * math.sin(a - b)),
                     (cx + (r + 24) * math.cos(a), cy + (r + 24) * math.sin(a)),
                     (cx + (r + 2) * math.cos(a + b), cy + (r + 2) * math.sin(a + b))])
    return ("".join(shape(t, SUNC, SUN_EDGE, 2.4) for t in rays)
            + f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{SUNC}" stroke="{SUN_EDGE}" stroke-width="{OW}"/>')


def wind():
    """Gusts after the hand-drawn original: long tapering strokes ending in spirals, plus plain streaks."""
    pale = "#D8E7F7"
    return (ribbon(spiral(spline([(372, 248), (412, 242), (444, 232)], 8), -1, 14, 1.35), 8, pale)
            + ribbon(spiral(spline([(312, 288), (396, 282), (466, 270), (496, 260)], 8), -1, 19, 1.4), 10, pale)
            + ribbon(spiral(spline([(346, 308), (376, 304), (400, 298)], 6), 1, 13, 1.3), 8, pale)
            + ribbon(spline([(300, 266), (350, 260), (392, 262)], 8), 5, pale)
            + ribbon(spline([(332, 324), (372, 320), (398, 322)], 8), 4, pale))


def fluxes():
    return (arrow(wavy((456, 400), (468, 352), 4, 16), FLUX_P, 4.5, both=True)
            + arrow(wavy((484, 408), (496, 358), 4, 16), FLUX_P, 4.5, both=True)
            + arrow(wavy((522, 420), (530, 322), 6, 24), FLUX_B, 6.0)
            + arrow(wavy((556, 440), (568, 330), 6, 24), FLUX_P, 6.0, both=True))


def iceberg():
    return (shape([(818, 590), (838, 572), (856, 552), (872, 572), (898, 588), (880, 598), (836, 600)], "#FFFFFF")
            + shape([(856, 552), (872, 572), (898, 588), (880, 598), (862, 580)], "#CFE5F3", INK, 1.6)
            + shape([(612, 688), (622, 679), (638, 680), (648, 687), (632, 692)], "#FFFFFF", INK, 2.0))


def ship(x=744, y=668):
    """Research vessel afloat on the sea surface; (x, y): waterline centre."""
    wake = line(spline([(x - 40, y + 4), (x - 30, y + 1), (x - 22, y + 3)], 4), "#9CCBF2", 2.2)
    hull = shape([(x - 28, y - 6), (x + 30, y - 12), (x + 24, y), (x - 22, y + 4)], "#D9412B")
    cabin = shape([(x - 14, y - 8), (x - 14, y - 20), (x + 6, y - 23), (x + 6, y - 11)], "#FFFFFF", INK, 1.8)
    funnel = shape([(x + 10, y - 12), (x + 10, y - 21), (x + 17, y - 22), (x + 17, y - 13)], SUNC, INK, 1.6)
    mast = line([(x - 4, y - 22), (x - 4, y - 34)], INK, 2.0)
    return wake + hull + cabin + funnel + mast


def ice():
    top = (f'<path d="{P(ICE_POLY, True)}" fill="url(#iceg)" stroke="{INK}" stroke-width="{OW}" '
           f'stroke-linejoin="round"/>')
    streaks = "".join(line(spline(s, 6), "#BFDDF0", 3.0, 0.9) for s in
                      ([(380, 520), (430, 540), (480, 580)], [(500, 540), (540, 570), (580, 620)],
                       [(600, 560), (650, 580), (700, 590)], [(250, 440), (300, 460), (340, 490)]))
    return cliff_face() + top + streaks + mesh()


def frame():
    return (f'<circle cx="{CX}" cy="{CY}" r="{(R_OUT + R_IN) / 2}" fill="none" stroke="#D6EAF5" '
            f'stroke-width="{R_OUT - R_IN}"/>'
            f'<circle cx="{CX}" cy="{CY}" r="{R_OUT}" fill="none" stroke="{INK}" stroke-width="9"/>'
            f'<circle cx="{CX}" cy="{CY}" r="{R_IN}" fill="none" stroke="{INK}" stroke-width="4"/>'
            f'<circle cx="{CX}" cy="{CY}" r="{R_SCENE}" fill="none" stroke="{INK}" stroke-width="6"/>')


defs = (f'<clipPath id="scene"><circle cx="{CX}" cy="{CY}" r="{R_SCENE}"/></clipPath>'
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#A8D7F2"/><stop offset="0.5" stop-color="#DDF0F8"/>'
        '<stop offset="0.75" stop-color="#F3F4E2"/></linearGradient>'
        f'<radialGradient id="glow" cx="{SUN[0]}" cy="{SUN[1]}" r="280" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#FFF4C2" stop-opacity="0.9"/><stop offset="1" stop-color="#FFF4C2" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="landg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#9FCB6B"/><stop offset="0.6" stop-color="#7DB35A"/>'
        '<stop offset="1" stop-color="#5F9846"/></linearGradient>'
        '<linearGradient id="rockg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#8A5E36"/><stop offset="1" stop-color="#5E3F24"/></linearGradient>'
        '<linearGradient id="iceg" x1="0" y1="0" x2="0.4" y2="1">'
        '<stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#DCEEF9"/></linearGradient>')

scene = (f'<rect x="{CX - R_OUT}" y="{CY - R_OUT}" width="{2 * R_OUT}" height="{2 * R_OUT}" fill="url(#sky)"/>'
         f'<rect x="{CX - R_OUT}" y="{CY - R_OUT}" width="{2 * R_OUT}" height="{2 * R_OUT}" fill="url(#glow)"/>'
         + sun() + cloud([(178, 248, 17), (202, 236, 23), (228, 246, 16)], 158, 248, 268, 28)
         + cloud([(694, 270, 22), (726, 250, 30), (768, 238, 36), (810, 252, 29), (842, 268, 20)], 672, 864, 300, 40)
         + wind() + mountains() + land() + ocean() + cavity() + layer_face() + ice() + circulation()
         + iceberg() + ship() + fluxes())

body = (f'<circle cx="{CX}" cy="{CY}" r="{R_OUT}" fill="#FFFFFF"/>'
        f'<g clip-path="url(#scene)">{scene}</g>' + frame())
x0, y0, s = CX - 500, CY - 500, 1000
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {y0:.0f} {s} {s}" width="{s}" height="{s}">\n'
       f'  <title>NICER: ice sheet - climate interactions (round)</title>\n  <defs>{defs}{"".join(GRADS)}</defs>\n  {body}\n</svg>\n')
(OUT / "nicer-illustration-round.svg").write_text(svg)
print(OUT / "nicer-illustration-round.svg")
