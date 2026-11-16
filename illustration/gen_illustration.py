"""NICER illustration: ice sheet - atmosphere - ocean interactions, in the visual language of the logo.

Same rounded tile (corner ratio 28/128), palette, corner sun, marine ice sheet on a retrograde bed
and floating shelf as the logo icon, with the processes NICER studies added.

Usage: python3 gen_illustration.py OUTDIR [text|none]
  text: short labels in the figure;  none: no labels (illustration only).
"""
import math, pathlib, sys

OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
MODE = sys.argv[2] if len(sys.argv) > 2 else "text"

W = 600
RX = W * 28 / 128                     # logo tile corner ratio
SKY, SEA, INK = "#60B3E5", "#1C5F96", "#111111"
SEA_DEEP = "#174F80"
LAND, SUNC, ICEC = "#6B5847", "#F2B630", "#DDEFFB"
WARM = "#F0703F"                      # ocean heat, longwave, geothermal heat
PLUME = "#BDE6FF"
LAYER = "#B4D2EC"                     # isochrones
FLOW = "#5E93C4"
EARTH = "#E9DCCB"                     # light marks on bedrock
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
FS = 15
LH = 17                               # line spacing of two-line labels
LW = 3.2                              # standard process line width

SL = 330.0
X0, YTOP = -40.0, 110.0               # ice summit (off the left edge)
XG, XF = 260.0, 390.0                 # grounding line, shelf front
YS, YF, YBF = 308.0, 314.0, 380.0     # surface at GL, surface at front, base at front
SUN_R = 140


def bed(x):
    if x <= XG:                       # retrograde: deepens inland
        return 440 + 50 * ((XG - x) / (XG - X0)) ** 1.5
    if x <= XG + 150:                 # sill at the grounding line, deepening seaward
        return 440 + 60 * ((x - XG) / 150) ** 0.6
    t = min(1.0, (x - XG - 150) / 120)  # shelf break
    return 500 + 90 * (3 * t * t - 2 * t ** 3)


def surf(x):
    if x <= XG:
        s = max(0.0, (x - X0) / (XG - X0))
        return YTOP + (YS - YTOP) * s ** 2.2
    return YS + (YF - YS) * (x - XG) / (XF - XG)


def base(x):
    if x <= XG:
        return bed(x)
    return bed(XG) + (YBF - bed(XG)) * (x - XG) / (XF - XG)


def depth(x, f):
    """Point a fraction f of the ice thickness below the surface."""
    return surf(x) + f * (base(x) - surf(x))


def rng(a, b, n):
    return [a + i * (b - a) / n for i in range(n + 1)]


def P(pts):
    return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def smooth(pts, k=6):
    return [(pts[i][0], sum(p[1] for p in pts[max(0, i - k):i + k + 1]) / len(pts[max(0, i - k):i + k + 1]))
            for i in range(len(pts))]


def bez(p0, c1, c2, p1, n=40):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3 * p0[0] + 3 * u*u*t * c1[0] + 3 * u*t*t * c2[0] + t**3 * p1[0],
                    u**3 * p0[1] + 3 * u*u*t * c1[1] + 3 * u*t*t * c2[1] + t**3 * p1[1]))
    return out


def head(tip, b, color, hw):
    dx, dy = tip[0] - b[0], tip[1] - b[1]; L = math.hypot(dx, dy)
    nx, ny = -dy / L * hw / 2, dx / L * hw / 2
    return f'<path d="{P([tip, (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny)])}Z" fill="{color}"/>'


def trim(pts, hl):
    """Cut length hl off the end of a polyline; return (shortened polyline, cut point)."""
    acc, i = 0.0, len(pts) - 1
    while i > 0:
        seg = math.dist(pts[i], pts[i - 1])
        if acc + seg >= hl:
            f = (hl - acc) / seg
            b = (pts[i][0] + f * (pts[i - 1][0] - pts[i][0]), pts[i][1] + f * (pts[i - 1][1] - pts[i][1]))
            return pts[:i] + [b], b
        acc += seg; i -= 1
    return [pts[0]], pts[0]


def line(pts, color, w=LW, dash=None, op=1.0):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="{P(pts)}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" '
            f'stroke-linejoin="round" opacity="{op}"{da}/>')


def arrow(pts, color, w=LW, dash=None, both=False, op=1.0):
    """Polyline with a triangular head at its end (and start if both); the line stops at the heads."""
    hl, hw = 3.6 * w, 3.0 * w
    body, b = trim(pts, hl)
    out = head(pts[-1], b, color, hw)
    if both:
        rev, b0 = trim(body[::-1], hl)
        body = rev[::-1]
        out += head(pts[0], b0, color, hw)
    return f'<g opacity="{op}">' + line(body, color, w, dash) + out + '</g>'


