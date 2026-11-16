# nicer-graphics

Logo and illustration for the NICER doctoral network. Open `index.html` for an overview.

| Folder | Contents |
|---|---|
| `logo/` | `gen_logo.py`; SVGs (logo, logo with project title, wordmark, icon, each in colour and mono); `png/` exports; `fonts/` (TeX Gyre Heros for the title outlines, GUST Font License) |
| `illustration/` | `gen_illustration.py`; SVG and PNG, unlabelled and labelled; captions in `illustration/README.md` |

Regenerate everything (SVGs, PNGs, `index.html`):

```bash
bash build.sh
```

Requires `python3` with `fontTools` (title outlines) and macOS `sips` for the PNG export.
