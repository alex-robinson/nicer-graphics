"""Generate the NICER logo SVGs: tile icon, wordmark, full logo and full logo with the project title,
each in colour and mono. Needs fontTools (title outlines).

Usage: python3 gen_logo.py OUTDIR
"""
import math, pathlib, sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

SKY, SEA, INK = "#60B3E5", "#1C5F96", "#111111"   # sky = tile blue of the 2007 NICE logo (NICE_logo_3.png)

# Wordmark C letter paths, cap height 100, (path, width)
L = {
    "N": ("M0,100V0H24L58,62V0H80V100H56L22,38V100Z", 80),
    "I": ("M0,0H22V100H0Z", 22),
    "C": ("M86.06,13.94A51,51 0 1 0 86.06,86.06L70.51,70.51A29,29 0 1 1 70.51,29.49Z", 102),
    "E": ("M0,0H64V20H22V40H58V60H22V80H64V100H0Z", 64),
    "R": ("M0,0H22V100H0Z M22,0H46A30,30 0 0 1 46,60H22V40H46A10,10 0 0 0 46,20H22Z M34,54H57L80,100H57Z", 80),
}
WM_X = {"N": 0, "I": 98, "C": 138, "E": 238, "R": 318}   # wordmark C spacing
GAP = 1.5  # half-width of the waterline gap
BOLD = 2.2  # stroke width added to the letters in their own colour: 10 % of the 22-unit stems


def logistic(lo, hi, xc, s):
    return lambda x: hi + (lo - hi) / (1 + math.exp((x - xc) / s))


def pts(f, x0, x1, dx=2.0, off=0.0):
    n = int(math.ceil((x1 - x0) / dx))
    return [(x0 + i * (x1 - x0) / n, f(x0 + i * (x1 - x0) / n) + off) for i in range(n + 1)]


def clip_above(f, x0, x1, ytop):
    p = pts(f, x0, x1, off=-GAP)
    s = f"M{x0},{ytop}H{x1}" + "".join(f"L{x:.2f},{y:.2f}" for x, y in reversed(p)) + "Z"
    return s


def clip_below(f, x0, x1, ybot):
    p = pts(f, x0, x1, off=GAP)
    return f"M{x0},{ybot}" + "".join(f"L{x:.2f},{y:.2f}" for x, y in p) + f"L{x1},{ybot}Z"


def letters(xmap, scale=1.0, dy=0.0):
    out = []
    for ch, x in xmap.items():
        d, _ = L[ch]
        out.append(f'<path transform="translate({x:.2f} {dy:.2f}) scale({scale})" d="{d}"/>')
    return "".join(out)


def bold(col):
    """Group attributes for letters filled and stroked in col, which thickens them by BOLD."""
    return f'fill="{col}" stroke="{col}" stroke-width="{BOLD}" stroke-linejoin="miter"'


def svg(vb, title, body, defs=""):
    x, y, w, h = vb
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" width="{w}" height="{h}">\n'
            f'  <title>{title}</title>\n  <defs>{defs}</defs>\n  {body}\n</svg>\n')


def write(name, s):
    (OUT / name).write_text(s)


# ---------------------------------------------------------------- concept 1
# Tile (pictogram C) + wordmark C; one waterline: flat through the tile and N, I; rises through C; high over E, R.
T = 100          # icon-only tile size
BT, BY = 128, -14  # lockup tile: larger than cap height so it reads as an icon, not an "O"
TX = 150         # letters start
X1 = {k: v + TX for k, v in WM_X.items()}
c_mid = X1["C"] + 51
f1 = logistic(66.0, 30.0, c_mid, 13.0)
W1 = X1["R"] + 80
DOME = "M12,66 C13,38 28,20 50,20 C72,20 87,38 88,66 Z"
TILE = f'<rect width="{T}" height="{T}" rx="22"/>'


