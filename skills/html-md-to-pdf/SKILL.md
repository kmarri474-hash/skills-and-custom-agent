---
name: html-md-to-pdf
description: Convert an HTML page, a slide-deck HTML, or a Markdown file into a PDF on macOS. Use when the user wants a PDF from an HTML or Markdown file, or wants slides/reveal-style decks (where only one slide shows at a time) exported to PDF.
---

# HTML / Markdown → PDF

Every run is the same loop: **detect** tooling, **route** by source type, **convert**, **verify**. Never claim done before the verify step passes.

## Step 1 — Detect tooling

```bash
which pandoc weasyprint; ls "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
python3 -c "import fitz" 2>/dev/null || pip3 install pymupdf
```

Done when you know which of Chrome, pandoc, weasyprint exist. Chrome path on macOS:
`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.

## Step 2 — Route by source type

| Source | Converter |
| --- | --- |
| Slide-deck HTML (one slide visible at a time) | `scripts/html_to_pdf_slides.py` (Step 3) |
| Plain styled HTML page | `chrome --headless --print-to-pdf=out.pdf file://$PWD/page.html` |
| Markdown | `pandoc in.md -o out.pdf`; no pandoc → render MD to HTML then treat as HTML |

WeasyPrint (`weasyprint page.html out.pdf`) is a no-Chrome fallback for document-style (non-slide) content.

Done when the source is classified and a converter chosen.

## Step 3 — Convert a slide deck

Decks built with `.slide { display: none }` + `.slide.active { display: flex }` render only the first slide under a naive print. The script injects print CSS that turns every slide into its own page, then runs Chrome headless and writes `<name>.pdf` beside the source:

```bash
python3 scripts/html_to_pdf_slides.py docs/*.html
```

The injected CSS encodes the rules that keep every page clean:
- Force `.slide { display: flex !important }` inside `@media print`.
- Paginate with `page-break-before: always` (+ `:first-of-type { avoid }`). This avoids the trailing **blank page** that `page-break-after` leaves behind — nav/control elements sit after the slides in the DOM, so `:last-child` never matches them.
- Hide chrome: `.nav, .count, .nav-bar, .controls, .progress { display: none }`.
- Give `.slide` an explicit `1280x720` size with `@page { size: 1280px 720px; margin: 0 }` so nothing overflows or clips.

Done when a PDF exists for every source deck.

## Step 4 — Verify

```bash
python3 scripts/verify_pdf.py out.pdf          # page count + blank pages
python3 scripts/verify_pdf.py out.pdf --sheet  # + contact-sheet PNG in /tmp
```

Done when every PDF reports `blanks=none` and its page count equals the slide count. A trailing blank means Step 3's pagination rules were not applied — regenerate, do not ship. Inspect the contact sheet whenever styling fidelity matters.
