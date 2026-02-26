#!/usr/bin/env python3
"""
Create true highlights from keyword start -> Debit column (text remains visible).  Each keyword is assigned a distinct colour.
Requires: PyMuPDF (fitz)

Run:
  pip install pymupdf
  python highlight_span_to_debit_yellow.py --input "STAT 1.pdf" --output Highlighted_Output.pdf
"""

import argparse, re
import fitz  # PyMuPDF

KEYWORDS = [
    "rent", "naveen v bhojg",
    "sai kiran", "udaya kum", "latha", "shankar t", "sundara",
    "swiggy", "zomato", "amazon pay", "zepto", "croma",
    "medical", "medicals", "pharma", "pharmacy", "hospital",
    "grocery", "groceries", "nandus", "bazar", "bazaar",
    "irctc", "makemytrip", "airtel", "recharge", "act", "broadband",
    "electricity", "water bill", "gas bill"
]
KEYWORDS = [k.lower() for k in KEYWORDS]

# ---------------------------------------------------------------------------
# highlight colors
# the script will cycle through a palette assigning a colour to each
# keyword the first time it is encountered.  this gives each term its own
# highlight colour instead of always yellow.
PALETTE = [
    (1.0, 1.0, 0.30),  # yellow (retro compatibility)
    (0.0, 1.0, 0.0),   # green
    (1.0, 0.0, 0.0),   # red
    (0.0, 0.0, 1.0),   # blue
    (1.0, 0.65, 0.0),  # orange
    (0.5, 0.0, 0.5),   # purple
    (0.0, 1.0, 1.0),   # cyan
]

import itertools

_color_cycle = itertools.cycle(PALETTE)
keyword_colors: dict[str, tuple[float, float, float]] = {}

AMOUNTS_TAIL = re.compile(r"\s([0-9,]+\.[0-9]{2})\s([0-9,]+\.[0-9]{2})\s([0-9,]+\.[0-9]{2})\s*$")

def highlight_span_on_page(page: fitz.Page):
    words = page.get_text("words")
    lines = {}
    for x0, y0, x1, y1, txt, b, ln, wn in words:
        lines.setdefault((b, ln), []).append((x0, y0, x1, y1, txt))

    for (b, ln), items in lines.items():
        items.sort(key=lambda w: (w[1], w[0]))
        line_text = " ".join([w[4] for w in items])
        lower_line = line_text.lower()

        if not any(k in lower_line for k in KEYWORDS):
            continue

        debit_x0 = None
        m = AMOUNTS_TAIL.search(line_text)
        if m:
            debit_val = m.group(1)
            tgt = debit_val.replace(",", "")
            for x0, y0, x1, y1, txt in items:
                if txt.replace(",", "") == tgt:
                    debit_x0 = x0
                    break
        if debit_x0 is None:
            debit_x0 = page.rect.width - 120

        for x0, y0, x1, y1, txt in items:
            t = txt.lower()
            # find matching keywords in this word
            matched = [k for k in KEYWORDS if k in t]
            if not matched:
                continue

            # choose a colour for the first matching keyword; any further
            # matches on the same word will share the same highlight.
            key = matched[0]
            color = keyword_colors.get(key)
            if color is None:
                color = next(_color_cycle)
                keyword_colors[key] = color

            x_start = x0
            span = []
            for sx0, sy0, sx1, sy1, stxt in items:
                if sx0 >= x_start and sx0 < debit_x0:
                    r = fitz.Rect(sx0, sy0, min(sx1, debit_x0), sy1)
                    span.append(fitz.Quad(r))
            if not span:
                continue
            ann = page.add_highlight_annot(span)
            ann.set_colors(stroke=color, fill=color)
            ann.set_opacity(0.35)
            ann.update()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    doc = fitz.open(args.input)
    for pno in range(doc.page_count):
        highlight_span_on_page(doc[pno])
    doc.save(args.output, deflate=True)
    doc.close()

if __name__ == "__main__":
    main()