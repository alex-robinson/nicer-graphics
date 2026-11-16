"""Build index.html: the NICER logo at real sizes, then the illustration. Images are linked relatively.

Usage: python3 build_page.py REPODIR
"""
import html, pathlib, sys

root = pathlib.Path(sys.argv[1])

LOGOS = [  # label, colour file, mono file, note
    ("Full logo", "logo/nicer-logo.svg", "logo/nicer-logo-mono.svg",
     "Tile: marine ice sheet on a bed below sea level, floating ice shelf, flat sea, sun in the corner. "
     "Sky in the 2007 NICE tile blue (#60B3E5), sea #1C5F96. A thin waterline continues through N and I and rises through C."),
    ("Wordmark", "logo/nicer-wordmark.svg", "logo/nicer-wordmark-mono.svg", "Wordmark only, same colours and waterline."),
]
ICON, ICON_MONO = "logo/nicer-icon.svg", "logo/nicer-icon-mono.svg"

ILLUS = [
    ("Unlabelled (final)", "illustration/nicer-illustration.png",
     "Interactions between the ice sheet, atmosphere, ocean and solid Earth addressed in NICER. The grounding line "
     "(black dot) rests on a bed that deepens inland, so its retreat (dashed arrow) can become self-sustaining."),
    ("Labelled", "illustration/nicer-illustration-labels.png",
     "Same figure with the processes named, for slides and the website."),
]

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--fg:#1b1f24;--mut:#5b6470;--line:#dde1e6}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0f1318;--card:#171c22;--fg:#e6e9ed;--mut:#9aa4b0;--line:#2a313a}}
:root[data-theme="dark"]{--bg:#0f1318;--card:#171c22;--fg:#e6e9ed;--mut:#9aa4b0;--line:#2a313a}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,'Helvetica Neue',Arial,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:26px;margin:0 0 4px} h2{font-size:20px;margin:40px 0 12px;border-bottom:1px solid var(--line);padding-bottom:6px}
.mut{color:var(--mut)} a{color:inherit}
.row{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:10px 0}
.lab{font-weight:600;margin-bottom:8px}
.sw{display:flex;flex-wrap:wrap;gap:12px;align-items:center}
.tile{display:flex;flex-direction:column;align-items:center;gap:4px;font-size:11px;color:var(--mut)}
.bx{padding:10px;border-radius:6px;display:flex;align-items:center;justify-content:center;min-height:40px}
.light{background:#fff;border:1px solid #e3e6ea}.dark{background:#13202e}
.figs{display:flex;flex-wrap:wrap;gap:16px}
.fig{flex:1 1 320px;max-width:480px}.fig img{width:100%;height:auto;display:block}
.cap{font-size:13px;margin-top:8px;max-width:640px}
ul.files{columns:2;font-size:13px;padding-left:18px}
@media (max-width:600px){ul.files{columns:1}}
"""


def img(p, style):
    return f'<img src="{p}" style="{style}" alt="{html.escape(pathlib.Path(p).name)}">'


def tile(label, p, style, bg):
    return f"<div class='tile'><div class='bx {bg}'>{img(p, style)}</div>{label}</div>"


parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
         f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>NICER graphics</title>"
         f"<style>{CSS}</style></head><body><main>",
         "<h1>NICER graphics</h1><p class='mut'>Logo and illustration for the NICER doctoral network. "
         "Logos are shown at real size. Sources and build script: <code>build.sh</code>.</p>",
         "<h2>Logo</h2><p class='mut'>Homage to the 2007 NICE logo (melting ice tiles, sun): "
         "<a href='https://web.archive.org/web/2009/http://nice.ipsl.jussieu.fr/'>Wayback Machine snapshot</a>.</p>"]

for label, full, mono, note in LOGOS:
    t = [tile("240 px", full, "width:240px", "light"), tile("120 px", full, "width:120px", "light"),
         tile("on dark", full, "width:160px", "dark"), tile("mono", mono, "width:160px", "light")]
    if label == "Full logo":
        t += [tile("icon 64", ICON, "width:64px;height:64px", "light"), tile("icon 32", ICON, "width:32px;height:32px", "light"),
              tile("icon mono 32", ICON_MONO, "width:32px;height:32px", "light")]
    parts.append(f"<div class='row'><div class='lab'>{label}</div><div class='sw'>{''.join(t)}</div>"
                 f"<div class='cap mut'>{note}</div></div>")

pngs = sorted((root / "logo/png").glob("*.png"))
parts.append("<div class='row'><div class='lab'>Files</div><ul class='files'>"
             + "".join(f"<li><a href='logo/{p.name}'>logo/{p.name}</a></li>" for p in sorted((root / "logo").glob("*.svg")))
             + "".join(f"<li><a href='logo/png/{p.name}'>logo/png/{p.name}</a></li>" for p in pngs)
             + "</ul></div>")

parts.append("<h2>Illustration</h2><p class='mut'>Ice sheet, atmosphere, ocean and solid Earth interactions, in the "
             "logo's tile shape and palette. PNG 2008 px square (600 dpi at 85 mm); SVG sources alongside.</p>"
             "<div class='row'><div class='figs'>")
for label, p, cap in ILLUS:
    svg = p.replace(".png", ".svg")
    parts.append(f"<div class='fig'><div class='lab'>{label}</div>{img(p, '')}<div class='cap'>{cap}</div>"
                 f"<div class='cap mut'><a href='{p}'>PNG</a> · <a href='{svg}'>SVG</a></div></div>")
parts.append("</div></div></main></body></html>")

out = root / "index.html"
out.write_text("".join(parts))
print(out)
