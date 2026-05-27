# Rally Board Ops — Reference

## Rally API Fundamentals

### Authentication

```python
RALLY_BASE = "https://rally1.rallydev.com/slm/webservice/v2.0"
HEADERS = {
    "zsessionid": "<API_KEY>",
    "Content-Type": "application/json",
}
```

### Project Reference

Extract Project ObjectID from board URL:
- URL: `https://rally1.rallydev.com/#/848873700905d/teamboard`
- ObjectID: `848873700905` (strip trailing `d/`)
- Ref: `{RALLY_BASE}/project/848873700905`

### Object Types

| Concept | Rally Type | API Path |
|---------|-----------|----------|
| Feature | PortfolioItem/Feature | `portfolioitem/feature/` |
| User Story | HierarchicalRequirement | `hierarchicalrequirement/` |
| Task | Task | `task/` |
| Defect | Defect | `defect/` |
| Tag | Tag | `tag/` |
| Iteration | Iteration | `iteration/` |

### CRUD Operations

| Op | Method | URL Pattern |
|----|--------|-------------|
| Create | POST | `{RALLY_BASE}/<type>/create` |
| Read | GET | `{RALLY_BASE}/<type>/<oid>` |
| Update | POST | `{RALLY_BASE}/<type>/<oid>` |
| Delete | DELETE | `{RALLY_BASE}/<type>/<oid>` |
| Query | GET | `{RALLY_BASE}/<type>?query=(Field = 'Value')&fetch=...` |

**NOTE:** Rally uses POST for both create and update. Create goes to `/create`, update goes to `/<oid>`.

---

## PRD-to-Stories Pipeline

### Step 1: Fetch PRD

```bash
gh issue view <NUMBER> --repo <ORG/REPO> --json title,body
```

### Step 2: Parse into Features and Stories

**Feature extraction** — look for phase headings:
```python
import re
pattern = r'###\s+(P\d+[a-z]?):\s+(.+)'
for match in re.finditer(pattern, prd_body):
    phase, title = match.group(1), match.group(2).strip()
    # Feature name: "P0 — Core Prepare Endpoint"
```

**Story extraction** — numbered items under each feature:
```python
pattern = r'(\d+)\.\s+As\s+(?:a|an)\s+\*\*(.+?)\*\*.*?I want\s+(.+?)(?:,\s+so that\s+(.+?))?(?:\n|$)'
```

### Step 3: Validate Fields

**CRITICAL** — check if AcceptanceCriteria field exists before using it:

```python
def discover_writable_text_fields(rally_base, headers):
    r = requests.get(
        f"{rally_base}/typedefinition?query=(Name = 'Hierarchical Requirement')&fetch=ObjectID",
        headers=headers,
    )
    type_oid = r.json()['QueryResult']['Results'][0]['ObjectID']
    r2 = requests.get(
        f"{rally_base}/typedefinition/{type_oid}/Attributes"
        f"?fetch=Name,ElementName,ReadOnly,Custom,AttributeType&pagesize=200",
        headers=headers,
    )
    results = r2.json().get('QueryResult', {}).get('Results', [])
    return [
        {'name': a['ElementName'], 'custom': a.get('Custom', False)}
        for a in results
        if a.get('AttributeType') == 'TEXT' and not a.get('ReadOnly', False)
    ]
```

**Known issue:** `AcceptanceCriteria` (without `c_` prefix) is NOT a real field in many Rally workspaces. API returns 200 but silently ignores the write and adds a Warning. Always use `Notes` as the fallback for AC content.

### Step 4: Create Features

```python
def create_feature(rally_base, headers, project_ref, name, description):
    payload = {
        "PortfolioItem/Feature": {
            "Name": name,
            "Description": description,
            "Project": project_ref,
        }
    }
    r = requests.post(f"{rally_base}/portfolioitem/feature/create", headers=headers, json=payload)
    result = r.json()
    errors = result.get("CreateResult", {}).get("Errors", [])
    if errors:
        raise Exception(f"Feature create failed: {errors}")
    obj = result["CreateResult"]["Object"]
    return {"ref": obj["_ref"], "oid": obj["ObjectID"], "fid": obj["FormattedID"]}
```

### Step 5: Create Stories Under Features

```python
def create_story(rally_base, headers, project_ref, feature_ref, name, description, plan_estimate=3):
    payload = {
        "HierarchicalRequirement": {
            "Name": name,
            "Description": description,
            "Project": project_ref,
            "PortfolioItem": feature_ref,
            "PlanEstimate": plan_estimate,
        }
    }
    r = requests.post(f"{rally_base}/hierarchicalrequirement/create", headers=headers, json=payload)
    result = r.json()
    errors = result.get("CreateResult", {}).get("Errors", [])
    if errors:
        return None, errors
    obj = result["CreateResult"]["Object"]
    return {"ref": obj["_ref"], "oid": obj["ObjectID"], "fid": obj["FormattedID"]}, []
```

