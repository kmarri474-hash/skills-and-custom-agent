---
name: content-standards
# Changelog:
#   1.0.0 — Initial docs stack content standards
# Canonical source: ai-engineering → sync/stacks/docs/skills/content-standards/SKILL.md
description: 'Enforces documentation writing standards for Markdown-based standards/knowledge repos. Use when: writing or editing Markdown docs, creating new pages, updating README or ARCHITECTURE files.'
---

# Content Standards — Documentation Repos

## Scope

All Markdown files in documentation and standards repositories.

## When to Use

- Writing or editing any `.md` file
- Creating new documentation pages
- Updating README, ARCHITECTURE, or standards files
- Adding or revising checklists, tables, or structured content

## Procedure

### MUST

1. **MUST** start every top-level page with a single `# H1` title — exactly one per file
2. **MUST** use sentence case for all headings (e.g. `## Key components`, not `## Key Components`)
3. **MUST** use fenced code blocks with language tags — never bare code blocks
4. **MUST** use relative Markdown links for internal cross-references — not absolute `https://github.com/...` paths where a relative path works
5. **MUST** keep tables aligned and use `|---|` separator rows (not `|:---|`)
6. **MUST** wrap file path references in backticks: `` `sync/stacks/docs/` ``
7. **MUST** use emoji status flags consistently: `✅` done, `🔄` in progress, `🔲` not started, `⚠️` needs attention
8. **MUST** end every file with a single newline (no trailing blank lines)
9. **MUST** use `**bold**` for term definitions at first use, not italics

### MUST NOT

1. **MUST NOT** use bare URLs as link text — always wrap: `[descriptive text](url)`
2. **MUST NOT** mix heading levels (skip from `##` to `####`)
3. **MUST NOT** use HTML `<br>` for spacing — use blank lines between paragraphs
4. **MUST NOT** commit `site/` output or generated HTML
5. **MUST NOT** create files with names that conflict with the site generator (no `.html` files in source)

### SHOULD

- Keep prose paragraphs under 4 sentences — break into bullets if longer
- Add a TL;DR or summary section at the top of files longer than 100 lines
- Cross-link related files (e.g. `docs/stacks/nestjs.md` links to `sync/stacks/nestjs/`)
