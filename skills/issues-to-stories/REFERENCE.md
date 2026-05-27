# Issues-to-Stories Reference

## Rally API Fundamentals

### Authentication

All Rally API requests use the `zsessionid` header:

```python
RALLY_BASE = "https://rally1.rallydev.com/slm/webservice/v2.0"
HEADERS = {
    "zsessionid": "<API_KEY>",
    "Content-Type": "application/json",
}
```

### Project Reference

Extract the Project ObjectID from the Rally board URL:
- URL: `https://rally1.rallydev.com/#/848873700905d/teamboard`
- ObjectID: `848873700905` (strip the trailing `d/` suffix)
- Ref: `https://rally1.rallydev.com/slm/webservice/v2.0/project/848873700905`

### Object Types

| Concept | Rally Type | API Path |
|---------|-----------|----------|
| Feature | PortfolioItem/Feature | `portfolioitem/feature/` |
| User Story | HierarchicalRequirement | `hierarchicalrequirement/` |
| Task | Task | `task/` |
| Defect | Defect | `defect/` |

---

## Field Discovery

### Check Available Writable Fields

Before attempting to write to any field, query the TypeDefinition to confirm the field exists and is writable:

```python
import requests

def discover_writable_text_fields(rally_base, headers):
    """Find all writable TEXT fields on HierarchicalRequirement."""
    # Get type definition OID
    r = requests.get(
        f"{rally_base}/typedefinition"
        f"?query=(Name = 'Hierarchical Requirement')&fetch=ObjectID",
        headers=headers,
    )
    type_oid = r.json()['QueryResult']['Results'][0]['ObjectID']

    # Get all attributes
    r2 = requests.get(
        f"{rally_base}/typedefinition/{type_oid}/Attributes"
        f"?fetch=Name,ElementName,ReadOnly,Custom,AttributeType"
        f"&pagesize=200&start=1",
        headers=headers,
    )
    results = r2.json().get('QueryResult', {}).get('Results', [])

    writable_text = []
    for attr in results:
        if attr.get('AttributeType') == 'TEXT' and not attr.get('ReadOnly', False):
            writable_text.append({
                'name': attr['ElementName'],
                'custom': attr.get('Custom', False),
            })
    return writable_text
```

### Common Writable TEXT Fields

| Field | Custom | Notes |
|-------|--------|-------|
| `Description` | No | Primary story description (HTML) |
| `Notes` | No | Best fallback for Acceptance Criteria |
| `c_AcceptanceCriteria` | Yes | May not exist in all workspaces |
| `c_HighlightsandAccomplishments` | Yes | Workspace-specific |

**CRITICAL:** The `AcceptanceCriteria` field (without `c_` prefix) is NOT a real field in many Rally workspaces. The API returns no error on write — it silently ignores the value and returns a `Warning`:

```json
{
  "Warnings": [
    "Ignored JSON element HierarchicalRequirement.AcceptanceCriteria during processing of this request."
  ]
}
```

**Always check the `Warnings` array in every API response.**

---

## API Patterns

### Create Feature

```python
def create_feature(rally_base, headers, project_ref, name, description):
    payload = {
        "PortfolioItem/Feature": {
            "Name": name,
            "Description": description,
            "Project": project_ref,
        }
    }
    r = requests.post(
        f"{rally_base}/portfolioitem/feature/create",
        headers=headers,
        json=payload,
    )
    result = r.json()
    errors = result.get("CreateResult", {}).get("Errors", [])
    if errors:
        raise Exception(f"Feature create failed: {errors}")
    obj = result["CreateResult"]["Object"]
    return {
        "ref": obj["_ref"],
        "oid": obj["ObjectID"],
        "fid": obj["FormattedID"],
    }
```

### Create Story Under Feature

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
    r = requests.post(
        f"{rally_base}/hierarchicalrequirement/create",
        headers=headers,
        json=payload,
    )
    result = r.json()
    errors = result.get("CreateResult", {}).get("Errors", [])
    if errors:
        return None, errors
    obj = result["CreateResult"]["Object"]
    return {
        "ref": obj["_ref"],
        "oid": obj["ObjectID"],
        "fid": obj["FormattedID"],
    }, []
```

### Update Story Field

```python
def update_story_field(rally_base, headers, story_oid, field_name, field_value):
    payload = {"HierarchicalRequirement": {field_name: field_value}}
    r = requests.post(
        f"{rally_base}/hierarchicalrequirement/{story_oid}",
        headers=headers,
        json=payload,
    )
    result = r.json()
    errors = result.get("OperationResult", {}).get("Errors", [])
    warnings = result.get("OperationResult", {}).get("Warnings", [])
    return not bool(errors), errors, warnings