### Step 6: Write Acceptance Criteria (Notes field)

```python
ac_html = """<h3>Acceptance Criteria</h3>
<ul>
<li><b>AC1:</b> When X happens, Y is the result.</li>
<li><b>AC2:</b> Z is validated and sourced.</li>
</ul>"""
payload = {"HierarchicalRequirement": {"Notes": ac_html}}
requests.post(f"{rally_base}/hierarchicalrequirement/{story_oid}", headers=headers, json=payload)
```

### Step 7: Create Tasks

```python
def create_task(rally_base, headers, project_ref, story_ref, name, index=1):
    payload = {
        "Task": {
            "Name": name,
            "WorkProduct": story_ref,
            "Project": project_ref,
            "TaskIndex": index,
        }
    }
    r = requests.post(f"{rally_base}/task/create", headers=headers, json=payload)
    return r.json().get("CreateResult", {}).get("Errors", [])
```

### Step 8: Add Repository References

Append to story Description:
```python
repo_html = """<h3>Repository Reference</h3>
<ul>
<li><b>Backend:</b> <a href="https://github.com/org/repo">repo</a></li>
<li><b>UI:</b> <a href="https://github.com/org/ui-repo">ui-repo</a></li>
</ul>
<p><b>PRD Source:</b> <a href="https://github.com/org/repo/issues/40">Issue #40</a></p>"""
```

### Execution Order (CRITICAL)

**NEVER combine create + update in a single per-story loop.** Batch each operation type:

1. Create all features (0.5s delay between)
2. Create all stories (0.3s delay between)
3. Update all stories with AC in Notes (0.3s delay)
4. Create all tasks (0.2s delay between, check for duplicates first)
5. Append repo references to Description (0.3s delay)
6. Verify everything

---

## Iteration Management

### Query Available Iterations

```python
def get_iterations(rally_base, headers, project_ref):
    r = requests.get(
        f"{rally_base}/iteration"
        f"?project={project_ref}"
        f"&fetch=Name,ObjectID,StartDate,EndDate,_ref"
        f"&order=StartDate"
        f"&pagesize=50",
        headers=headers,
    )
    return r.json().get("QueryResult", {}).get("Results", [])
```

### Assign Story to Iteration

```python
def assign_iteration(rally_base, headers, story_oid, iteration_ref):
    payload = {"HierarchicalRequirement": {"Iteration": iteration_ref}}
    r = requests.post(
        f"{rally_base}/hierarchicalrequirement/{story_oid}",
        headers=headers, json=payload,
    )
    result = r.json()
    op = result.get(list(result.keys())[0], {})
    return not bool(op.get("Errors")), op.get("Errors", [])
```

### Strategy: Divide by Priority

Split stories across iterations based on priority tier:

```python
# Example: 91 stories across 3 iterations
iter_map = {
    "P0-core": "iteration_ref_1",     # Iteration 11: P0 core backend + UI shell
    "P0-remaining": "iteration_ref_2", # Iteration 12: P0 remaining + promoted
    "P1-P2-P3": "iteration_ref_3",     # Iteration 13: P1 accordion + P2 AI + P3 + deferred
}
```

Keep iteration sizes balanced (e.g., 30/30/31 for 91 stories).

---

## Plan Estimates

### Set Plan Estimate on Story

```python
def set_plan_estimate(rally_base, headers, story_oid, points):
    payload = {"HierarchicalRequirement": {"PlanEstimate": points}}
    r = requests.post(
        f"{rally_base}/hierarchicalrequirement/{story_oid}",
        headers=headers, json=payload,
    )
    result = r.json()
    op = result.get(list(result.keys())[0], {})
    return not bool(op.get("Errors")), op.get("Errors", [])
```

### Estimation Heuristics

| Points | Complexity | Examples |
|--------|-----------|----------|
| 1 | Trivial | Config change, toggle, simple UI label |
| 2 | Small | Single data tool, one API field, simple card |
| 3 | Medium | Multi-field data tool, card with interactions, filter logic |
| 5 | Large | Complex integration, timeline component, state machine |
| 8 | Very Large | AI/ML feature, full accordion with expand, complex pipeline |

### Capacity Reporting

After assigning estimates, print per-iteration totals:

```python
for iter_name, stories in iteration_groups.items():
    total = sum(s['points'] for s in stories)
    print(f"{iter_name}: {len(stories)} stories, {total} points")
```

---

## Tag Management

### Query Existing Tags

