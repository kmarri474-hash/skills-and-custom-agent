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

### 3. OAuth2 authorization code (interactive)
Requires a browser redirect login. **Avoid for backend services** — it can't run unattended.
We explicitly rejected this in ADR-0005.

**Precedence rule**: if a static token/API key is configured, use it and never call the token
endpoint. Otherwise run client-credentials and cache.

> **Real-world note (observed in production):** the OAuth2 client-credentials grant returned
> `HTTP 400 Bad Request` on a rally1.rallydev.com tenant where only **API keys** were enabled,
> even with valid-looking `client_id`/`client_secret`. The **API key / static bearer token path
> worked immediately.** If client-credentials 400s, ask the user for a Rally **API Key**
> (Rally → user menu → API Keys) and use the token path — don't burn time debugging the OAuth2
> grant. Always run `scripts/verify_rally.py` to confirm which path works before writing app code.

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
| Routes 404 after deploy | stale container image | rebuild + repin tag + restart |

## ADR-0005 (decisions carried from the source project)

- **Nullable columns on the entity** over a separate `RallyFeatureLink` table — it's 1:1.
- **Soft delete** over hard delete — preserves sessions/history; re-import reactivates.
- **OAuth2 client credentials** over authorization code — works unattended for backends.
- **Single project scope** via env var — multi-project deferred; covers the common case.
- **Best-effort import** — workspace always created even if LLM/parse steps fail.
