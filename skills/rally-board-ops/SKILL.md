---
name: rally-board-ops
description: "Full Rally board management: create features/stories from PRDs, assign iterations, set plan estimates, create/assign tags, batch-update stories, and cross-reference GitHub issues. Use when user says 'rally', 'create stories', 'assign iterations', 'add tags', 'plan estimates', 'rally board', 'populate rally', 'update rally stories', or wants any CRUD operations on a Rally board. Supersedes issues-to-stories with full lifecycle support."
---

# Rally Board Operations

Full lifecycle Rally management — from PRD-to-stories creation through iteration planning, estimation, and tagging.

## Quick Start

Collect from user (skip any already provided):

1. **Rally board URL** — extract Project ObjectID (numeric segment before `d/`)
2. **Rally API key** — `zsessionid` token (ask user to type directly if sensitive)
3. **What operation?** — create stories, assign iterations, add estimates, add tags, or batch update

## Workflows

### A. Create Features & Stories from PRD

See [REFERENCE.md § PRD-to-Stories Pipeline](REFERENCE.md#prd-to-stories-pipeline) for full flow.

1. Fetch PRD from GitHub Issue (`gh issue view`)
2. Parse into feature groups and numbered stories
3. Validate field availability (check `AcceptanceCriteria` — use `Notes` if missing)
4. Create features → stories → AC → tasks → repo refs (in that order, never combined)
5. Verify all created

### B. Assign Stories to Iterations

1. Query available iterations: `GET /iteration?project=<ref>&fetch=Name,ObjectID,StartDate,EndDate`
2. Map stories to iterations by priority/phase
3. Update each story: `POST /hierarchicalrequirement/<oid>` with `{"Iteration": "<iter_ref>"}`

### C. Add Plan Estimates

1. Decide point values by complexity (1=trivial, 2=small, 3=medium, 5=large, 8=complex)
2. Update each story with `{"PlanEstimate": N}`
3. Print per-iteration totals for capacity planning

### D. Create & Assign Tags

1. Query existing tags: `GET /tag?query=(Name = "Backend")&fetch=Name,ObjectID,_ref`
2. Create missing tags: `POST /tag/create` with `{"Tag": {"Name": "Backend"}}`
3. Save tag refs to `tag_refs.json` for reuse
4. Update stories: `POST /hierarchicalrequirement/<oid>` with `{"Tags": [{"_ref": "..."}]}`

### E. Batch Update Any Field

Generate a Python script with the story-to-value mapping and execute with concurrency handling.

## Critical Rules

| Rule | Detail |
|------|--------|
| **Delay between writes** | 0.35s minimum between any Rally API write calls |
| **Retry on concurrency** | Wait 1s, retry once on `ConcurrencyConflictException` |
| **AcceptanceCriteria field** | Does NOT exist in most workspaces — use `Notes` instead |
| **Check Warnings array** | Rally returns 200 even on silent field ignores |
| **Batch by operation** | Create all stories first, then all AC, then all tasks — never per-story |
| **Use POST for updates** | Rally uses POST (not PUT/PATCH) for updates: `POST /<type>/<oid>` |

## Script Generation Pattern

Always generate a standalone Python script (not inline commands) for batch operations:
- All data mappings at the top as a list of tuples
- `assert len(items) == N` sanity check
- Delay + retry loop
- Print OK/FAIL per item + summary at end
- Use `requests` library only (no pyral or rally SDK)

See [REFERENCE.md](REFERENCE.md) for complete API patterns, error handling, and script templates.
