#!/bin/bash
# Regenerate all NICER graphics: SVGs, PNGs and the overview page (index.html).
# Needs python3 (standard library only) and macOS sips for rasterizing.
# Usage: bash build.sh   (run from anywhere)
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"; TMP="$(mktemp -d)"; trap 'rm -r "$TMP"' EXIT

python3 "$D/logo/gen_logo.py" "$D/logo"
python3 "$D/illustration/gen_illustration.py" "$D/illustration" none
python3 "$D/illustration/gen_illustration.py" "$D/illustration" text

render() {  # svg, width_px, out.png  (rewrites the declared size so sips renders at that width)
  local svg=$1 w=$2 out=$3
  read vw vh < <(sed -nE '1s/.*viewBox="[-0-9.]+ [-0-9.]+ ([0-9.]+) ([0-9.]+)".*/\1 \2/p' "$svg")
  local h; h=$(python3 -c "print(round($w*$vh/$vw))")
  sed -E "1s/width=\"[0-9.]+\" height=\"[0-9.]+\"/width=\"$w\" height=\"$h\"/" "$svg" > "$TMP/t.svg"
  sips -s format png "$TMP/t.svg" --out "$out" >/dev/null
  echo "$(basename "$out")  ${w}x${h}"
}

L="$D/logo"; mkdir -p "$L/png"
for w in 32 64 180 512 1024; do render "$L/nicer-icon.svg" $w "$L/png/nicer-icon-$w.png"; done
render "$L/nicer-icon-mono.svg" 1024 "$L/png/nicer-icon-mono-1024.png"
for w in 600 1200 3000; do render "$L/nicer-logo.svg" $w "$L/png/nicer-logo-$w.png"; done
render "$L/nicer-logo-mono.svg" 3000 "$L/png/nicer-logo-mono-3000.png"
for w in 1200 3000; do render "$L/nicer-wordmark.svg" $w "$L/png/nicer-wordmark-$w.png"; done

I="$D/illustration"   # 2008 px = 600 dpi at 85 mm print width
render "$I/nicer-illustration.svg" 2008 "$I/nicer-illustration.png"
render "$I/nicer-illustration-labels.svg" 2008 "$I/nicer-illustration-labels.png"

python3 "$D/build_page.py" "$D"
