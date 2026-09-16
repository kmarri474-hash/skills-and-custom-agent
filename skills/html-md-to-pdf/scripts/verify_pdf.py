#!/usr/bin/env python3
"""Verify a PDF: report page count and flag near-blank pages. Optionally write
a contact-sheet PNG for a quick visual scan.

Usage:
    python3 verify_pdf.py out.pdf [more.pdf ...] [--sheet]

Requires: pymupdf  (pip3 install pymupdf)
"""
import sys, glob, os
import fitz  # PyMuPDF


def is_blank(page) -> bool:
    pix = page.get_pixmap(matrix=fitz.Matrix(0.25, 0.25))
    data = pix.samples
    distinct = set(data[j:j + 3] for j in range(0, len(data), 300))
    return len(distinct) <= 2


def contact_sheet(doc, out_png, cols=3):
    pages = [p.get_pixmap(matrix=fitz.Matrix(0.5, 0.5)) for p in doc]
    w, h = pages[0].width, pages[0].height
    rows = (len(pages) + cols - 1) // cols
    sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, w * cols, h * rows), False)
    sheet.clear_with(255)
    for i, pg in enumerate(pages):
        r, c = divmod(i, cols)
        pg.set_origin(c * w, r * h)
        sheet.copy(pg, pg.irect)
    sheet.save(out_png)
    return out_png


def main(argv):
    make_sheet = "--sheet" in argv
    files = [a for a in argv if not a.startswith("--")]
    if not files:
        sys.exit("usage: verify_pdf.py out.pdf [...] [--sheet]")
    expanded = []
    for f in files:
        expanded.extend(sorted(glob.glob(f)) or [f])
    for f in expanded:
        doc = fitz.open(f)
        blanks = [i + 1 for i, p in enumerate(doc) if is_blank(p)]
        print(f"{f}: pages={len(doc)} blanks={blanks or 'none'}")
        if make_sheet:
            out = os.path.join("/tmp", os.path.basename(f)[:-4] + "_sheet.png")
            print(f"  contact sheet -> {contact_sheet(doc, out)}")


if __name__ == "__main__":
    main(sys.argv[1:])