def wavy(p0, p1, amp=5.0, lam=16.0, straight=14.0):
    L = math.dist(p0, p1); ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    pts = []
    for s in rng(0, L, int(L / 1.5)):
        a = amp * math.sin(2 * math.pi * s / lam) * min(1.0, max(0.0, (L - straight - s) / 6))
        pts.append((p0[0] + ux * s - uy * a, p0[1] + uy * s + ux * a))
    return pts


def curl(pts, sign=1, R=11.0, turn=1.7 * math.pi):
    """Continue a polyline into a tightening spiral (wind-gust glyph)."""
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    th = math.atan2(y1 - y0, x1 - x0); x, y = x1, y1; out = list(pts); done, ds = 0.0, 1.0
    while done < turn:
        k = 1.0 / (R * (1 - 0.55 * done / turn))
        th += sign * k * ds; done += k * ds
        x += math.cos(th) * ds; y += math.sin(th) * ds
        out.append((x, y))
    return out


def spring(x, y0, y1, n=6, amp=9.0, lead=7.0):
    pts = [(x, y0), (x, y0 + lead)]
    h = (y1 - y0 - 2 * lead) / n
    for i in range(n):
        pts += [(x + amp, y0 + lead + (i + 0.25) * h), (x - amp, y0 + lead + (i + 0.75) * h)]
    pts += [(x, y1 - lead), (x, y1)]
    return pts


def cloud(cx, cy, k=1.0):
    puffs = [(-38, 8, 20), (-14, -6, 27), (17, -2, 24), (38, 10, 17)]
    c = "".join(f'<circle cx="{cx + k*dx:.1f}" cy="{cy + k*dy:.1f}" r="{k*r:.1f}"/>' for dx, dy, r in puffs)
    return (f'<g fill="#FFFFFF">{c}<rect x="{cx - 52*k:.1f}" y="{cy + 4*k:.1f}" width="{104*k:.1f}" '
            f'height="{24*k:.1f}" rx="{12*k:.1f}"/></g>')


# ------------------------------------------------------------------ geometry
ice = ([(-60, YTOP)] + [(x, surf(x)) for x in rng(X0, XG, 60)] + [(XF, YF), (XF, YBF)]
       + [(x, base(x)) for x in rng(XF, XG, 10)] + [(x, bed(x) + 0.5) for x in rng(XG, -60, 60)])
ICE = P(ice) + "Z"
BED = P([(x, bed(x)) for x in rng(-60, W + 60, 120)] + [(W + 60, W + 60), (-60, W + 60)]) + "Z"

layers = "".join(line(smooth([(x, depth(x, f)) for x in rng(-60, XF - 3, 90)]), LAYER, 2.2)
                 for f in (0.32, 0.55, 0.76))

# ------------------------------------------------------------------ processes
el = {}
# solar radiation: towards the ice and the ocean, plus a reflected ray from the bright ice
XUP = 286                             # reflected solar and longwave rise side by side from the shelf
el["solar"] = (arrow(wavy((468, 98), (372, 160)), SUNC, 3.6) + arrow(wavy((556, 154), (540, 246)), SUNC, 3.6)
               + arrow(wavy((XUP, surf(XUP) - 6), (XUP, surf(XUP) - 72)), SUNC))
# longwave emission from the shelf
el["lw"] = arrow(wavy((XUP + 22, surf(XUP + 22) - 6), (XUP + 22, surf(XUP + 22) - 72)), WARM)
# moisture transport aloft: wind gusts towards the ice sheet
el["wind"] = (line(curl(bez((430, 36), (370, 26), (290, 32), (214, 52))[:-1], sign=-1), "#FFFFFF")
              + line(curl(bez((410, 66), (360, 58), (300, 62), (236, 80))[:-1], sign=-1), "#FFFFFF", op=0.85))
# snowfall
snow = "".join(f'<circle cx="{x + (7 if j % 2 else 0):.1f}" cy="{y:.1f}" r="2.6"/>'
               for j, y in enumerate(rng(106, 150, 4)) for x in rng(72, 156, 7) if y < surf(x + 7) - 7)
el["snow"] = cloud(118, 72) + f'<g fill="#FFFFFF">{snow}</g>'
# katabatic wind down the slope (gust glyph curling at its downstream end)
el["kat"] = line(curl([(x, surf(x) - 13) for x in rng(182, 240, 20)], sign=-1, R=9), "#FFFFFF")
# surface melt ponds on the shelf
el["melt"] = "".join(f'<ellipse cx="{x}" cy="{surf(x) + 1:.1f}" rx="{rx}" ry="3" fill="#3E9AD6"/>'
                     for x, rx in ((334, 9), (358, 8), (378, 8)))
