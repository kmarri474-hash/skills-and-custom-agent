#!/usr/bin/env python3
"""Convert slide-deck HTML (with .slide/.active show-one-at-a-time CSS) to a
multi-page PDF where every slide becomes its own landscape page.

Usage:
    python3 html_to_pdf_slides.py deck.html [more.html ...]

Writes <name>.pdf next to each source file.
"""
import subprocess, sys, tempfile, os, pathlib

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Injected only for printing. Forces every slide visible as its own page and
# hides on-screen navigation chrome. page-break-BEFORE avoids the trailing
# blank page that page-break-after produces when nav elements follow slides.
PRINT_CSS = """
<style id="__pdf_print_css__">
@media print {
  html, body { overflow: visible !important; height: auto !important; width: auto !important; background: #0a1628 !important; }
  .nav-bar, .nav, .controls, .progress, .progress-bar, .count { display: none !important; }
  .slide {
    display: flex !important;
    flex-direction: column !important;
    width: 1280px !important;
    height: 720px !important;
    page-break-before: always;
    break-before: page;
    page-break-after: avoid;
    break-after: avoid;
    overflow: hidden !important;
  }
  .slide:first-of-type { page-break-before: avoid; break-before: avoid; }
}
@page { size: 1280px 720px; margin: 0; }
</style>
"""


def convert(src: pathlib.Path):
    html = src.read_text(encoding="utf-8")
    if "</head>" in html:
        html = html.replace("</head>", PRINT_CSS + "</head>", 1)
    else:
        html = PRINT_CSS + html
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                     dir=str(src.parent), encoding="utf-8") as tf:
        tf.write(html)
        tmp = tf.name
    out = src.with_suffix(".pdf")
    try:
        subprocess.run([CHROME, "--headless", "--disable-gpu",
                        "--no-pdf-header-footer",
                        f"--print-to-pdf={out}",
                        f"file://{tmp}"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        os.unlink(tmp)
    print(f"{src.name} -> {out.name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: html_to_pdf_slides.py file.html [...]")
    for arg in sys.argv[1:]:
        convert(pathlib.Path(arg))
