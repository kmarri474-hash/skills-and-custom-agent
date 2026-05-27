---
name: issues-to-stories
description: "Convert GitHub Issues (PRDs) into Rally Features and User Stories with full acceptance criteria, tasks, and repo references. Use when user says 'create rally stories', 'convert issues to stories', 'issues to rally', 'create features from PRD', 'PRD to rally', or wants to populate a Rally board from a GitHub issue containing a PRD. Requires: Rally project/board URL, API key, GitHub issue URL."
---

# Issues to Rally Stories

Convert a GitHub Issue (PRD) into fully populated Rally Features and User Stories.

## Workflow

### 1. Collect Inputs

Ask the user for (skip any already provided):

- **GitHub Issue URL** — e.g., `https://github.com/org/repo/issues/40`
- **Rally Board URL** — e.g., `https://rally1.rallydev.com/#/848873700905d/teamboard`
- **Rally API Key** — their `ZSESSIONID` token (ask user to type directly if sensitive)
- **Repository URLs** — repos for backend/frontend (to tag stories with repo references)

Extract the Rally **Project ObjectID** from the board URL (the numeric segment before `d/`).

### 2. Fetch the PRD

```bash
gh issue view <NUMBER> --repo <ORG/REPO> --json title,body
```

If `gh` CLI is not authenticated, fall back to the GitHub API with a token.

### 3. Parse PRD into Features and Stories

Scan the PRD body for phase/feature groupings and numbered user stories.

**Feature extraction pattern:**
- Look for `### P0:`, `### P1:`, `## Phase` headings or similar groupings
- Each phase becomes a Rally **Feature** (PortfolioItem/Feature)
- Feature name format: `P0 — <Phase Title>`

**Story extraction pattern:**
- Numbered items (1., 2., ...) under each phase heading
- Each becomes a **User Story** (HierarchicalRequirement)
- Story name format: `S<N>: <Short Title>` (derive from the "I want..." clause)

**For each story, extract:**
- Description (the full "As a... I want... so that..." text as HTML)
- Acceptance criteria (from AC sections, implementation notes, or inferred from story)
- Tasks (from "Modules to build" sections, implementation decisions, testing notes)
- Plan estimate (based on complexity: 1-8 points)
- Repository classification (backend/frontend/both based on where code changes land)

### 4. Validate Rally Field Availability

**CRITICAL:** Before creating stories, check which fields exist in the target workspace:

```python
# Check if AcceptanceCriteria field exists
r = requests.get(f"{RALLY_BASE}/typedefinition?query=(Name = 'Hierarchical Requirement')&fetch=ObjectID", headers=HEADERS)
type_oid = r.json()['QueryResult']['Results'][0]['ObjectID']

r2 = requests.get(
    f"{RALLY_BASE}/typedefinition/{type_oid}/Attributes"
    f"?fetch=Name,ElementName,ReadOnly,AttributeType"
    f"&pagesize=200&query=(AttributeType = 'TEXT')",
    headers=HEADERS,
)
# Look for writable TEXT fields — use for AC storage
```

**Known issue:** Many Rally workspaces do NOT have `AcceptanceCriteria` as a writable field. The API silently ignores writes to it with a warning. Use **`Notes`** field as the AC target instead. If `c_AcceptanceCriteria` (custom) exists and is writable, prefer that.

### 5. Create Features in Rally

```python
payload = {
    "PortfolioItem/Feature": {
        "Name": "P0 — Core Prepare Endpoint",
        "Description": "<p>Phase description from PRD</p>",
        "Project": f"{RALLY_BASE}/project/{PROJECT_OID}",
    }
}
r = requests.post(f"{RALLY_BASE}/portfolioitem/feature/create", headers=HEADERS, json=payload)
feature_ref = r.json()['CreateResult']['Object']['_ref']
```

Add a **0.5-second delay** between feature creations to avoid concurrency conflicts.

### 6. Create User Stories

```python
payload = {
    "HierarchicalRequirement": {
        "Name": "S1: Primary BH diagnosis with source system",
        "Description": "<h3>User Story</h3><p>As a...</p>",
        "Project": PROJECT_REF,
        "PortfolioItem": feature_ref,  # Links story to its Feature
        "PlanEstimate": 3,
    }
}
r = requests.post(f"{RALLY_BASE}/hierarchicalrequirement/create", headers=HEADERS, json=payload)
```

**Concurrency handling:** When creating many stories under one Feature, Rally throws `ConcurrencyConflictException`. Mitigate with:
- 0.3s delay between creates
- On error: wait 1s, retry once
- If retry fails: collect the story and batch-retry at the end

### 7. Add Acceptance Criteria

Write AC to the **Notes** field (or `c_AcceptanceCriteria` if available):

```python
ac_html = """<h3>Acceptance Criteria</h3>
<ul>
<li><b>AC1:</b> When X happens, Y is the result.</li>
<li><b>AC2:</b> Z is validated and sourced.</li>
</ul>"""
payload = {"HierarchicalRequirement": {"Notes": ac_html}}
requests.post(f"{RALLY_BASE}/hierarchicalrequirement/{story_oid}", headers=HEADERS, json=payload)
```

### 8. Create Tasks

```python
payload = {
    "Task": {
        "Name": "Implement resolver function",
        "WorkProduct": story_ref,
        "Project": PROJECT_REF,
        "TaskIndex": 1,
    }
}
requests.post(f"{RALLY_BASE}/task/create", headers=HEADERS, json=payload)
```

- Check for existing tasks before creating (avoids duplicates on retry)
- 0.2s delay between task creations
- Retry once on ConcurrencyConflictException

### 9. Add Repository References

Classify each story and append repo links to Description:

```python
repo_html = """<h3>Repository Reference</h3>
<ul>
<li><b>Backend:</b> <a href="https://github.com/org/backend-repo">backend-repo</a></li>
<li><b>UI:</b> <a href="https://github.com/org/ui-repo">ui-repo</a></li>
</ul>
<p><b>PRD Source:</b> <a href="https://github.com/org/repo/issues/40">GitHub Issue #40</a></p>"""
```

### 10. Verify

Query all created stories and confirm:
- All stories from the PRD exist (count matches)
- Story names match PRD titles exactly
- All stories have Notes (AC) populated
- All stories have tasks (check `Tasks.Count > 0`)
- Repository references present in Description

See [REFERENCE.md](REFERENCE.md) for full API patterns, error handling, and script templates.

## Key Lessons

| Issue | Solution |
|-------|----------|
| `AcceptanceCriteria` field silently ignored | Check TypeDefinition first; use `Notes` field |
| `ConcurrencyConflictException` on rapid creates | Add delays (0.2-0.5s) + retry logic |
| Wrong ObjectID for story updates | Always query by FormattedID to get correct OID |
| Feature ObjectID vs Story ObjectID confusion | Features use `portfolioitem/feature/`, Stories use `hierarchicalrequirement/` |
| Rally API returns 200 even on field-write failures | Always check `Warnings` array in response |