# ice flow: just below the surface, clear of the layers
el["flow"] = arrow(smooth([(x, depth(x, 0.15)) for x in rng(20, XF - 14, 80)], 3), FLOW, 3.4)
el["layers"] = layers
# basal sliding
el["slide"] = "".join(arrow([(x, bed(x) - 11), (x + 34, bed(x + 34) - 11)], "#3B3B3B", 2.6) for x in (110, 170))
# geothermal heat flux (same glyph as the surface fluxes)
el["ghf"] = arrow(wavy((152, 570), (152, 504)), WARM)
# solid-Earth response (uplift / subsidence)
el["gia"] = line(spring(182, 506, 570), EARTH, 2.8)
# grounding line and its retreat down the retrograde bed
el["gl"] = (arrow([(x, bed(x) + 14) for x in rng(XG - 12, XG - 80, 12)], EARTH, 2.6, dash="7 5"))
# warm ocean water: from the shelf break into the cavity, along the bed
el["warm"] = arrow(smooth([(x, bed(x) - 11) for x in rng(418, 290, 40)], 3), WARM, 4.0)
# meltwater plume along the shelf base towards the front
el["plume"] = arrow([(x, base(x) + 8) for x in rng(276, 382, 10)], PLUME, 3.2)
# calving
el["calve"] = f'<path d="M506,331 L510,321 L528,319 L536,331 L534,360 L510,363 Z" fill="{ICEC}"/>'

ORDER = ["layers", "flow", "slide", "gl", "ghf", "gia", "melt", "calve", "solar", "lw", "wind", "snow", "kat"]

# label: text, x, y, anchor, colour (rotation in degrees optional)
xk = 206; ang = math.degrees(math.atan2(surf(xk + 5) - surf(xk - 5), 10))
LAB = [
    ("solar radiation", 452, 214, "middle", INK),
    ("surface\nradiation", XUP + 34, 244, "start", INK),
    ("moisture transport", 320, 22, "middle", INK),
    ("snowfall", 118, 79, "middle", "#5B7C99"),
    ("katabatic wind", xk, surf(xk) - 34, "middle", INK, ang),
    ("surface melt", 324, 298, "start", INK),
    ("ice flow", 84, depth(84, 0.15) + 24, "middle", "#3C6E9E"),
    ("internal layers", 92, (depth(92, 0.55) + depth(92, 0.76)) / 2 + 5, "middle", "#6F95B8"),
    ("basal sliding", 150, bed(150) - 26, "middle", "#3B3B3B"),
    ("geothermal\nheat", 138, 534, "end", "#F3E6D6"),
    ("solid Earth", 200, 542, "start", "#F3E6D6"),
    ("grounding line", 236, 480, "middle", "#F3E6D6"),
    ("warm ocean water", 430, 490, "start", "#FFFFFF"),
    ("basal melt", 372, 419, "start", "#FFFFFF"),
    ("calving", 521, 384, "middle", "#FFFFFF"),
]


def labels():
    if MODE != "text":
        return ""
    out = []
    for t, x, y, a, c, *rot in LAB:
        tr = f' transform="rotate({rot[0]:.1f} {x:.1f} {y:.1f})"' if rot else ""
        for i, s in enumerate(t.split("\n")):  # one <text> per line: sips ignores tspan dy
            out.append(f'<text x="{x:.1f}" y="{y + i * LH:.1f}"{tr} text-anchor="{a}" font-family="{FONT}" '
                       f'font-size="{FS}" font-weight="500" fill="{c}">{s}</text>')
    return "".join(out)


body = (f'<g clip-path="url(#tile)">'
        f'<rect width="{W}" height="{W}" fill="{SKY}"/>'
        f'<circle cx="{W}" cy="0" r="{SUN_R}" fill="{SUNC}"/>'
        f'<rect y="{SL}" width="{W}" height="{W - SL}" fill="{SEA}"/>'
        f'<rect y="430" width="{W}" height="{W - 430}" fill="{SEA_DEEP}"/>'
        + el["warm"] + el["plume"] +
        f'<path d="{BED}" fill="{LAND}"/>'
        f'<path d="{ICE}" fill="{ICEC}"/>'
        + "".join(el[k] for k in ORDER) + labels() + '</g>')
defs = f'<clipPath id="tile"><rect width="{W}" height="{W}" rx="{RX:.1f}"/></clipPath>'
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W}" width="{W}" height="{W}">\n'
       f'  <title>NICER: ice sheet - climate interactions</title>\n  <defs>{defs}</defs>\n  {body}\n</svg>\n')
name = "nicer-illustration" + ("-labels" if MODE == "text" else "") + ".svg"
(OUT / name).write_text(svg)
print(OUT / name)
