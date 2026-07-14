#!/usr/bin/env python3
"""Read-only UI brand audit helper for the optum-branding Codex skill.

Scan frontend/static files for likely entry points, hard-coded colors, font
declarations, and brand/logo references before making visual edits.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path


TEXT_EXTENSIONS = {
    ".astro",
    ".css",
    ".html",
    ".js",
    ".jsx",
    ".md",
    ".mdx",
    ".scss",
    ".sass",
    ".svelte",
    ".ts",
    ".tsx",
    ".vue",
}

SKIP_DIRS = {
    ".git",
    ".next",
    ".turbo",
    ".vite",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
}

COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)")
FONT_RE = re.compile(r"font-family\s*:\s*([^;}\n]+)", re.IGNORECASE)
ASSET_RE = re.compile(
    r"[\w./@-]*(?:logo|brand|mark|optum|lifeprint|unitedhealth|uhg)[\w./@-]*\.(?:png|jpe?g|svg|webp|gif)",
    re.IGNORECASE,
)


def iter_files(root: Path):
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit UI files for brand-relevant styling.")
    parser.add_argument("path", type=Path, help="Repository or folder to scan")
    parser.add_argument("--limit", type=int, default=40, help="Maximum examples per section")
    args = parser.parse_args()

    root = args.path.expanduser().resolve()
    if not root.exists():
        parser.error(f"path does not exist: {root}")

    colors: Counter[str] = Counter()
    fonts: Counter[str] = Counter()
    assets: dict[str, set[str]] = defaultdict(set)
    entry_points: list[Path] = []
    scanned = 0

    for path in iter_files(root):
        scanned += 1
        rel = path.relative_to(root)
        if path.name in {"index.html", "App.tsx", "App.jsx", "main.tsx", "main.jsx"}:
            entry_points.append(rel)

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        colors.update(match.group(0) for match in COLOR_RE.finditer(text))
        fonts.update(match.group(1).strip().strip('"\'') for match in FONT_RE.finditer(text))
        for match in ASSET_RE.finditer(text):
            assets[match.group(0)].add(str(rel))

    print(f"root: {root}")
    print(f"files_scanned: {scanned}")

    print("\nlikely_entry_points:")
    for rel in sorted(entry_points)[: args.limit]:
        print(f"- {rel}")

    print("\nhard_coded_colors:")
    for value, count in colors.most_common(args.limit):
        print(f"- {value} ({count})")

    print("\nfont_families:")
    for value, count in fonts.most_common(args.limit):
        print(f"- {value} ({count})")

    print("\nbrand_or_logo_asset_references:")
    for asset, files in sorted(assets.items())[: args.limit]:
        locations = ", ".join(sorted(files)[:5])
        print(f"- {asset}: {locations}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
