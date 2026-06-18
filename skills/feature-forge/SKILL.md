---
name: feature-forge
description: End-to-end feature delivery pipeline that chains skills from requirement grilling through implementation, testing, debugging, and PR creation. Use when user says "feature forge", "build feature end to end", "full implementation", "chain skills", "requirement to PR", "start a feature", "new feature workflow", or wants a structured multi-phase delivery without back-and-forth.
---

# Feature Forge — Skill Chain Pipeline

Orchestrates a full feature delivery in **7 phases**, invoking the right skill at each gate.
Each phase has a **gate check** — do not proceed until the gate passes.

## Quick Start

Say: _"feature forge: [describe your requirement]"_

The pipeline runs sequentially. At each phase gate, confirm with the user before advancing.

## Phase Map

| # | Phase | Skill Invoked | Gate |
|---|-------|--------------|------|
| 1 | **Grill** | `grill-with-docs` | Shared understanding documented in CONTEXT.md + ADRs |
| 2 | **Plan** | `to-prd` → `to-issues` | PRD published, issues created on tracker |
| 3 | **Explore** | `coding-standards` + `nextjs-ai` | Codebase mapped, implementation plan written |
| 4 | **Build** | `tdd` + `coding-standards` + `logging` | All tests green, code complete |
| 5 | **Heal** | `diagnose` | App runs locally, zero 500s, all routes verified |
| 6 | **Verify** | `run-turbo-local` | Full test suite passes + dev server 200 on all routes |
| 7 | **Ship** | `pull-request` | PR created with complete template, issues closed |

## Detailed Workflow

See [REFERENCE.md](REFERENCE.md) for the full phase-by-phase checklist with exact commands, common pitfalls, and lessons learned.

See [EXAMPLES.md](EXAMPLES.md) for a real session trace of the Netra AI 3.x redesign delivery.

## Critical Rules (learned the hard way)

1. **Never create `babel.config.json`** at project root — it disables Next.js SWC and causes `_interop_require_default` 500 errors. Put babel config inline in `jest.config.js` transform only.
2. **`jest.mock()` factories** cannot reference outer-scope variables. Use `require('react')` inside factories, prefix helper functions with `mock`.
3. **Always `rm -rf .next`** before testing after config changes — stale cache causes phantom errors.
4. **Multi-line commit messages**: write to temp file, use `git commit -F`, delete after. Never use multi-line `-m "..."` in zsh.
5. **Protected branches** (`main`, `FB*`, `RB*`): never commit directly. Always create a working branch and PR.
6. **Close issues after verification**, not after code completion.