def concept1(mono, with_tile=True):
    pre = ("c1m" if mono else "c1") + ("" if with_tile else "w")
    ytop, ybot = (BY - 6, BY + BT + 6) if with_tile else (-6, 106)
    defs = (f'<clipPath id="{pre}-a"><path d="{clip_above(f1, -6, W1 + 6, ytop)}"/></clipPath>'
            f'<clipPath id="{pre}-b"><path d="{clip_below(f1, -6, W1 + 6, ybot)}"/></clipPath>'
            f'<clipPath id="{pre}-t"><rect y="{BY}" width="{BT}" height="{BT}" rx="28"/></clipPath>')
    top, bot = (INK, INK) if mono else (SKY, SEA)
    tile = (f'<g clip-path="url(#{pre}-t)">'
            f'<g clip-path="url(#{pre}-a)"><rect y="{BY}" width="{BT}" height="{BT}" fill="{top}"/>'
            f'<path transform="translate(12 0)" d="{DOME}" fill="#FFFFFF"/></g>'
            f'<g clip-path="url(#{pre}-b)"><rect y="{BY}" width="{BT}" height="{BT}" fill="{bot}"/></g></g>')
    xmap = X1 if with_tile else {k: v - TX for k, v in X1.items()}
    body = ((tile if with_tile else "") +
            f'<g clip-path="url(#{pre}-a)" {bold(top)}>{letters(xmap)}</g>'
            f'<g clip-path="url(#{pre}-b)" {bold(bot)}>{letters(xmap)}</g>')
    if with_tile:
        vb = (-6, BY - 6, W1 + 12, BT + 12)
    else:
        vb = (-6, -6, W1 - TX + 12, 112)
    # clip functions are defined in lockup coordinates; shift for the wordmark-only file
    if not with_tile:
        body = f'<g transform="translate({-TX} 0)">' + body.replace(letters(xmap), letters(X1)) + '</g>'
        vb = (-6, -6, W1 - TX + 12, 112)
        body = body.replace(f'<g transform="translate({-TX} 0)">', f'<g transform="translate({-TX} 0)">')
    title = "NICER combined 1: one sea line from the ice-dome tile through the wordmark" if with_tile else "NICER wordmark C, revised waterline (no slivers)"
    return svg(vb, title + (" (mono)" if mono else ""), body, defs)


LAND = "#6B5847"   # bedrock (muted earth tone)
SUNC = "#F2B630"
ICEC = "#DDEFFB"   # pale ice blue, as the 2007 NICE tiles; keeps the tile edge visible on white
# Cross-section in the lockup tile (tile spans x 0..BT, y BY..BY+BT). One flat sea level (y = SL),
# the same level the waterline has through N and I. A marine ice sheet rests on a bed below sea level
# and goes afloat at the grounding line as an ice shelf. Large sun cut by the top-right tile corner.
SL = 66.0
X0, YTOP = -8.0, 12.0            # ice summit (just off the left tile edge)
XG, XF = 76.0, 106.0             # grounding line, shelf front
YS, YB_F = 60.0, 77.0            # shelf surface, shelf base at the front
SUN = (BT, BY, 50)               # cx, cy, r: centred on the tile corner


def bed_y(x):
    # retrograde bed inland (deeper towards the interior), shallow sill at the grounding line,
    # continental shelf dipping seaward
    if x <= XG:
        return 84.0 + 8.0 * ((XG - x) / (XG + 10)) ** 1.5
    return 84.0 + 12.0 * min(1.0, (x - XG) / 60.0) ** 0.8


def ice_path():
    sx = [X0 + i * (XG - X0) / 40 for i in range(41)]
    surf = [(x, YTOP + (YS - YTOP) * ((x - X0) / (XG - X0)) ** 2.2) for x in sx]
    base_shelf = [(XF, YB_F), (XG, bed_y(XG) + 0.5)]   # meets the bed contour exactly at the grounding line
    bed = [(x, bed_y(x) + 0.5) for x in reversed(sx)]
    pts_ = [(-12, YTOP)] + surf + [(XF, YS)] + base_shelf + bed + [(-12, bed_y(X0))]
    return "M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in pts_) + "Z"


def bed_path():
    xs = [-12 + i * (BT + 24) / 60 for i in range(61)]
    return "M" + "L".join(f"{x:.2f},{bed_y(x):.2f}" for x in xs) + f"L{BT + 12},{BY + BT + 12}L-12,{BY + BT + 12}Z"


def grounded_tile(pre, mono):
    """defs, body for the ice-sheet/shelf tile (lockup coordinates)."""
    top, bot = (INK, INK) if mono else (SKY, SEA)
    defs = (f'<clipPath id="{pre}-a"><path d="{clip_above(f1, -12, W1 + 6, BY - 6)}"/></clipPath>'
            f'<clipPath id="{pre}-b"><path d="{clip_below(f1, -12, W1 + 6, BY + BT + 6)}"/></clipPath>'
            f'<clipPath id="{pre}-t"><rect y="{BY}" width="{BT}" height="{BT}" rx="28"/></clipPath>')
    cx, cy, r = SUN
    bed = bed_path()
    if mono:
        land = (f'<path d="{bed}" fill="{INK}" stroke="#FFFFFF" stroke-width="5" stroke-linejoin="round"/>')
        sun = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF"/>'
    else:
        land = f'<path d="{bed}" fill="{LAND}"/>'
        sun = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{SUNC}"/>'
    if mono:   # sky and sea are both ink: the waterline gap marks sea level
        water = (f'<g clip-path="url(#{pre}-a)"><rect x="-12" y="{BY}" width="{BT + 24}" height="{BT}" fill="{top}"/>{sun}</g>'
                 f'<g clip-path="url(#{pre}-b)"><rect x="-12" y="{BY}" width="{BT + 24}" height="{BT}" fill="{bot}"/></g>')
    else:      # colour change alone marks sea level inside the tile; the gap starts at the tile edge
        water = (f'<rect x="-12" y="{BY}" width="{BT + 24}" height="{BT}" fill="{top}"/>{sun}'
                 f'<rect x="-12" y="{SL}" width="{BT + 24}" height="{BY + BT - SL}" fill="{bot}"/>')
    body = (f'<g clip-path="url(#{pre}-t)">' + water +
            f'{land}<path d="{ice_path()}" fill="{"#FFFFFF" if mono else ICEC}"/>'
            + (f'<rect y="{BY}" width="{BT}" height="{BT}" rx="28" fill="none" stroke="{INK}" stroke-width="6"/>' if mono else "")
            + '</g>')
    return defs, body