```

### Create Task Under Story

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
    result = r.json()
    errors = result.get("CreateResult", {}).get("Errors", [])
    return not bool(errors), errors
```

### Query Stories by Feature

```python
def get_stories_by_feature(rally_base, headers, project_ref, feature_fid):
    r = requests.get(
        f"{rally_base}/hierarchicalrequirement"
        f"?query=(Feature.FormattedID = '{feature_fid}')"
        f"&fetch=FormattedID,Name,ObjectID,_ref,Description,Notes,Tasks"
        f"&pagesize=50"
        f"&project={project_ref}",
        headers=headers,
    )
    return r.json().get("QueryResult", {}).get("Results", [])
```

### Get Existing Tasks (Duplicate Prevention)

```python
def get_existing_task_names(headers, story_ref):
    r = requests.get(
        f"{story_ref}/Tasks?fetch=Name&pagesize=50",
        headers=headers,
    )
    return [t["Name"] for t in r.json().get("QueryResult", {}).get("Results", [])]
```

---

## Error Handling

### ConcurrencyConflictException

Rally throws this when multiple writes hit the same parent object (Feature or Story) in rapid succession:

```
ConcurrencyConflictException: Modified since read on update
```

**Mitigation strategy:**

```python
import time

def create_with_retry(create_fn, *args, max_retries=2, delay=0.5):
    """Retry on concurrency conflicts."""
    for attempt in range(max_retries + 1):
        ok, errors = create_fn(*args)
        if ok:
            return True, []
        if any("ConcurrencyConflict" in str(e) for e in errors):
            if attempt < max_retries:
                time.sleep(delay * (attempt + 1))
                continue
        return False, errors
    return False, ["Max retries exceeded"]
```

**Prevention:**
- 0.2–0.5s delay between creates under the same parent
- Create stories for different features in round-robin order when possible
- Never parallelize creates under the same parent

### Silent Field Ignores

Rally returns HTTP 200 even when a field write is ignored. Always check:

```python
result = r.json()
warnings = result.get("OperationResult", {}).get("Warnings", [])
for w in warnings:
    if "Ignored JSON element" in w:
        print(f"WARNING: Field was silently ignored: {w}")
        # Fall back to alternative field
```

### ObjectID Mismatch

When updating stories, the ObjectID from the creation response may differ from the queryable ObjectID. Always query by FormattedID to get the current correct OID:

```python
def get_story_oid(rally_base, headers, project_ref, formatted_id):
    r = requests.get(
        f"{rally_base}/hierarchicalrequirement"
        f"?query=(FormattedID = '{formatted_id}')"
        f"&fetch=ObjectID,_ref"
        f"&project={project_ref}",
        headers=headers,
    )
    results = r.json().get("QueryResult", {}).get("Results", [])
    if results:
        return results[0]["ObjectID"], results[0]["_ref"]
    return None, None
```

---

## PRD Parsing Strategy

### Feature Grouping

Look for phase/section headings in the PRD markdown:

```python
import re

def extract_features(prd_body):
    """Extract feature groups from PRD markdown."""
    features = []
    # Match headings like: ### P0: Core Prepare + Frontend Wiring
    pattern = r'###\s+(P\d+[a-z]?):\s+(.+)'
    for match in re.finditer(pattern, prd_body):
        phase = match.group(1)
        title = match.group(2).strip()
        features.append({
            "phase": phase,
            "name": f"{phase} — {title}",
            "start_pos": match.start(),
        })
    return features
```

### Story Extraction

Look for numbered items under each feature section:

```python
def extract_stories(prd_body, feature_start, next_feature_start):
    """Extract numbered user stories from a section."""
    section = prd_body[feature_start:next_feature_start]
    stories = []
    # Match: 1. As an **MWT Wellbeing Specialist**, I want...
    pattern = r'(\d+)\.\s+As\s+(?:a|an)\s+\*\*(.+?)\*\*.*?I want\s+(.+?)(?:,\s+so that\s+(.+?))?(?:\n|$)'
    for match in re.finditer(pattern, section, re.DOTALL):
        num = int(match.group(1))
        role = match.group(2)
        want = match.group(3).strip().rstrip('.')
        so_that = match.group(4).strip().rstrip('.') if match.group(4) else ""
        
        # Derive short title from the "I want" clause
        short_title = derive_short_title(want)
        
        stories.append({
            "number": num,
            "name": f"S{num}: {short_title}",
            "role": role,
            "want": want,
            "so_that": so_that,
            "full_text": match.group(0),
        })
    return stories
```