```python
def get_tag(rally_base, headers, tag_name):
    r = requests.get(
        f"{rally_base}/tag?query=(Name = \"{tag_name}\")&fetch=Name,ObjectID,_ref",
        headers=headers,
    )
    results = r.json().get("QueryResult", {}).get("Results", [])
    return results[0] if results else None
```

### Create Tag

```python
def create_tag(rally_base, headers, tag_name):
    payload = {"Tag": {"Name": tag_name}}
    r = requests.post(f"{rally_base}/tag/create", headers=headers, json=payload)
    result = r.json()
    errors = result.get("CreateResult", {}).get("Errors", [])
    if errors:
        return None, errors
    obj = result["CreateResult"]["Object"]
    return {"ref": obj["_ref"], "oid": obj["ObjectID"], "name": tag_name}, []
```

### Ensure Tags Exist (Idempotent)

```python
def ensure_tags(rally_base, headers, tag_names):
    """Get or create tags, return name→ref map."""
    tag_refs = {}
    for name in tag_names:
        existing = get_tag(rally_base, headers, name)
        if existing:
            tag_refs[name] = existing["_ref"]
            print(f"  EXISTS: {name} -> {existing['_ref']}")
        else:
            tag, errors = create_tag(rally_base, headers, name)
            if tag:
                tag_refs[name] = tag["ref"]
                print(f"  CREATED: {name} -> {tag['ref']}")
            else:
                print(f"  FAILED: {name} -> {errors}")
        time.sleep(0.35)
    return tag_refs
```

### Assign Tags to Story

```python
def assign_tags(rally_base, headers, story_oid, tag_refs_list):
    """tag_refs_list: [{"_ref": "https://..."}, ...]"""
    payload = {"HierarchicalRequirement": {"Tags": tag_refs_list}}
    r = requests.post(
        f"{rally_base}/hierarchicalrequirement/{story_oid}",
        headers=headers, json=payload,
    )
    result = r.json()
    op = result.get(list(result.keys())[0], {})
    return not bool(op.get("Errors")), op.get("Errors", [])
```

### Recommended Tag Categories

| Category | Tags | Purpose |
|----------|------|---------|
| Layer | Frontend, Backend | Which codebase |
| Type | Data-Tool, Infrastructure, AI/ML, Monitoring, Integration | Nature of work |
| Priority | P0, P1, P2, P3 | Priority tier |
| Status | Deferred, Removed | Out-of-scope markers |

### Tag Assignment Strategy

Map stories to tags based on:
1. **Layer**: Backend if API/agent/tool; Frontend if UI component
2. **Type**: What kind of work (data fetching, infra, AI, monitoring, etc.)
3. **Priority**: Match the feature's priority phase (P0, P1, P2, P3)
4. **Status overrides**: Deferred/Removed replace priority tag

---

## Error Handling

### ConcurrencyConflictException

Rally's most common error when doing batch operations:

```python
def with_retry(fn, *args, delay=0.35, retries=1):
    """Execute fn with concurrency retry."""
    time.sleep(delay)
    ok, errors = fn(*args)
    if ok:
        return True, []
    if any("Concurrency" in str(e) for e in errors) and retries > 0:
        time.sleep(1)
        return with_retry(fn, *args, delay=0, retries=retries - 1)
    return False, errors
```

**Prevention:**
- 0.2–0.5s delay between writes
- Batch by operation type (all stories, then all AC, then all tasks)
- Never parallelize writes to the same parent object

### Silent Field Ignores

Always check warnings:

```python
warnings = result.get("OperationResult", {}).get("Warnings", [])
for w in warnings:
    if "Ignored JSON element" in w:
        print(f"WARNING: Field silently ignored: {w}")
```

### ObjectID Mismatch

When updating, always confirm OID by querying FormattedID:

```python
def get_story_oid(rally_base, headers, project_ref, formatted_id):
    r = requests.get(
        f"{rally_base}/hierarchicalrequirement"
        f"?query=(FormattedID = '{formatted_id}')"
        f"&fetch=ObjectID,_ref&project={project_ref}",
        headers=headers,
    )
    results = r.json().get("QueryResult", {}).get("Results", [])
    return (results[0]["ObjectID"], results[0]["_ref"]) if results else (None, None)
```

---

## Query Patterns

### Stories by Feature

```python
r = requests.get(
    f"{rally_base}/hierarchicalrequirement"
    f"?query=(Feature.FormattedID = '{feature_fid}')"
    f"&fetch=FormattedID,Name,ObjectID,_ref,Description,Notes,Tags,PlanEstimate,Iteration"
    f"&pagesize=200&project={project_ref}",
    headers=headers,
)
```

### Stories by Iteration

```python
r = requests.get(
    f"{rally_base}/hierarchicalrequirement"
    f"?query=(Iteration.Name = '{iter_name}')"
    f"&fetch=FormattedID,Name,PlanEstimate,Tags"
    f"&pagesize=200&project={project_ref}",
    headers=headers,
)
```

