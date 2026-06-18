# Rally Integration — Reference

Deep knowledge for Broadcom Rally (CA Agile Central) WSAPI v2.0 integration.

## Endpoints & base URL

- **Host**: `https://rally1.rallydev.com` (on-prem instances differ — ask the user).
- **WSAPI base path**: `/slm/webservice/v2.0`
- **OAuth2 token**: `https://rally1.rallydev.com/login/oauth2/token`

Full object endpoints (append to WSAPI base):

| Object | Path |
|---|---|
| Feature (Portfolio Item) | `/portfolioitem/feature` |
| Epic / higher PIs | `/portfolioitem/epic`, `/portfolioitem/<type>` |
| User Story | `/hierarchicalrequirement` |
| Task | `/task` |
| Defect | `/defect` |
| Project | `/project` |
| Iteration | `/iteration` |
| Release | `/release` |

## Authentication options

Rally supports three mechanisms. Support the first two; the third is interactive and rarely
needed for backend services.

### 1. OAuth2 client credentials (machine-to-machine — preferred)
```
POST https://rally1.rallydev.com/login/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=<id>&client_secret=<secret>
```
Response: `{ "access_token": "...", "expires_in": 3600 }`. Cache the token and refresh
~60s before expiry. Send as `Authorization: Bearer <access_token>`.

### 2. API key / static bearer token (zsession key)
A long-lived key created in Rally under "API Keys". Send as `Authorization: Bearer <key>`
(or `ZSESSIONID` header on older instances). If present, skip the OAuth2 flow entirely.

