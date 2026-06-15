---
name: rally-integration
description: Integrate Broadcom Rally (CA Agile Central) into any app — authenticate via WSAPI v2.0, fetch Portfolio Item Features / User Stories, scope queries to a project and its children, and import them as local records. Use when the user wants to connect to Rally, import Rally features/stories, configure Rally OAuth or API keys, scope to a Rally project, debug Rally WSAPI queries, or deploy a Rally integration. Trigger phrases: "Rally integration", "import from Rally", "connect to Rally", "Rally WSAPI", "Rally features", "Rally project scope", "rally1.rallydev.com".
---

# Rally Integration

End-to-end guide for wiring Broadcom Rally (rally1.rallydev.com) into an application,
distilled from a production FastAPI integration. Follow the workflow; pull exact code
from [templates/](templates/) and deep WSAPI knowledge from [REFERENCE.md](REFERENCE.md).

## What you provide vs. what the user provides

**The skill provides everything** — auth flow, WSAPI query syntax, project scoping,
HTML→Markdown, caching, error handling, deploy config.

**Ask the user only for secrets/identifiers** (never invent these):
- Rally base URL (default `https://rally1.rallydev.com/slm/webservice/v2.0`)
- Auth: **either** `client_id` + `client_secret` (OAuth2) **or** an API key / bearer token
- Project to scope to: a human name (e.g. `OCM - Implementation`) or a project ref URL
- Whether SSL verification must be disabled (corporate proxy/MITM)

Collect these with the ask-questions tool, then write them to `.env` — never hardcode.

## Workflow

1. **Gather inputs** — ask the user for the values above. Don't proceed without auth + base URL.
2. **Verify connectivity first** — run [scripts/verify_rally.py](scripts/verify_rally.py)
   with the user's values. It authenticates, resolves the project, and prints a feature
   count. This eliminates trial-and-error. Do this BEFORE writing app code.
3. **Add config** — env vars + a settings object. See [templates/config.py](templates/config.py).
4. **Add the WSAPI client** — copy [templates/rally_service.py](templates/rally_service.py).
   It handles auth caching, project resolution, pagination, state parsing, HTML→Markdown.
5. **Wire into the app** — list / import / sync endpoints. See [templates/api_routes.py](templates/api_routes.py).
6. **Persist** — store `rally_feature_id` (unique), `rally_state`, `rally_last_synced_at`.
   Prefer soft delete so re-import reactivates. See [REFERENCE.md](REFERENCE.md#persistence).
7. **Deploy** — push the same env vars as platform settings. See [REFERENCE.md](REFERENCE.md#deployment).
8. **Validate live** — hit your list endpoint and confirm the feature count matches step 2.

## Critical gotchas (these caused real trial-and-error)

- **`State` is a nested object**, not a string. Filter with `(State.Name = "In Progress")`,
  not `(State = ...)`. When reading results, `State` may be a dict (`_refObjectName`/`Name`).
- **`pagesize` max is 200.** If you get exactly 200, you're likely capped — paginate or scope down.
- **Project scoping needs BOTH** `project=<ref>` AND `projectScopeDown=true` to include child projects.
- **Resolve project name → ref once** via `/project?query=(Name = "...")`, then cache it.
  An unfound name silently returns everything unscoped — log a warning.
- **Base URL double-suffix**: if the configured base already ends in `/slm/webservice/v2.0`,
  don't append it again. Strip then re-add.
- **Corporate networks** often need `verify=False` on the HTTP client. Make it a config flag,
  default `True`, and log loudly when disabled.
- **Auth precedence**: a static bearer token / API key short-circuits the OAuth2 client-credentials
  flow. Support both; prefer the token if present.
- **OAuth2 may 400 even with valid creds** — some tenants only enable API keys. If the token
  endpoint returns `400 Bad Request`, switch to an API key. (Confirmed in production.)
- **Descriptions are HTML** — convert to Markdown (`markdownify`) before storing or LLM ingestion.

## Quick reference

| Need | Endpoint / param |
|---|---|
| Features (Portfolio Items) | `/portfolioitem/feature` |
| User Stories | `/hierarchicalrequirement` |
| Projects | `/project` |
| Single item by ID | `query=(FormattedID = "F12345")` |
| Fields to return | `fetch=FormattedID,Name,Description,State` |
| Scope to project + children | `project=<ref>&projectScopeDown=true` |
| OAuth2 token | POST `/login/oauth2/token` grant_type=client_credentials |

See [REFERENCE.md](REFERENCE.md) for full WSAPI query language, auth options, response shapes,
persistence schema, and deployment notes.
