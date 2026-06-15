---
name: rally-to-prd
description: 'Fetch a Rally user story by ID and generate a complete PRD document. Use when user says "get story", "rally story", "fetch user story", "generate PRD from rally", "US number", or provides a Rally URL. Requires story number and OAuth token (via interactive browser flow) from user.'
argument-hint: 'Rally story number (e.g., 846732192647) or full Rally URL'
---

# Rally Story to PRD

## Workflow

### 1. Collect Inputs

Ask the user for (skip any already provided):

- **Story ID** — the numeric object ID (from URL path `/userstory/<ID>/`) or FormattedID (e.g., US10352106)
- **Rally OAuth Token** — obtained via interactive browser login (see step 2 below)

### 2. Get OAuth Token

Personal API keys are blocked. Run this interactively to get a token:

```python
import requests, urllib.parse, sys

CLIENT_ID     = "<your-rally-client-id>"      # ask the user — never hardcode
CLIENT_SECRET = "<your-rally-client-secret>"  # ask the user — never hardcode
REDIRECT_URI  = "https://localhost:4200"

auth_url = (
    "https://rally1.rallydev.com/login/oauth2/auth"
    f"?client_id={CLIENT_ID}&response_type=code"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}&scope=alm"
)
print(auth_url)  # open in browser, log in
auth_code = input("Paste code from redirect URL: ").strip()
token_r = requests.post("https://rally1.rallydev.com/login/oauth2/token", data={
    "grant_type": "authorization_code", "code": auth_code,
    "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "redirect_uri": REDIRECT_URI,
}, timeout=30)
TOKEN = token_r.json()["access_token"]
```

### 3. Fetch Story Data

Run these API calls sequentially via `curl` in the terminal (set `TOKEN` from step 2):

```bash
# Primary story fields
curl -s -H "zsessionid: $TOKEN" \
  "https://rally1.rallydev.com/slm/webservice/v2.0/hierarchicalrequirement/<STORY_ID>?fetch=Name,Description,Notes,FormattedID,ScheduleState,PlanEstimate,Blocked,BlockedReason,Iteration,Release,Owner,Project,Tags,Parent,Feature,PortfolioItem,c_AcceptanceCriteria,Priority,Package,TestCaseCount,DefectCount"

# Tasks under the story
curl -s -H "zsessionid: $TOKEN" \
  "https://rally1.rallydev.com/slm/webservice/v2.0/hierarchicalrequirement/<STORY_ID>/Tasks?fetch=Name,Description,State,Owner,Estimate,ToDo"

# Children (if DirectChildrenCount > 0)
curl -s -H "zsessionid: $TOKEN" \
  "https://rally1.rallydev.com/slm/webservice/v2.0/hierarchicalrequirement/<STORY_ID>/Children?fetch=Name,FormattedID,ScheduleState,Owner"
```

> **Type name**: Always use `hierarchicalrequirement` — NOT `userstory`.

### 3. Check for Design Assets

Scan the response for:
- Image references (`<img src="/slm/attachment/...">`)
- Figma links (`figma.com/...`)
- SharePoint/external links

If found, **ask the user**:
- "I found a design attachment/link: [URL]. Can you describe what it shows, or paste the image here so I can incorporate it into the PRD?"
- Do NOT attempt to fetch Rally attachments directly (auth-gated binary).

### 4. Generate PRD Document

Produce a markdown document with these sections:

```markdown
# <FormattedID> — <Story Name>

## Metadata
| Field | Value |
|---|---|
| Story ID | ... |
| Status | ... |
| Sprint | ... |
| Points | ... |
| Owner | ... |
| Project | ... |
| Parent Feature | ... |

## User Story
> As a [role], I want [goal] so that [benefit].
(extracted from Description)

## Context
Where this story fits in the feature hierarchy and why it matters.

## Acceptance Criteria
(from c_AcceptanceCriteria — convert HTML to markdown GIVEN/WHEN/THEN format)

## Tasks
(list tasks with state and owner, if any)

## Business Rules
Table of key rules derived from AC and description.

## Design References
Links/descriptions of UI mockups, Figma, workflows.

## Implementation Notes
Developer-oriented guidance inferred from the requirements.

## Open Questions
Ambiguities, missing info, or items needing PO clarification.
```

### 5. Save Location

Save as `docs/<FormattedID>-requirements.md` in the workspace root. If no `docs/` folder exists, create it.

## Notes

- HTML entities in Rally responses (`\u003Cp\u003E`) are Unicode-escaped HTML — decode and convert to clean markdown.
- If the story has a parent Feature, include relevant context from the feature description/AC to give developers broader understanding.
- Keep the PRD actionable — focus on what to build, not process history.