### 3. OAuth2 authorization code (interactive — the practical path for ad-hoc work)
Requires a browser login. **Avoid for unattended backend services** (it can't refresh silently),
but it is the **correct and confirmed-working path for one-off reports and CRUD** against
browser-login tenants where client_credentials is disabled.

Flow:
1. **Authorize** — send the user to:
   ```
   https://rally1.rallydev.com/login/oauth2/auth
     ?response_type=code
     &client_id=<id>
     &redirect_uri=<EXACT registered URI, e.g. https://localhost:3000/callbace>
     &scope=alm
   ```
   - `scope=alm` is **required** (omitting it → `invalid_scope`).
   - `redirect_uri` must match the registered value **exactly**, including the path.
2. **Capture the code** — the browser redirects to `<redirect_uri>?code=XXXX`. A self-signed
   `https://localhost` listener works, but browsers won't auto-post through a self-signed cert,
   so the simplest reliable method is: **user copies the `code` from the address bar**.
3. **Exchange** — single-use code → token:
   ```
   POST https://rally1.rallydev.com/login/oauth2/token
   grant_type=authorization_code&code=<XXXX>&redirect_uri=<same URI>
     &client_id=<id>&client_secret=<secret>
   ```
   Response: `{ "access_token": "...", "expires_in": 3600 }`.
4. **Cache the token** (e.g. `rally_token.txt`) and reuse it for every subsequent call. The
   **auth code is consumed on first exchange** — re-running the exchange returns
   `400 code_not_found`. Caching avoids forcing the user through the browser repeatedly.

**Precedence rule**: if a static token/API key is configured, use it and never call the token
endpoint. Otherwise, for services use client_credentials; for ad-hoc work use authorization_code.

> **Real-world notes (observed in production):**
> - `grant_type=client_credentials` returned `HTTP 400` ("must be `authorization_code`") on a
>   rally1.rallydev.com tenant configured as a browser-login app. **`authorization_code` worked.**
> - The same tenant also accepts **API keys** (Rally → user menu → API Keys) as a static bearer
>   token — preferred for unattended services.
> - Always run `scripts/verify_rally.py` (API key path) or `scripts/rally_ops.py auth-url`
>   (authorization_code path) to confirm which works before building further.

## WSAPI query language

- Queries are URL-encoded strings in the `query` param.
- **Binary operators only** — every condition is `(A op B)`. Combine with `AND` / `OR`, each
  pair wrapped in parens: `((A = "x") OR (B = "y"))`.
- **Nested fields use dot paths**: `State.Name`, `Project.Name`, `Owner.UserName`.
- Operators: `=`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `!contains`.
- String values in double quotes. `contains` is case-insensitive substring.

Key params:

| Param | Purpose |
|---|---|
| `query` | filter expression (URL-encoded) |
| `fetch` | comma list of fields to return (e.g. `FormattedID,Name,Description,State`); `fetch=true` returns all |
| `pagesize` | results per page, **max 200** |
| `start` | 1-based offset for pagination |
| `order` | sort field, e.g. `FormattedID` or `CreationDate desc` |
| `project` | project ref URL to scope to |
| `projectScopeDown` | `true` to include child projects (REQUIRED with `project` for subtree) |
| `projectScopeUp` | `true` to include parent projects |

## Response shape

```json
{
  "QueryResult": {
    "TotalResultCount": 81,
    "Results": [
      {
        "FormattedID": "F12345",
        "Name": "...",
        "Description": "<p>HTML…</p>",
        "State": { "_refObjectName": "In Progress", "_ref": "...", "Name": "In Progress" }
      }
    ]
  }
}
```

- **`State` (and other typed fields) come back as objects**, not strings. Read
  `_refObjectName` (or `Name`). Defensive helper:
  ```python
  def state_name(v):
      return v.get("_refObjectName") or v.get("Name") or "" if isinstance(v, dict) else (v or "")
  ```
- A single-object GET via query still returns a `Results` array — take `[0]`.
- Errors come as `{ "QueryResult": { "Errors": [...], "Warnings": [...] } }` with HTTP 200.
  **Always check `Errors`** even on 200.

## Writes — create & update (stories, tasks, fields)

All writes are JSON POSTs with `Content-Type: application/json`. The body is wrapped in the
object type name. **Always check the result envelope for `Errors`** even on HTTP 200.

### Create a User Story
```
POST {base}/hierarchicalrequirement/create
{
  "HierarchicalRequirement": {
    "Name": "S99: ...",
    "Description": "<p>HTML…</p>",
    "Project": "<project _ref>",
    "PortfolioItem": "<feature _ref>",      // links story to a Feature (F-id)
    "Iteration": "<iteration _ref>",         // optional; omit/null = backlog
    "Owner": "<user _ref>"
  }
}
→ { "CreateResult": { "Object": { "FormattedID": "US123", "_ref": "..." }, "Errors": [], "Warnings": [] } }
```

### Create a Task under a story
```
POST {base}/task/create
{
  "Task": {
    "Name": "...",
    "WorkProduct": "<story _ref>",   // the parent story/defect
    "Owner": "<user _ref>",
    "Estimate": 4.0,
    "Project": "<project _ref>"
  }
}
```

### Update a field on an existing object
POST to the object's own `_ref` (not `/create`) with just the fields to change:
```
POST <object _ref>
{ "HierarchicalRequirement": { "ScheduleState": "In-Progress" } }
→ { "OperationResult": { "Errors": [], "Warnings": [] } }
```

### Move a story between iterations / to backlog
```
POST <story _ref>
{ "HierarchicalRequirement": { "Iteration": "<iteration _ref or null>" } }
```
`null` sends it to the backlog. Only mutate stories actually in the source iteration — fetch
`Iteration` first and compare names (they're long: `2026 Iteration 13 (6/17 to 6/30)`).

### Acceptance Criteria field
AC is **not** the Description — it's a dedicated field, on most tenants the custom field
**`c_AcceptanceCriteria`**. Discover the exact element name from the type definition:
```
GET {base}/typedefinition?query=(ElementName = "HierarchicalRequirement")&fetch=Attributes
→ follow Attributes._ref, look for ElementName/Name containing "accept"
```
If discovery returns no candidates (custom fields aren't always enumerated), **fall back to
`c_AcceptanceCriteria`** and **read it back** to confirm it persisted — Rally silently accepts
(and drops) unknown fields, so a 200 alone does NOT prove the write took:
```
POST <story _ref>  { "HierarchicalRequirement": { "c_AcceptanceCriteria": "<p>…</p>" } }
GET  {base}/hierarchicalrequirement?query=(FormattedID="US123")&fetch=c_AcceptanceCriteria
```

### Resolving Owner (users) — case-sensitive!
`=` matches are **case-sensitive**. `(EmailAddress = "Susan.Xu@optum.com")` returns nothing if
Rally stored `susan.xu@optum.com`. Strategy:
1. Try `(EmailAddress = "<as given>")`, then `(UserName = "<as given>")`.
2. On miss, search broadly: `(DisplayName contains "<surname>")`,
   `(EmailAddress contains "<token>")`, `(LastName = "<surname>")` — show matches, pick the ref.
3. Never invent an email. If ambiguous, ask the user.

### Resolving Iterations
```
GET {base}/iteration?query=(Name = "2026 Iteration 13 (6/17 to 6/30)")
   &project=<ref>&projectScopeUp=true&projectScopeDown=true&fetch=Name,_ref
```
Names are long and exact. To find "the current sprint", either ask the user for the exact name
or query by date window (`((StartDate <= "<today>") AND (EndDate >= "<today>"))`).

### Concurrency conflicts on bulk task creation
Creating several Tasks immediately after creating their parent story can return:
`Concurrency conflict: Object has been modified since being read for update`. This is transient
— **retry the failed create 2–4×**. `scripts/rally_ops.py` retries automatically.

## Project scoping (the #1 source of confusion)

To restrict features to a project **and all its sub-projects**:
```
?query=...&project=https://rally1.rallydev.com/slm/webservice/v2.0/project/779298915037&projectScopeDown=true
```

Resolve a human project name to its ref **once**, then cache it:
```
GET /project?query=(Name = "OCM - Implementation")&fetch=Name,_ref&pagesize=1
→ Results[0]._ref
```
Project names must match **exactly** (case + spacing). To discover the right name, query
`(Name contains "OCM")` and show the user the matches. An unmatched name returns data
**unscoped** — log a warning so it's not mistaken for "no results".

## HTML descriptions

Rally `Description`, `Notes`, and discussion fields are HTML. Convert before storing or
feeding to an LLM:
```python
from markdownify import markdownify
md = markdownify(html, heading_style="ATX", strip=["img"]).strip()
```

## SSL verification

Corporate networks with TLS inspection may break cert validation. Provide a
`RALLY_SSL_VERIFY` flag (default `True`). When `False`, pass `verify=False` to the HTTP
client and **log a warning every time** so it's never silently insecure in production.

## Base URL normalization

Users paste base URLs inconsistently. Guard against a doubled WSAPI suffix:
```python
WSAPI = "/slm/webservice/v2.0"
base = configured.rstrip("/")
if base.endswith(WSAPI):
    base = base.removesuffix(WSAPI)
url = f"{base}{WSAPI}{path}"
```

## Persistence

Store Rally linkage on your existing entity (1:1 — no separate table needed):

| Column | Type | Notes |
|---|---|---|
| `rally_feature_id` | string, **unique**, indexed | e.g. `F12345` |
| `rally_state` | string nullable | last-known Rally state |
| `rally_last_synced_at` | datetime nullable | refresh timestamp |
| `deleted_at` | datetime nullable | **soft delete** |

**Soft delete**: set `deleted_at` instead of removing the row. All list queries filter
`WHERE deleted_at IS NULL`. Re-importing the same `rally_feature_id` reactivates the record
(`deleted_at = NULL`), preserving downstream data. Rationale in ADR-0005 below.

**Import is best-effort**: always create/reactivate the record even if optional post-processing
(e.g. LLM parsing) fails — return a `partial` status rather than aborting.

**Sync vs import**: a *sync* refreshes only `name` + `rally_state` (+ timestamp) and must
**never** overwrite user-edited downstream content. A full re-import replaces the source doc.

## Config / env vars

```
RALLY_BASE_URL=https://rally1.rallydev.com/slm/webservice/v2.0
RALLY_AUTH_URL=https://rally1.rallydev.com/login/oauth2/token
RALLY_CLIENT_ID=<id>                 # OAuth2 path
RALLY_CLIENT_SECRET=<secret>         # OAuth2 path  (SECRET)
RALLY_API_KEY=                       # alternative to client_id/secret (SECRET)
RALLY_PROJECT_NAME=OCM - Implementation   # human name (auto-resolved)
RALLY_PROJECT_REF=                   # raw project ref URL (overrides NAME)
RALLY_SSL_VERIFY=true
```

An `enabled` flag should be true when base URL + (client_id OR api_key) are present.

## Deployment

Push the **same env vars as platform app settings**. For Azure App Service:
```bash
az webapp config appsettings set --name <app> --resource-group <rg> \
  --settings RALLY_PROJECT_NAME="OCM - Implementation" RALLY_SSL_VERIFY=false ...
```
Mark secrets (`RALLY_CLIENT_SECRET`, `RALLY_API_KEY`) as secure parameters in IaC
(ARM `securestring`, Terraform `sensitive`). After deploy, validate the live list endpoint
returns the **same count** you saw locally from `verify_rally.py`.

**Gotcha seen in production**: an App Service pinned to an old image tag (`:v4`) served stale
code and 404'd new routes. Pin to `:latest` (or a fresh digest) and restart after each build.

## Common errors → fixes

| Symptom | Cause | Fix |
|---|---|---|
| Exactly 200 results | `pagesize` cap hit | scope to a project or paginate with `start` |
| Returns ALL features despite project set | name didn't match / missing `projectScopeDown` | verify exact name; add `projectScopeDown=true` |
| `Could not parse: State` | filtered on `State` not `State.Name` | use the nested path |
| 401 / token errors | wrong client creds or expired token | check secret; ensure refresh logic |
| `400 Bad Request` on token endpoint | tenant only allows API keys | use an API key / bearer token instead of client-credentials |
| SSL `CERTIFICATE_VERIFY_FAILED` | corp TLS inspection | set `RALLY_SSL_VERIFY=false` (log it) |
| HTTP 200 but empty `Results` + `Errors` | malformed query | inspect `QueryResult.Errors` |
| `400 code_not_found` on token endpoint | auth code already used (single-use) or expired | get a fresh code; cache the token so you exchange only once |
| `invalid_scope` on `/auth` | missing `scope=alm` | add `scope=alm` to the authorize URL |
| `invalid_redirect_uri` on `/auth` | URI not registered / path mismatch | use the EXACT registered `redirect_uri` (path included) |
| AC field write "succeeds" but stays empty | wrong/unknown field name silently dropped | use `c_AcceptanceCriteria`; read the field back to verify |
| `Concurrency conflict ... modified since read` | task created too fast after parent story | retry the create 2–4× |
| User query returns nothing | `=` is case-sensitive | retry lowercase, or `contains` on DisplayName/Email |
| Routes 404 after deploy | stale container image | rebuild + repin tag + restart |

## ADR-0005 (decisions carried from the source project)

- **Nullable columns on the entity** over a separate `RallyFeatureLink` table — it's 1:1.
- **Soft delete** over hard delete — preserves sessions/history; re-import reactivates.
- **OAuth2 client credentials** over authorization code **for unattended services**; for
  **ad-hoc reports/CRUD** the authorization_code flow (or an API key) is the working path on
  browser-login tenants. Cache the token so the single-use code is exchanged only once.
- **Single project scope** via env var — multi-project deferred; covers the common case.
- **Best-effort import** — workspace always created even if LLM/parse steps fail.
