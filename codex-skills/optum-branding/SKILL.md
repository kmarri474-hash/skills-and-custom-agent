---
name: optum-branding
description: Apply Optum brand guidance to frontend repositories, standalone HTML pages, PowerPoint decks, Word documents, Excel workbooks, dashboards, reports, PDFs/source documents, and other visual content. Use when Codex is asked to brand, re-skin, audit, polish, or align an app, index.html file, page, component library, design system, CSS theme, tokens, slide deck, handout, spreadsheet, report, or document with current Optum standards from brand.optum.com and related approved Optum guidance.
---

# Optum Branding

Use this skill to inspect frontend UI, standalone web pages, presentations, documents, spreadsheets, reports, dashboards, and other visual artifacts, then make the artifact follow Optum brand guidance as closely as approved sources and assets allow. Treat public guidance as a starting point and verify current standards from live Optum Brand Center sources whenever network access and authentication allow.

## Workflow

1. Identify the artifact type and editing surface: UI stack, standalone `index.html`, static site, PowerPoint deck, Word document, Excel workbook, PDF/source file, dashboard, report, theme/template, token files, component library, icon set, image/logo assets, and the main routes/pages/slides/sheets/sections that demonstrate the experience.
2. For frontend repos, static sites, and folders containing HTML/CSS/JS assets, run the audit helper before editing:

   ```bash
   python3 /path/to/optum-branding/scripts/audit_ui_brand.py /path/to/repo-or-folder
   ```

   Use the output to find hard-coded colors, font families, logo/image assets, theme files, and likely UI entry points. For PowerPoint, Word, Excel, report, or PDF work, inspect themes, masters/layouts, styles, embedded assets, charts, tables, source files, and representative pages/sheets/slides with the normal document tooling available in the workspace.
3. Read `references/optum-digital-brand.md` for source priority, public-site observations, palette cautions, content-format checklists, and reporting expectations.
4. If internet access is available, check `https://brand.optum.com/content/brand-overview` first. If the site shell loads but detailed content or assets require authentication, use user-provided Brand Center excerpts/assets and approved assets already present in the artifact, and clearly state that full Brand Center guidance could not be inspected.
5. For brand assets, check the target artifact first. Use Optum logo marks, Lifeprint imagery, fonts, templates, iconography, and other protected brand assets only when they already exist in the artifact/repo, the user provides them, or Brand Center access provides them. Do not recreate or approximate protected assets.
6. Prefer existing abstractions before local patches: design tokens, theme providers, CSS variables, Tailwind config, Sass maps, component variants, document styles, PowerPoint masters, presentation themes, workbook themes, report templates, or shared layout primitives.
7. If the repo or artifact already uses approved Optum/UHG components, tokens, templates, or a mature local design system, map Optum decisions into those APIs/styles directly. Do not create parallel tokens or one-off styles that drift from the system.
8. Apply brand changes in this order:
   - Typography: approved fonts when available, fallback stacks when not, heading/body hierarchy, readable scale, and line-height.
   - Color: Optum orange-led brand moments, disciplined neutrals, accessible contrast, semantic colors, and restrained accent use.
   - Components and layouts: buttons, links, forms, cards, headers, navigation, slide masters, document styles, spreadsheet tables/charts, focus states, alerts, and data displays.
   - Brand assets: logo placement, clear space, and sizing only when approved assets are available.
   - Imagery/illustration/iconography: use existing approved assets or code-native UI icons; avoid inventing logos, Lifeprint graphics, or brand marks.
9. Preserve behavior, meaning, formulas, data integrity, and source content. Keep changes tightly scoped to styling, theming, layout polish, brand-safe formatting, and low-risk copy only when copy is visibly off-brand.
10. Verify with the artifact's normal checks. For UI or HTML, run the app/page and inspect desktop and mobile viewports when feasible. For PowerPoint, Word, Excel, reports, and PDFs, inspect representative pages/slides/sheets, exported previews, layout overflow, contrast, chart readability, formulas, and asset rendering.
11. In the final answer, summarize what changed, what source guidance was used, and any standards that could not be verified because of authentication, missing licensed fonts, missing approved assets/templates, or uninspected pages/slides/sheets.

## Guardrails

- Do not claim full Optum brand compliance unless current Brand Center guidance was accessible and the implemented artifact was checked against the relevant current pages.
- Do not download, recreate, trace, approximate, recolor, stretch, compress, rotate, crop, add effects to, or otherwise modify protected Optum logos, Lifeprint imagery, or brand marks.
- Do not bundle Optum fonts, logo files, templates, or proprietary brand assets in a repo/document package unless the repo/artifact already has the licensed files or the user provides approved assets. Prefer fallbacks and document the missing dependency.
- Do not reduce accessibility while branding. Maintain WCAG AA contrast for text and meaningful UI elements; use more than color alone for status.
- Do not replace a mature local design system, document template, slide master, workbook theme, or reporting system with one-off styling. Map Optum decisions into the system already in use.
