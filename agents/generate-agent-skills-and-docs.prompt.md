---
description: 'Analyze a repository and generate AI agent skills, Copilot instructions, Codex skills, and an upgraded README. Documentation-only changes — no runtime files modified.'
mode: 'agent'
---

# AI Agent Skills & Documentation Generator

You are an AI IDE Agent with edit-only access to this repository. Your job is to analyze the codebase and produce **documentation-only** changes that define strict, enforceable AI skills for GitHub Copilot and Codex agents.

---

## GLOBAL CONSTRAINTS (ABSOLUTE)

- **DO NOT** create, modify, refactor, or suggest any source code, configuration, or runtime files
- **ONLY** Markdown (`.md`) files may be created or modified
- **ALL** changes MUST be committed to a **NEW branch** named: `docs/agent-skills-and-readme-upgrade`
- **DO NOT** invent architecture, endpoints, flows, or behaviors — all documentation must be derived strictly from existing repository content
- If something is unclear, document it explicitly as an **assumption**
- Skills are **NOT advisory** — they are **MANDATORY enforcement rules**

---

## PHASE 1 — REPOSITORY ANALYSIS

Perform a thorough analysis of the repository by reading actual source files. Cover:

1. **Business purpose & scope** — What does this service do? Who consumes it?
2. **Tech stack** — Framework, language, runtime, deployment model
3. **Architectural layers & boundaries** — Entry points, middleware pipeline, API layer, business logic, external integrations
4. **Folder & module responsibilities** — What each directory and module owns
5. **API organization & conventions** — REST/GraphQL/gRPC, endpoint patterns, request/response shapes
6. **Error handling patterns** — Exception filters, try/catch patterns, error response shapes
7. **Logging & observability** — Logger library, log levels, structured logging, metrics, tracing
8. **Auth & security** — Authentication strategy, authorization guards, token handling
9. **Environment & configuration** — Config management, secrets handling, environment-specific files
10. **Dependencies & integrations** — External services, APIs, message queues, databases
11. **Testing patterns** — Test framework, test file locations, coverage setup
12. **CI/CD pipeline** — Build, test, scan, deploy pipeline files
13. **Deployment model** — Containerization, orchestration, Helm/K8s, cloud platform

**Ground every finding in actual file paths and code patterns.**

---

## PHASE 2 — ROOT README.md UPDATE

Modify **ONLY** the existing root `README.md`. Replace boilerplate content with project-specific documentation:

| Section | Content |
|---|---|
| **Project Overview** | Business intent, problem solved, consumers |
| **High-Level Architecture** | Request → processing → response flow, integrations, boundaries (ASCII diagram) |
| **Folder Structure** | Tree-style with responsibilities per directory |
| **Local Development** | Conceptual startup and config expectations (**NO secrets or real values**) |
| **API Design** | Documentation-only sample endpoints, request/response shapes, error expectations |
| **Logging & Observability** | Log fields, levels, correlation IDs, PII/PHI rules, metrics |
| **Branching & PR Strategy** | Branch naming, review process, quality gates |
| **Non-Goals** | Explicit exclusions — what this service does NOT do |

**NO executable examples. NO real credential values.**

---

## PHASE 3 — GITHUB COPILOT SKILLS

Create exactly these files:

```
.github/skills/coding-standards/SKILL.md
.github/skills/pull-request-standards/SKILL.md
.github/skills/logging-standards/SKILL.md
.github/skills/architecture-guardrails/SKILL.md
```

### Required SKILL.md Format

Each file MUST use the official Copilot skill pattern:

```markdown
---
name: <skill-name>
description: '<What it enforces>. Use when: <trigger conditions with keywords>.'
---

# <Skill Title>

## Scope
<What files/areas this skill covers>

## When to Use
- <Trigger condition 1>
- <Trigger condition 2>
- ...

## Procedure

### MUST
1. **MUST** <rule derived from actual repo patterns>
...

### MUST NOT
1. **MUST NOT** <prohibition derived from actual repo patterns>
...

## Prohibited Actions
- <Action that must never be taken>
- ...

## Examples

### Good
<Code example following the rules — derived from actual repo patterns>

### Bad
<Code example violating the rules — with explanation>

## Enforcement Statement
This skill is **MANDATORY**. Any violation will be flagged with:
> **"Violation: Copilot skill <skill-name> not followed"**

### Implementation Plan Enforcement
Before writing ANY code, the agent MUST produce a clear implementation plan.
If no plan is provided, code generation MUST be refused.
```

### Skill Content Guidelines

- **coding-standards**: Framework patterns, naming conventions, dependency injection, typing, validation, logging usage, response shapes — all derived from actual source code
- **pull-request-standards**: Branch naming (from existing branches), PR description template, commit message format, CI gates (from pipeline files), secrets policy
- **logging-standards**: Logger library used, log levels, structured format, PII/PHI field list (from models), correlation IDs, metrics library, prohibited logging patterns
- **architecture-guardrails**: Module boundaries, allowed/prohibited integration patterns, data access patterns, deployment model, auth pipeline, config management, dependency rules

**Every rule must be traceable to an actual pattern in the repository.**

---

## PHASE 4 — COPILOT INSTRUCTIONS

Create:
```
.github/instructions/copilot-instructions.md
```

This file MUST:
- List all 4 skills with their paths
- State that **skills override Copilot defaults**
- Require **self-validation** before generating suggestions
- **REFUSE** disallowed actions with the violation message format
- Require **implementation plans** before any code generation
- Show which skills are applied when executing requests
- Use this exact violation message: `"Violation: Copilot skill <skill-name> not followed"`

---

## PHASE 5 — CODEX SKILLS

Create equivalent skills under:
```
.codex/skills/coding-standards/SKILL.md
.codex/skills/pull-request-standards/SKILL.md
.codex/skills/logging-standards/SKILL.md
.codex/skills/architecture-guardrails/SKILL.md
```

Codex skills MUST:
- Use the same YAML frontmatter format (`name`, `description`)
- Be **semantically identical** to Copilot skills
- Use LLM-agent language (no IDE-specific assumptions)
- Include **anti-hallucination rules**: reject speculative changes, verify references exist, defer to repository rules over model defaults
- Use violation message: `"Violation: Codex skill <skill-name> not followed"`

---

## PHASE 6 — COMMIT & PR

1. Create branch: `docs/agent-skills-and-readme-upgrade`
2. Stage only `.md` files
3. Commit with message: `Add AI agent skills documentation and upgrade README`
4. Push and create a PR to the default branch with a description containing:
   - Summary of all changes
   - List of files created/modified
   - Implementation plan
   - Checklist confirming: no secrets, markdown-only, no runtime changes, repo-derived content

---

## VALIDATION CHECKLIST

Before completing, verify:

- [ ] New branch created
- [ ] Root `README.md` updated with project-specific content
- [ ] `.github/skills/**/SKILL.md` — 4 files with YAML frontmatter
- [ ] `.github/instructions/copilot-instructions.md` created
- [ ] `.codex/skills/**/SKILL.md` — 4 files with YAML frontmatter
- [ ] ALL skill `name` fields match their folder names
- [ ] ALL skill `description` fields include "Use when:" trigger phrases
- [ ] **Markdown-only changes** — zero runtime or config files touched
- [ ] **No hallucinated content** — every rule traces to actual repo code
- [ ] PR created with proper description

---

**BEGIN EXECUTION IMMEDIATELY.**