def concept1b(mono):
    pre = "c1m" if mono else "c1"
    defs, body = grounded_tile(pre, mono)
    la, lb = f"{pre}-a", f"{pre}-b"
    top, bot = (INK, INK) if mono else (SKY, SEA)
    body += (f'<g clip-path="url(#{la})" {bold(top)}>{letters(X1)}</g>'
             f'<g clip-path="url(#{lb})" {bold(bot)}>{letters(X1)}</g>')
    return svg((-6, BY - 6, W1 + 12, BT + 12), "NICER: ice sheet and shelf on a flat sea; waterline continues through the wordmark"
               + (" (mono)" if mono else ""), body, defs)


def icon1(mono):
    pre = "i1m" if mono else "i1"
    defs, body = grounded_tile(pre, mono)
    return svg((0, BY, BT, BT), "NICER icon: ice sheet and floating shelf, sun" + (" (mono)" if mono else ""), body, defs)


# ---------------------------------------------------------------- full logo with project title
# The title is set in TeX Gyre Heros Bold (GUST Font License, logo/fonts/), dark grey in colour, and converted to outlines, so the
# files render identically without the font installed. It spans the wordmark from N to R.
TITLE = "Next-generation Ice sheet-Climate Research"
FONT = pathlib.Path(__file__).parent / "fonts" / "texgyreheros-bold.otf"
TITLE_COL = "#3E454D"   # dark grey: lighter than the ink so the title stays secondary to NICER
TITLE_GAP = 12.0   # letters bottom (y = 100) to title cap top


def text_outline(text, x0, x1, cap_top):
    """SVG path of text in FONT, kerned, scaled uniformly to span x0..x1 with its cap height starting at cap_top."""
    f = TTFont(FONT)
    cmap, gs, hmtx = f.getBestCmap(), f.getGlyphSet(), f["hmtx"]
    kern = {}
    for lk in f["GPOS"].table.LookupList.Lookup:
        for st in (lk.SubTable if lk.LookupType == 2 else []):
            if st.Format == 1:
                for g1, ps in zip(st.Coverage.glyphs, st.PairSet):
                    for r in ps.PairValueRecord:
                        kern[g1, r.SecondGlyph] = getattr(r.Value1, "XAdvance", 0) or 0
    names = [cmap[ord(c)] for c in text]
    xs, x = [], 0.0
    for i, g in enumerate(names):
        xs.append(x)
        x += hmtx[g][0] + (kern.get((g, names[i + 1]), 0) if i + 1 < len(names) else 0)
    last = gs[names[-1]]
    bp = BoundsPen(gs); last.draw(bp)
    width = xs[-1] + bp.bounds[2]          # to the right ink edge of the last glyph
    s = (x1 - x0) / width
    base = cap_top + s * f["OS/2"].sCapHeight
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}")
    for g, gx in zip(names, xs):
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x0 + s * gx, base)))
    return pen.getCommands(), base + s * 220   # path, bottom incl. descenders


def concept1b_title(mono):
    pre = "c1tm" if mono else "c1t"
    defs, body = grounded_tile(pre, mono)
    top, bot = (INK, INK) if mono else (SKY, SEA)
    body += (f'<g clip-path="url(#{pre}-a)" {bold(top)}>{letters(X1)}</g>'
             f'<g clip-path="url(#{pre}-b)" {bold(bot)}>{letters(X1)}</g>')
    d, ybot = text_outline(TITLE, X1["N"] - BOLD / 2, W1 + BOLD / 2, 100 + BOLD / 2 + TITLE_GAP)
    body += f'<path d="{d}" fill="{INK if mono else TITLE_COL}"/>'
    h = max(BY + BT, ybot) + 6 - (BY - 6)
    return svg((-6, BY - 6, W1 + 12, round(h, 1)), f"NICER: {TITLE}" + (" (mono)" if mono else ""), body, defs)


write("nicer-logo-title.svg", concept1b_title(False))
write("nicer-logo-title-mono.svg", concept1b_title(True))
write("nicer-icon.svg", icon1(False))
write("nicer-icon-mono.svg", icon1(True))
write("nicer-wordmark.svg", concept1(False, with_tile=False))
write("nicer-wordmark-mono.svg", concept1(True, with_tile=False))
write("nicer-logo.svg", concept1b(False))
write("nicer-logo-mono.svg", concept1b(True))
print("ok")