### Stories by Tag

```python
r = requests.get(
    f"{rally_base}/hierarchicalrequirement"
    f"?query=(Tags.Name = 'Backend')"
    f"&fetch=FormattedID,Name,Tags"
    f"&pagesize=200&project={project_ref}",
    headers=headers,
)
```

### Paginated Query

Rally limits to 200 results per page:

```python
def query_all(rally_base, headers, endpoint, query, fetch, project_ref):
    all_results = []
    start = 1
    while True:
        r = requests.get(
            f"{rally_base}/{endpoint}"
            f"?query={query}&fetch={fetch}"
            f"&pagesize=200&start={start}&project={project_ref}",
            headers=headers,
        )
        qr = r.json().get("QueryResult", {})
        results = qr.get("Results", [])
        all_results.extend(results)
        if start + len(results) > qr.get("TotalResultCount", 0):
            break
        start += 200
    return all_results
```

---

## Cross-Referencing GitHub Issues

After creating Rally stories from a GitHub Issue PRD, post a cross-reference comment:

```bash
gh issue comment <NUMBER> --repo <ORG/REPO> --body "## Rally Cross-Reference

| Feature | Rally ID | Stories |
|---------|----------|---------|
| P0 Core | F1852252 | 26 stories |
| P1 Extensions | F1852253 | 2 stories |

[Rally Board](https://rally1.rallydev.com/#/<PROJECT_OID>d/teamboard)"
```

---

## Script Template Pattern

Every batch operation script follows this structure:

```python
#!/usr/bin/env python3
"""<Operation description>."""
import requests, time, json

RALLY_BASE = "https://rally1.rallydev.com/slm/webservice/v2.0"
HEADERS = {"zsessionid": "<KEY>", "Content-Type": "application/json"}
DELAY = 0.35

# === DATA MAPPING ===
items = [
    (oid, formatted_id, value),
    # ...
]

assert len(items) == N, f"Expected N, got {len(items)}"
print(f"Processing {len(items)} items...")

success = fail = 0
for oid, fid, value in items:
    time.sleep(DELAY)
    url = f"{RALLY_BASE}/hierarchicalrequirement/{oid}"
    data = {"HierarchicalRequirement": {"FieldName": value}}
    r = requests.post(url, headers=HEADERS, json=data, timeout=30)
    result = r.json()
    op = result.get(list(result.keys())[0], {})
    if op.get("Errors"):
        if any("Concurrency" in e for e in op["Errors"]):
            time.sleep(1)
            r = requests.post(url, headers=HEADERS, json=data, timeout=30)
            result = r.json()
            op = result.get(list(result.keys())[0], {})
            if op.get("Errors"):
                print(f"  FAIL: {fid} -> {op['Errors']}")
                fail += 1
                continue
        else:
            print(f"  FAIL: {fid} -> {op['Errors']}")
            fail += 1
            continue
    print(f"  OK: {fid} -> {value}")
    success += 1

print(f"\nDone: {success} OK, {fail} FAIL out of {len(items)}")
```

---

## Verification Checklist

After any batch operation, verify:

```python
def verify_stories(rally_base, headers, project_ref, feature_fids):
    issues = []
    for fid in feature_fids:
        stories = get_stories_by_feature(rally_base, headers, project_ref, fid)
        for s in stories:
            sid = s['FormattedID']
            if not s.get('Notes'):
                issues.append(f"{sid}: Missing AC in Notes")
            if s.get('Tasks', {}).get('Count', 0) == 0:
                issues.append(f"{sid}: No tasks")
            if not s.get('PlanEstimate'):
                issues.append(f"{sid}: No plan estimate")
            if not s.get('Iteration'):
                issues.append(f"{sid}: No iteration assigned")
            if s.get('Tags', {}).get('Count', 0) == 0:
                issues.append(f"{sid}: No tags")
    return issues
```

## Key Lessons Learned

| Issue | Solution |
|-------|----------|
| `AcceptanceCriteria` field silently ignored | Check TypeDefinition first; use `Notes` field |
| `ConcurrencyConflictException` on rapid writes | 0.35s delay + 1 retry with 1s backoff |
| Rally returns 200 on field-write failures | Always check `Warnings` array |
| Feature OID vs Story OID confusion | Features: `portfolioitem/feature/`, Stories: `hierarchicalrequirement/` |
| Wrong ObjectID after creation | Query by FormattedID to get current OID |
| Tags must exist before assigning | Use ensure_tags() pattern — get-or-create |
| Iteration names may have duplicates | Use ObjectID, not Name, for iteration references |
| Combining create + update per-story | Batch by operation type to avoid concurrency |
| Multi-line strings in git commit | Use temp file + `git commit -F` |
