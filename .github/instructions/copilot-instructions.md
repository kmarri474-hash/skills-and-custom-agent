---
applyTo: "**"
---

# GitHub Copilot Instructions — skills-and-custom-agent-1

## Overview

This file configures GitHub Copilot for the `skills-and-custom-agent-1` repository.
All skills listed below are **MANDATORY** and override Copilot defaults.

## Repository Context

- **Language:** Markdown, JavaScript (Node.js scripts)
- **Framework:** None (static site generator — `scripts/dev-server.mjs`)
- **Type:** docs
- **Build Tool:** npm
<!-- Fill in below -->
- **Purpose:** {{e.g. Central AI quality standards and team documentation}}

### Key Components

<!-- Fill in: describe main sections -->
- Standards: {{e.g. sync/ — synced skills, templates, shared policies}}
- Documentation: {{e.g. docs/ — design tokens, stack narratives, repo checklists}}
- Site: {{e.g. site/ — generated HTML output (gitignored)}}
- Scripts: `scripts/dev-server.mjs`, `scripts/validate-mermaid.mjs`

## Active Skills

| # | Skill | Path | Trigger |
|---|---|---|---|
| 1 | content-standards | `.github/skills/content-standards/SKILL.md` | Writing or editing any Markdown file |
| 2 | diagram-standards | `.github/skills/diagram-standards/SKILL.md` | Adding or editing Mermaid diagrams |
| 3 | pull-request-standards | `.github/skills/pull-request-standards/SKILL.md` | Git operations, commits, PRs |

## Enforcement Rules

### Instruction File Priority

Files follow a naming convention that determines precedence when instructions conflict:

1. **Standard files** (`SKILL.md`, `copilot-instructions.md`, `enforcement-rules.md`) — Synced; do not edit.
2. **`repo.instructions.md`** — Repo-specific rules (committed, never overwritten); overrides standard files when they conflict.

---

## PR Review Behavior

### Severity Labels Are Required on All Inline Findings

When performing a pull request review, **every inline comment must begin with a severity label**:

- `**[High]**` — security vulnerability, data loss, broken core functionality, significant bug, incorrect logic, or violation of a mandatory skill rule
- `**[Medium]**` — code quality issue, missing test coverage, or non-critical skill violation
- `**[Low]**` — style, naming, or minor improvement suggestion

**Format:**
```
**[High]** The `userId` field is logged directly — this may expose PII. Use the opaque ID instead.
```

This label must appear as the first line of every inline comment, on its own or immediately before the explanation. Do not omit the label or bury it in the body.

**Why this matters:** The CI Copilot gate (`pr-template-check.yml`) filters findings by severity using `COPILOT_GATE_MIN_SEVERITY`. Without the label in the comment body, the gate cannot parse the severity and treats the finding as low priority — low-severity findings are written to the CI step summary only and are never posted as PR comments.
