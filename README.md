# Skills & Custom Agents

Koti's private toolkit of agent **skills** and **custom agents** for Claude Code and other
Agent-Skills-standard harnesses (Codex, VS Code Copilot).

> **Private / team-only.** This repository is private. Every install method below requires
> access to `kmarri_uhg/skills-and-custom-agent`. Nothing here is published publicly.

## ⭐ Featured: `nithin-forge`

An end-to-end delivery pipeline that chains the individual skills into one unbroken run —
from a raw idea to reviewed, committed code:

```
discover → spec → tickets → implement → verify → review
```

It's **user-invoked** (you type it; it never fires on its own) and *conducts* the companion
skills below, so install the whole toolkit to use it. See
[`skills/nithin-forge/SKILL.md`](skills/nithin-forge/SKILL.md).

## Install

Pick the row for your setup. All require repo access (private repo).

### Claude Code — plugin (recommended, auto-updating)

Installs the whole toolkit as a managed bundle that updates when you pull new versions.

```shell
/plugin marketplace add kmarri_uhg/skills-and-custom-agent
/plugin install nithin-forge@nithin-skills
```

Then invoke the pipeline as `/koti-forge:koti-forge` (plugin skills are namespaced with the
plugin name). Refresh later with `/plugin marketplace update nithin-skills`.

> The marketplace manifest lives on the repo's **default branch**, so this works once this
> change is merged to `main`.

### Claude Code / Codex / any Agent-Skills harness — direct copy (bare names)

Copies skills into your personal skills directory, so they invoke with plain names
(`/koti-forge`, no plugin prefix).

```shell
git clone https://github.com/njosep17_uhg/skills-and-custom-agent.git
cd skills-and-custom-agent

# One skill:
cp -R skills/koti-forge ~/.agents/skills/      # or ~/.claude/skills/

# The whole set:
cp -R skills/* ~/.agents/skills/
```

### `skills` CLI (if you already use it)

The [`skills`](https://www.npmjs.com/package/skills) CLI lets you pick skills and target agent,
copying each to the right per-IDE location:

```shell
npx skills@latest add kmarri_uhg/skills-and-custom-agent
```

### VS Code Copilot — custom agents

```shell
mkdir -p .github/agents
cp agents/*.agent.md .github/agents/
```

## Skills

| Skill | Description |
|-------|-------------|
| `koti-forge` | ⭐ End-to-end delivery pipeline: discover → spec → tickets → implement → verify → review |
| `ask-nithin` | Router — ask which skill or flow fits your situation |
| `caveman` | Ultra-compressed communication mode (~75% token reduction) |
| `code-review` | Review changes since a fixed point along Standards + Spec axes |
| `codebase-design` | Shared vocabulary for designing deep modules |
| `deploy-to-azure` | Deploy a containerized app to Azure App Service (UHG policy compliant) |
| `diagnose` | Disciplined diagnosis loop for hard bugs and performance regressions |
| `diagnosing-bugs` | Diagnosis loop for hard bugs and performance regressions |
| `domain-modeling` | Build and sharpen a project's domain model |
| `find-skills` | Discover and install agent skills |
| `git-guardrails-claude-code` | Hooks to block dangerous git commands before they run |
| `grill-me` | Interview the user relentlessly until shared understanding |
| `grill-with-docs` | Grill session that updates the domain model, ADRs, and glossary inline |
| `grilling` | Grill the user relentlessly about a plan, decision, or idea |
| `handoff` | Compact the conversation into a handoff document |
| `html-md-to-pdf` | Convert HTML/Markdown/slide decks to PDF on macOS |
| `implement` | Implement work from a spec or set of tickets |
| `improve-codebase-architecture` | Scan for deepening opportunities and grill through them |
| `issues-to-stories` | Convert GitHub Issues into Rally Features and User Stories |
| `prototype` | Build a throwaway prototype to answer a design question |
| `rally-board-ops` | Full Rally board lifecycle: features, stories, iterations, estimates |
| `rally-integration` | Integrate Broadcom Rally (WSAPI v2.0) into any app |
| `rally-to-prd` | Fetch a Rally story and generate a PRD |
| `research` | Investigate a question against primary sources; capture findings as Markdown |
| `resolving-merge-conflicts` | Resolve an in-progress git merge/rebase conflict |
| `run-turbo-local` | Run an app in the Care Navigation turborepo locally |
| `scaffold-exercises` | Create exercise directory structures that pass linting |
| `setup-matt-pocock-skills` | Configure the repo's tracker, triage labels, and docs for the skills |
| `setup-pre-commit` | Set up Husky + lint-staged pre-commit hooks |
| `tdd` | Test-driven development with red-green-refactor |
| `teach` | Teach a concept or skill within the workspace |
| `to-issues` | Break a plan/spec/PRD into independently-grabbable issues |
| `to-prd` | Turn conversation context into a PRD |
| `to-spec` | Turn conversation context into a spec published to the tracker |
| `to-tickets` | Break work into tracer-bullet tickets with blocking edges |
| `triage` | Triage issues through a state machine |
| `wayfinder` | Plan work too big for one session as a shared map of decision tickets |
| `write-a-skill` | Create new skills with proper structure and progressive disclosure |
| `writing-great-skills` | Reference for the vocabulary and principles of predictable skills |
| `zoom-out` | Step back for broader context or a higher-level perspective |

> **`koti-forge` runs on the mattpocock/skills ecosystem.** Its stations invoke
> `grill-with-docs`, `wayfinder`, `to-spec`, `to-tickets`, `implement`, `code-review`,
> `research`, `prototype`, `tdd`, `verify`, and `setup-matt-pocock-skills`. Installing the
> whole set (above) gives you every station.

## Custom Agents

| Agent | Description |
|-------|-------------|
| `api-architect` | Generates fully-working layered API integration code (service / manager / resilience); gathers requirements, then generates on "generate" |
| `debug` | Reproduce → minimise → hypothesise → instrument → fix → regression-test; guards every fix with a test |
| `orchestrator` | Decomposes a goal into a plan and delegates each step to the sharpest skill or subagent, verifying results before integrating |

## Repository layout

```
skills/            # Agent skills (Claude Code / Agent-Skills standard)
codex-skills/      # Codex-format skills
agents/            # Custom agent definitions (.agent.md)
.claude-plugin/    # Claude Code plugin marketplace + plugin manifest
.skill-lock.json   # Skill source tracking (skills CLI)
```
