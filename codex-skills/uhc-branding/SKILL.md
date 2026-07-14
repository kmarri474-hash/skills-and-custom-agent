---
name: uhc-branding
description: Apply UnitedHealthcare brand guidance to frontend repositories, standalone HTML pages, PowerPoint decks, documents, dashboards, reports, and other content. Use when Codex is asked to brand, re-skin, audit, or align an app, index.html file, page, component library, design system, CSS theme, tokens, slide deck, handout, PDF/source document, or visual content with current UHC / UnitedHealthcare standards from brand.uhc.com and related UHC digital design guidance.
---

# UHC Branding

Use this skill to inspect frontend UI, standalone web pages, presentations, documents, reports, dashboards, and other content, then make the artifact follow current UnitedHealthcare brand standards as closely as the available sources and assets allow. Treat public guidance as a starting point and verify current standards from live sources when network access is available.

## Workflow

1. Identify the artifact type and editing surface: UI stack, standalone `index.html`, static site, PowerPoint deck, document, report, PDF/source file, dashboard, theme/template, token files, component library, icon set, image/logo assets, and the main routes/pages/slides/sections that demonstrate the experience.
2. For frontend repos, static sites, and folders containing HTML/CSS/JS assets, run the audit helper before editing:

   ```bash
   python3 /path/to/uhc-branding/scripts/audit_ui_brand.py /path/to/repo-or-folder
   ```

   Use the output to find hard-coded colors, font families, logo/image assets, theme files, and likely UI entry points. For PowerPoint, document, or PDF work, inspect the file theme, slide masters/layouts, styles, embedded assets, and source files with the normal document tooling available in the workspace.
3. Read `references/uhc-digital-brand.md` for source priority, current offline guidance, palette values, content-format checklists, and reporting expectations.
4. If internet access is available, check `https://brand.uhc.com` first. If access is limited, use user-provided Brand Center excerpts and the public Abyss UHC Brand pages linked in the reference file, and clearly state that Brand Center could not be fully inspected.
5. For brand assets, check the target artifact first. If it lacks an approved UHC mark and a U-mark alone is appropriate, use the bundled asset at `assets/UHC_U-mark_blu_RGB.png` only when that file is present; copy it into the artifact or repo using the normal asset workflow and keep the filename or add clear source notes. If the asset is absent, ask the user for an approved Brand Center asset or use an approved asset already present in the artifact.
6. Prefer existing abstractions before local patches: design tokens, theme providers, CSS variables, Tailwind config, Sass maps, component variants, document styles, PowerPoint masters, presentation themes, report templates, or shared layout primitives.
7. If the repo or artifact already uses Abyss or UHC tokens/components/templates, use those APIs/components/styles directly. Do not create parallel tokens or one-off styles that drift from the design system.
8. Apply brand changes in this order:
   - Typography: licensed fonts or fallbacks, heading/body hierarchy, readable scale, and line-height.
   - Color: blue/white proportion, supporting accents, neutral backgrounds, semantic colors, and accessible contrast.
   - Components and layouts: buttons, links, forms, cards, headers, navigation, slide masters, document styles, tables, charts, focus states, alerts, and data displays.
   - Brand assets: logo placement and clear space only when approved assets already exist in the artifact, the user provides them, Brand Center access provides them, or the bundled U-mark asset fits the use case.
   - Imagery/illustration/iconography: use existing approved assets or code-native UI icons; avoid inventing logos or brand marks.
9. Preserve behavior, meaning, and source content. Keep changes tightly scoped to styling, theming, layout polish, brand-safe formatting, and low-risk copy only when copy is visibly off-brand.
10. Verify with the artifact's normal checks. For UI or HTML, run the app/page and inspect desktop and mobile viewports when feasible. For PowerPoint/documents/reports, inspect representative pages/slides, exported previews, layout overflow, contrast, and asset rendering.
11. In the final answer, summarize what changed, what source guidance was used, and any standards that could not be verified because of authentication, missing licensed fonts, missing approved assets, or uninspected pages/slides.

## Guardrails

- Do not claim full UHC brand compliance unless Brand Center was accessible and the implemented artifact was checked against the relevant current pages.
- Do not download, recreate, trace, or approximate protected UHC logos. Use only assets already in the repo/artifact, assets the user provides/has authorized from Brand Center, or the bundled `assets/UHC_U-mark_blu_RGB.png` asset when a U-mark alone is appropriate.
- Do not recolor, stretch, compress, rotate, crop, add effects to, or otherwise modify approved UHC marks. Preserve aspect ratio, visible clear space, and accessible contrast against the surrounding surface.
- Do not bundle UHC fonts in a repo or document package unless the repo/artifact already has the licensed font files or the user provides them. Prefer CSS or document fallbacks and document the missing licensed-font dependency.
- Do not reduce accessibility while branding. Maintain WCAG AA contrast for text and meaningful UI elements; use more than color alone for status.
- Do not replace a mature local design system, document template, slide master, or reporting system with one-off styling. Map UHC decisions into the system already in use.
