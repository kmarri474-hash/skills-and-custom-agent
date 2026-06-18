---
name: rally-integration
description: Integrate Broadcom Rally (CA Agile Central) into any app OR do ad-hoc Rally work — authenticate via WSAPI v2.0, pull reports (features/stories/tasks), create & update stories/tasks, set Acceptance Criteria, move items between iterations, and scope queries to a project and its children. Use when the user wants to connect to Rally, import/pull Rally features/stories, create stories or tasks, set acceptance criteria, move stories between sprints/iterations, configure Rally OAuth or API keys, scope to a Rally project, debug Rally WSAPI queries, or deploy a Rally integration. Trigger phrases: "Rally", "Rally integration", "import from Rally", "pull Rally report", "create Rally story", "create story/task", "acceptance criteria", "move to iteration", "connect to Rally", "Rally WSAPI", "rally1.rallydev.com".
---

# Rally Integration

End-to-end guide for working with Broadcom Rally (rally1.rallydev.com) — both **building an
integration** into an app AND doing **ad-hoc operations** (reports, creating/updating stories
and tasks, setting acceptance criteria, moving items between iterations). Follow the workflow;
pull exact code from [templates/](templates/), ready-to-run scripts from [scripts/](scripts/),
and deep WSAPI knowledge from [REFERENCE.md](REFERENCE.md).

## Two modes

- **App integration** (persistent service) — prefer an **API key** for unattended auth. Follow
  the "App integration workflow" below.
- **Ad-hoc operations** (one-off reports / CRUD from your machine) — use the **OAuth2
  authorization_code** flow with [scripts/rally_ops.py](scripts/rally_ops.py). See
  "Operations workflow".

## What you provide vs. what the user provides

**The skill provides everything** — auth flow, WSAPI query syntax, project scoping,
HTML→Markdown, caching, error handling, deploy config.

**Ask the user only for secrets/identifiers** (never invent these):
- Rally base URL (default `https://rally1.rallydev.com/slm/webservice/v2.0`)
- Auth: **either** an API key / bearer token **or** `client_id` + `client_secret` (OAuth2)
- Project to scope to: a human name (e.g. `OCM - Implementation`) or a project ref URL
- Whether SSL verification must be disabled (corporate proxy/MITM)
- For writes: the target **Owner** (email/username), **Iteration** name, parent **Feature** ID

Collect these with the ask-questions tool, then write them to `.env` — never hardcode.

## App integration workflow

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

## Operations workflow (ad-hoc reports & CRUD)

For one-off work — pull a report, create stories/tasks, set Acceptance Criteria, move items
between iterations — use [scripts/rally_ops.py](scripts/rally_ops.py). It handles the
OAuth2 **authorization_code** flow, **token caching**, project/iteration/owner resolution,
pagination, writes, and concurrency-conflict retries.

1. **Put creds in `.env`**: `RALLY_CLIENT_ID`, `RALLY_CLIENT_SECRET`, and the exact registered
   `RALLY_REDIRECT_URI` (e.g. `https://localhost:3000/callbace`). Confirm `.env` is gitignored.
2. **Get an auth code** — print the auth URL and have the user log in:
   ```
   python scripts/rally_ops.py auth-url
   ```
   The browser redirects to `<redirect_uri>?code=XXXX`. The page may fail to load (self-signed
   localhost) — that's fine; the user copies the `code` value from the address bar.
3. **Run the operation** — the code is **single-use**, so the script caches the token in
   `rally_token.txt` and reuses it for every subsequent call until it expires (~1h):
   ```
   python scripts/rally_ops.py --code XXXX report  --project "CM | Team Nebula" --kind feature
   python scripts/rally_ops.py             report  --feature F1852252 --kind story
   python scripts/rally_ops.py             create-story --feature F1852252 \
       --name "..." --owner user@optum.com --iteration "2026 Iteration 13 (6/17 to 6/30)" \
       --description-file body.html --tasks-file tasks.json
   python scripts/rally_ops.py             set-ac --story US10684787 --ac-file ac.html
   python scripts/rally_ops.py             move-iteration --story US10552982 --to "" 
   python scripts/rally_ops.py             find-user --name "Xu"
   ```
