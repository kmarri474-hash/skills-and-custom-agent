---
name: pull-request-standards
# Changelog:
#   2.0.0 — Embed v2.1.0 PR template + pr-template-check.yml validation rules
#   1.0.0 — Initial docs stack PR standards
# Canonical source: ai-engineering → sync/stacks/docs/skills/pull-request-standards/SKILL.md
description: 'Enforces PR hygiene for documentation and standards repositories. Use when: creating commits, writing PR titles/descriptions, branching, or raising pull requests in a docs or ai-engineering repo.'
---

# Pull request standards — documentation repos

## Scope

All git commits, branches, and pull requests in documentation and standards repositories
(including the `ai-engineering` hub itself).

## When to use

- Creating a commit
- Opening or editing a pull request
- Writing a branch name
- Drafting or reviewing a PR description

---

## Branch naming

| Type | Pattern | Example |
|---|---|---|
| Feature / new content | `FB-<description>` | `FB-lint-workflow-inputs-skill` |
| Chore / maintenance | `chore/<description>` | `chore/quality-rename-repos` |
| Bug fix | `fix/<description>` | `fix/stale-repo-links` |
| Release / hotfix | `RB-<YYYY.MM.DD>-<major.minor.patch>` | `RB-2026.07.09-1.2.0` |

---

## Commit messages

Use Conventional Commits format: `<type>(scope): <description>`

- Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `ci`
- Subject ≤ 72 characters, present tense ("add" not "added")
- Run `npm run validate:diagrams` before committing files with Mermaid blocks
- Never commit `site/`, `node_modules/`, or other generated output

---

## PR template (v2.1.0)

Every PR body **MUST** begin with the version comment and include all required sections.
The `pr-template-check.yml` workflow enforces these rules automatically.

```markdown
<!-- Version: 2.1.0 - Checked and enforced by `pr-template-check.yml` -->

## Description


## Motivation and Context


## How Has This Been Tested?


## Tests
- [ ] I have added unit tests that prove my fix or feature works
- [ ] N/A - Documentation change only

## E2E Tests
- [ ] I have created/updated a PR for related E2E tests:
- [ ] This PR contains E2E tests
- [ ] N/A - E2E test changes not required. Reason:

## Type of Change
- [ ] 🐛 Bug fix (non-breaking change fixing an issue)
- [ ] ✨ New feature (non-breaking change adding functionality)
- [ ] 💥 Breaking change (fix or feature causing existing functionality to change)
- [ ] 🧹 Technical debt reduction
- [ ] 📚 Documentation update

## Rally Details
- Rally Link:

## Impact and Risk
- Dependencies:
- Rollback plan:

## Checklist
- [ ] I have performed a self-review of my own code
- [ ] No secrets or sensitive data
- [ ] I have updated relevant documentation
- [ ] I have followed proper logging practices as defined in the logging standards
- [ ] My changes generate no new warnings or errors
- [ ] I have appropriate error handling and logged those errors
- [ ] Any dependent changes have been merged and published (manifest updates, upstream and downstream PRs, etc.)

## Screenshots


## Related Issues

```

---

## Validation rules (enforced by `pr-template-check.yml`)

| Section | What is required to pass |
|---|---|
| `## Description` | Non-empty text (not just the placeholder comment) |
| `## Motivation and Context` | Non-empty text |
| `## Tests` | Exactly one checkbox checked — use the provided options verbatim |
| `## E2E Tests` | One option checked; if N/A, `Reason:` must have non-blank text after it |
| `## Type of Change` | At least one checkbox checked |
| `## Rally Details` | `- Rally Link:` followed by `N/A`, `US*`/`DE*` ID, Rally URL, or `[US123](url): Name` |
| `## Impact and Risk` | Non-empty `Dependencies:` and `Rollback plan:` values |
| `## Checklist` | **All 7 boxes** must be `[x]` — none may remain unchecked |

### Rally Details accepted formats

```
- Rally Link: N/A
- Rally Link: US12345
- Rally Link: [US12345](https://rally1.rallydev.com/#/?detail=/userstory/12345): Story Name
- Rally Link: https://rally1.rallydev.com/#/?detail=/userstory/12345
```

### MUST NOT

- **MUST NOT** leave any section empty or containing only placeholder comment text
- **MUST NOT** leave Checklist items unchecked — the gate requires all 7 `[x]`
- **MUST NOT** write custom text in the `Tests` checkboxes — use the exact provided strings