### Description HTML Generation

```python
def build_description_html(story, phase_name):
    return f"""<h3>User Story</h3>
<p>As an <b>{story['role']}</b>, I want {story['want']}, so that {story['so_that']}.</p>

<h3>Phase</h3>
<p>{phase_name}</p>"""
```

### AC Generation Strategy

For each story, generate acceptance criteria from:
1. **Explicit AC in the PRD** (if present under the story)
2. **Implementation decisions section** (extract relevant constraints)
3. **Testing section** (extract test expectations as AC)
4. **Inferred from story text** (the "I want" and "so that" clauses)

Format as structured HTML:
```html
<h3>Acceptance Criteria</h3>
<ul>
<li><b>AC1:</b> When [condition], [expected behavior].</li>
<li><b>AC2:</b> [Data field] includes [specific content] from [source].</li>
<li><b>AC3:</b> When [error condition], [graceful behavior].</li>
</ul>
```

### Task Generation Strategy

Derive tasks from:
1. **"Modules to build" sections** in the PRD
2. **Implementation decisions** (e.g., "Redis cache" → cache tasks)
3. **Testing decisions** (e.g., "unit tests for X" → test tasks)
4. **Standard patterns**: Create toolkit, Implement query, Write unit tests

Typical task count: 4-8 per story.

---

## Repository Classification

Classify each story based on where code changes are needed:

| Indicator | Repo |
|-----------|------|
| API endpoint, toolkit, agent, model, service logic | Backend |
| Next.js route, React component, frontend wiring | UI |
| "Wire frontend button to endpoint" | Both |
| DevOps, observability, health checks | Backend |
| Cache, database, data pipeline | Backend |

Add repo references as HTML appended to the Description field:

```python
def build_repo_reference_html(repos, backend_url, ui_url, issue_url):
    lines = ['<h3>Repository Reference</h3>', '<ul>']
    if "backend" in repos:
        lines.append(f'<li><b>Backend:</b> <a href="{backend_url}">{backend_url.split("/")[-1]}</a></li>')
    if "ui" in repos:
        lines.append(f'<li><b>UI:</b> <a href="{ui_url}">{ui_url.split("/")[-1]}</a></li>')
    lines.append('</ul>')
    lines.append(f'<p><b>PRD Source:</b> <a href="{issue_url}">GitHub Issue</a></p>')
    return '\n'.join(lines)
```

---

## Verification Checklist

After all creates/updates, run a verification pass:

```python
def verify_stories(rally_base, headers, project_ref, feature_ids, expected_count):
    total = 0
    issues = []
    for fid in feature_ids:
        stories = get_stories_by_feature(rally_base, headers, project_ref, fid)
        for s in stories:
            total += 1
            fid_s = s['FormattedID']
            name = s['Name']
            notes = s.get('Notes', '') or ''
            tasks_count = s.get('Tasks', {}).get('Count', 0)
            desc = s.get('Description', '') or ''

            if not notes:
                issues.append(f"{fid_s}: Missing AC in Notes")
            if tasks_count == 0:
                issues.append(f"{fid_s}: No tasks")
            if "Repository Reference" not in desc:
                issues.append(f"{fid_s}: Missing repo reference")

    if total != expected_count:
        issues.insert(0, f"Count mismatch: {total} vs expected {expected_count}")
    return total, issues
```

---

## Execution Order

The recommended execution order for maximum reliability:

1. **Discover fields** — TypeDefinition query to find AC field
2. **Create Features** — one per phase, with 0.5s delays
3. **Create Stories** — under each feature, with 0.3s delays
4. **Write AC** — update Notes field on all stories, with 0.3s delays
5. **Create Tasks** — under each story, check for duplicates, 0.2s delays
6. **Add Repo References** — append to Description, 0.3s delays
7. **Verify** — query everything back and confirm completeness

**Do NOT combine steps 3-5 into a single loop per story.** Creating a story and immediately creating its tasks causes concurrency conflicts on the story object. Batch each operation type separately.

---

## Complete Script Template

For a ready-to-run Python script template, generate it dynamically based on the user's specific PRD content. The script should:

1. Use `requests` library (standard in most Python envs)
2. Accept Rally API key and project OID as variables at the top
3. Define all features, stories, AC, and tasks as data structures
4. Execute in the order: Features → Stories → AC → Tasks → Repo Refs → Verify
5. Print a summary table at the end
6. Handle all concurrency errors with retries
7. Be idempotent (check for existing items before creating)
