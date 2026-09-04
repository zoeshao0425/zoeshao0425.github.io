#!/usr/bin/env python3
"""Extract a paper's Figure 1 from its PDF and render it as a publication cover.

The theme shows covers in a 3:2 box, so the figure is scaled to fit and centred on
a white 600x400 canvas rather than cropped -- these are teaser figures and cutting
them changes what they say.

Finding the figure is done by locating the "Figure 1:" caption text, then treating
the region directly above it as the figure:

  * the caption's horizontal extent gives the column band (in a two-column paper a
    full-width figure has a full-width caption, so this distinguishes the two cases)
  * the nearest text block above the caption, within that band, gives a ceiling
  * vector drawings and placed images between that ceiling and the caption give the
    figure's true bounding box

Usage:
    tools/extract_figure1.py <input.pdf> <output.png> [--page N] [--top Y] [--debug]

    --page  0-indexed page to search, if auto-detection picks the wrong "Figure 1"
    --top   override the ceiling in PDF points, when a caption or stray rule confuses
            the automatic boundary
    --debug print the detected geometry instead of guessing why it looks wrong

Requires PyMuPDF (pip install pymupdf).
"""

import argparse
import re
import sys

import fitz

CAPTION_RE = re.compile(r"^\s*(?:Figure|Fig\.?)\s*1\s*[:.]", re.IGNORECASE)

OUT_W, OUT_H = 600, 400  # 3:2, matching the theme's cover box
MARGIN = 4               # breathing room around the figure, in output px


def block_text(block):
    return "".join(s["text"] for line in block["lines"] for s in line["spans"])


def find_caption(doc, forced_page=None):
    """Return (page_number, caption_bbox) for the Figure 1 caption."""
    pages = [forced_page] if forced_page is not None else range(len(doc))
    for pno in pages:
        for block in doc[pno].get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            if CAPTION_RE.match(block_text(block)):
                return pno, fitz.Rect(block["bbox"])
    return None, None


HEADER_FRAC = 0.08   # top slice of the page where a running head lives
RULE_FRAC = 0.09     # ...and the hairline rule under it


def _header_floor(page):
    """Lowest edge of the running head, so the figure never absorbs it.

    On an inner page a journal template repeats the paper title (or author list)
    plus a rule at the very top. That sits directly above a top-of-page figure with
    no whitespace between them, so distance alone cannot separate the two.
    """
    floor = page.rect.y0
    head_zone = page.rect.y0 + HEADER_FRAC * page.rect.height
    rule_zone = page.rect.y0 + RULE_FRAC * page.rect.height

    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        r = fitz.Rect(block["bbox"])
        if r.y1 < head_zone and r.width > 0.35 * page.rect.width:
            floor = max(floor, r.y1 + 2)
    for d in page.get_drawings():
        r = fitz.Rect(d["rect"])
        if r.y1 < rule_zone and r.height < 1.5 and r.width > 0.5 * page.rect.width:
            floor = max(floor, r.y1 + 2)
    return floor


def _band_items(page, caption, band_x0, band_x1, floor):
    """Every drawing, image and text block between `floor` and the caption."""
    def in_band(r):
        overlap = min(r.x1, band_x1) - max(r.x0, band_x0)
        return overlap > 0.35 * min(r.width, band_x1 - band_x0)

    def usable(r):
        return r.y1 <= caption.y0 + 1 and r.y1 > floor and in_band(r)

    items = []
    for d in page.get_drawings():
        r = fitz.Rect(d["rect"])
        if r.width >= 1 and r.height >= 1 and usable(r):
            items.append((r, False))
    for info in page.get_images(full=True):
        for r in page.get_image_rects(info[0]):
            if usable(r):
                items.append((r, False))
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        r = fitz.Rect(block["bbox"])
        if usable(r):
            # Running prose above the figure: many lines filling the column width.
            # Labels *inside* a figure are short and narrow, so they do not match.
            prose = len(block["lines"]) >= 3 and r.width > 0.8 * (band_x1 - band_x0)
            items.append((r, prose))
    return items


def figure_rect(page, caption, forced_top=None, gap=22.0):
    """Bounding box of the artwork above `caption`.

    Grows a cluster upward from the caption: an element joins the figure while it
    starts within `gap` points of what has been claimed so far. Papers leave much
    more whitespace between a figure and the preceding paragraph than between the
    figure's own parts, so the first big gap is the figure's top edge. Running
    prose is a hard stop regardless of distance, and the running head is excluded
    outright since no gap separates it from a top-of-page figure.
    """
    band_x0, band_x1 = caption.x0, caption.x1
    slack = 0.04 * (band_x1 - band_x0)
    band_x0 -= slack
    band_x1 += slack

    floor = _header_floor(page) if forced_top is None else forced_top
    items = _band_items(page, caption, band_x0, band_x1, floor)
    if not items:
        return fitz.Rect(band_x0, floor, band_x1, caption.y0)

    items.sort(key=lambda t: -t[0].y1)
    rect = None
    for r, is_prose in items:
        if rect is None:
            if is_prose:
                continue  # never seed the cluster on a paragraph
            rect = fitz.Rect(r)
            continue
        if r.y1 < rect.y0 - gap:
            break                       # whitespace: we have reached the figure's top
        if is_prose and r.y1 <= rect.y0 + 1:
            break                       # a paragraph, not part of the figure
        rect |= r

    if rect is None:
        return fitz.Rect(band_x0, floor, band_x1, caption.y0)

    # An element may stick out past the column; the figure itself does not.
    rect.x0 = max(rect.x0, band_x0)
    rect.x1 = min(rect.x1, band_x1)
    rect.y0 = max(rect.y0, floor)
    rect.y1 = min(rect.y1, caption.y0)
    return rect


def render(src, pno, clip, out_path):
    """Scale `clip` to fit a white 600x400 canvas, preserving aspect."""
    out = fitz.open()
    page = out.new_page(width=OUT_W, height=OUT_H)

    avail_w, avail_h = OUT_W - 2 * MARGIN, OUT_H - 2 * MARGIN
    scale = min(avail_w / clip.width, avail_h / clip.height)
    w, h = clip.width * scale, clip.height * scale
    x, y = (OUT_W - w) / 2, (OUT_H - h) / 2

    page.show_pdf_page(fitz.Rect(x, y, x + w, y + h), src, pno, clip=clip)
    # Render at 2x for retina, then the file is still only a few tens of KB.
    page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(out_path)
    out.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("out")
    ap.add_argument("--page", type=int, default=None)
    ap.add_argument("--top", type=float, default=None)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    doc = fitz.open(args.pdf)
    pno, caption = find_caption(doc, args.page)
    if caption is None:
        sys.exit("no 'Figure 1' caption found in %s" % args.pdf)

    page = doc[pno]
    rect = figure_rect(page, caption, args.top)

    if args.debug:
        print("page      %d" % pno)
        print("caption   %s" % [round(v) for v in caption])
        print("figure    %s  (%.0f x %.0f, aspect %.2f)"
              % ([round(v) for v in rect], rect.width, rect.height,
                 rect.width / rect.height if rect.height else 0))

    if rect.height < 10 or rect.width < 10:
        sys.exit("figure region for %s looks degenerate: %s" % (args.pdf, rect))

    render(doc, pno, rect, args.out)
    print("%s  page %d  figure %.0fx%.0f -> %s"
          % (args.pdf, pno, rect.width, rect.height, args.out))
    doc.close()


if __name__ == "__main__":
    main()