4. **Clean up** — delete `rally_ops.py`-generated temp files (`rally_token.txt`, any
   `*.json`/`*.html` you created) and **remove the consumed `RALLY_AUTH_CODE`** from `.env`.

### Write-operation rules (IMPORTANT)
- **Writes are hard to reverse.** Before creating/updating in bulk, **list what will change and
  confirm with the user** (use the ask-questions tool for destination/scope).
- **Acceptance Criteria lives in a dedicated field**, not Description. On most tenants it's the
  custom field **`c_AcceptanceCriteria`** (confirmed). Discover it via the type definition; if
  discovery returns nothing, fall back to `c_AcceptanceCriteria` and **read the field back to
  verify it persisted** (Rally silently ignores unknown fields). Treat AC as a must-have field
  for every story you create.
- **User lookup is case-sensitive** for `=`. `(EmailAddress = "Susan.Xu@...")` can miss a
  record stored lowercase. Use `find-user` (which tries `contains` on DisplayName/Email) when an
  exact match fails — never guess an email.
- **Iteration names are long and exact** (e.g. `2026 Iteration 13 (6/17 to 6/30)`, not
  `Iteration 13`). Resolve by listing iterations or use a `contains`/word-boundary match; verify
  before mutating.
- **Concurrency conflicts** (`Object has been modified since being read`) happen when creating
  several Tasks under a freshly-created story. **Retry the failed create 2–4×** — `rally_ops.py`
  does this automatically.
- **To move a story out of an iteration**, set `Iteration` to `null` (backlog) or to another
  iteration's ref. Only touch items actually in the source iteration.

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
- **Auth precedence**: a static bearer token / API key short-circuits any OAuth2 flow.
  Support all; prefer the API key for unattended services.
- **OAuth2 client_credentials may 400** — many tenants are browser-login apps and only enable
  `authorization_code` (or API keys). If client_credentials returns `400` ("must be
  authorization_code"), either use an **API key** (services) or the **authorization_code** flow
  (ad-hoc, via `scripts/rally_ops.py`). Both are confirmed working in production.
- **authorization_code REQUIRES `scope=alm`** on the `/login/oauth2/auth` request, and the
  `redirect_uri` must **exactly** match the one registered on the OAuth app (path included, e.g.
  `/callbace`). A self-signed `https://localhost` callback works, but the browser can't auto-post
  the code — have the user copy it from the address bar.
- **Descriptions are HTML** — convert to Markdown (`markdownify`) before storing or LLM ingestion.
- **Acceptance Criteria is a separate custom field** (`c_AcceptanceCriteria`), not Description.
  Always set it on stories you create, then read it back to confirm it saved.

## Quick reference

| Need | Endpoint / param |
|---|---|
| Features (Portfolio Items) | `/portfolioitem/feature` |
| User Stories | `/hierarchicalrequirement` |
| Tasks | `/task` |
| Projects | `/project` |
| Iterations | `/iteration` |
| Users | `/user` |
| Single item by ID | `query=(FormattedID = "F12345")` |
| Fields to return | `fetch=FormattedID,Name,Description,State` |
| Scope to project + children | `project=<ref>&projectScopeDown=true` |
| Create story | POST `/hierarchicalrequirement/create` body `{"HierarchicalRequirement": {...}}` |
| Create task under story | POST `/task/create` with `WorkProduct=<story _ref>` |
| Update a field | POST to the object `_ref` with `{"<Type>": {"Field": value}}` |
| Acceptance Criteria field | `c_AcceptanceCriteria` (custom; verify via typedefinition) |
| Move story to backlog | POST story `_ref` with `{"HierarchicalRequirement": {"Iteration": null}}` |
| OAuth2 token (ad-hoc) | POST `/login/oauth2/token` grant_type=authorization_code (needs `scope=alm` on auth) |
| OAuth2 token (service) | API key as `Authorization: Bearer <key>` (no token call) |

See [REFERENCE.md](REFERENCE.md) for full WSAPI query language, auth options, response shapes,
persistence schema, and deployment notes.
