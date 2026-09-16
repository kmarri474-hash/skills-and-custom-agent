# Optum Digital Brand Reference

Use this file as local orientation only. Current Optum standards should be verified from Optum Brand Center whenever network access and authentication allow.

## Source Priority

1. Current Optum Brand Center guidance at `https://brand.optum.com/content/brand-overview` and user-provided approved excerpts/assets.
2. Existing approved Optum/UHG design system tokens, components, document templates, slide masters, workbook themes, or brand assets already present in the target artifact.
3. Publicly observable Optum Brand Center shell cues and public Optum web properties when the detailed Brand Center content is not accessible.
4. Conservative accessibility and UI best practices when exact brand guidance is unavailable.

## Public Site Observations

The public Brand Center URL loaded on 2026-06-11 as an Optum Brand Center JavaScript portal. The visible HTML shell confirms the Brand Center location and title, loads assets from `brand.optum.com`, and uses a Monigle/Beam API backend. Detailed content and asset endpoints observed during inspection returned `401 Unauthorized`, so do not treat local notes as complete standards.

Publicly observable portal assets included Optum-orange tones such as `#E87722`, `#E97722`, and `#F47521`, neutral grays such as `#222428`, `#717E8B`, `#E1E4E7`, `#EFF1F2`, and white. These values are evidence from the portal shell/assets, not a substitute for current Brand Center palettes.

The portal CSS referenced `Museo Sans` in the shell. Do not assume this is the required artifact font without Brand Center confirmation. Do not bundle licensed font files unless the user supplies approved files or the target artifact already contains them.

## Artifact Checklist

- Frontend/HTML: inspect theme tokens, CSS variables, Tailwind/theme config, component variants, route-level layouts, focus states, and responsive behavior.
- PowerPoint: inspect masters/layouts, theme fonts/colors, title/body hierarchy, footers, charts, tables, and embedded logos/images.
- Word/PDF/source docs: inspect styles, headings, tables, links, callouts, headers/footers, page breaks, and exported rendering.
- Excel/reports/dashboards: inspect workbook themes, table styles, chart palettes, conditional formatting, filters, frozen panes, formulas, and data readability.
- All formats: preserve meaning, accessibility, source data, formulas, and behavior while applying brand-safe visual changes.

## Reporting Expectations

In the final response after using this skill, state:

- Which artifacts and representative views/slides/sheets/pages were inspected.
- Which guidance source was used: live Brand Center, user-provided excerpts/assets, existing artifact assets, or public shell observations.
- Any gaps: Brand Center auth unavailable, missing approved Optum logo/assets/templates, missing licensed fonts, uninspected views, or checks that could not be run.
