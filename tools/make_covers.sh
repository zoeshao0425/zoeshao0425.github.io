#!/usr/bin/env bash
# Render the top of a paper's first page into a 3:2 cover thumbnail.
#
# The publication card shows covers in a 3:2 box, but a paper's first page is
# portrait, so we crop the top slice (title + authors + abstract + teaser
# figure) rather than letterboxing the whole page down to something unreadable.
#
# Usage: tools/make_covers.sh <input.pdf> <output.png>

set -euo pipefail

IN="$1"
OUT="$2"
DPI=150
WIDTH_PX=600 # final width; displayed at ~240px, so this is retina-safe

# Page geometry varies (letter vs. A4 vs. cropped preprints), so read the real
# MediaBox instead of assuming US letter.
box=$(gs -q -dNODISPLAY -dNOSAFER -dBATCH \
  -c "($IN) (r) file runpdfbegin 1 pdfgetpage /MediaBox get == quit" 2>/dev/null)

read -r x0 y0 x1 y1 <<<"$(echo "$box" | tr -d '[]' | xargs)"

page_w=$(echo "$x1 - $x0" | bc -l)
page_h=$(echo "$y1 - $y0" | bc -l)

# Height of the 3:2 slice we keep, in points.
crop_h=$(echo "$page_w * 2 / 3" | bc -l)
# Shift the page so the slice lands on the top of the page rather than the bottom.
offset_y=$(echo "$page_h - $crop_h" | bc -l)

dev_w=$(printf '%.0f' "$(echo "$page_w * $DPI / 72" | bc -l)")
dev_h=$(printf '%.0f' "$(echo "$crop_h * $DPI / 72" | bc -l)")

tmp=$(mktemp -t cover).png
gs -q -dNOPAUSE -dBATCH -sDEVICE=png16m \
  -sOutputFile="$tmp" \
  -r$DPI -dFirstPage=1 -dLastPage=1 \
  -g${dev_w}x${dev_h} -dFIXEDMEDIA \
  -c "<</PageOffset [0 $offset_y]>> setpagedevice" \
  -f "$IN"

sips -Z $WIDTH_PX "$tmp" --out "$OUT" >/dev/null
rm -f "$tmp"
echo "$OUT  ($(sips -g pixelWidth -g pixelHeight "$OUT" | tail -2 | tr -d ' \n'))"
