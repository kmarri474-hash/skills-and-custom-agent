"""Rally WSAPI v2.0 client (async, httpx).

Battle-tested patterns: token caching, project-name resolution + caching,
nested-state parsing, base-URL normalization, SSL flag, HTML->Markdown.

Depends on: httpx, markdownify, and a `settings` object exposing the fields in config.py.
"""

import logging
import time

import httpx
from markdownify import markdownify

from app.core.config import settings  # adapt import path

logger = logging.getLogger(__name__)

WSAPI_BASE = "/slm/webservice/v2.0"

_token_cache: dict = {"access_token": None, "expires_at": 0.0}
_project_ref_cache: dict = {"ref": None}


def _rally_base_url() -> str:
    base = settings.RALLY_BASE_URL.rstrip("/")
    return base.removesuffix(WSAPI_BASE) if base.endswith(WSAPI_BASE) else base


def _http_client() -> httpx.AsyncClient:
    if not settings.RALLY_SSL_VERIFY:
        logger.warning("Rally SSL certificate verification is disabled")
    return httpx.AsyncClient(timeout=30, verify=settings.RALLY_SSL_VERIFY)


async def _get_access_token() -> str:
    # Static token short-circuits the OAuth2 flow.
    if settings.rally_bearer_token:
        return settings.rally_bearer_token

    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    async with _http_client() as client:
        resp = await client.post(
            settings.RALLY_AUTH_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.RALLY_CLIENT_ID,
                "client_secret": settings.RALLY_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()

    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)
    logger.info("Rally access token refreshed")
    return _token_cache["access_token"]


async def _rally_get(path: str, params: dict | None = None) -> dict:
    token = await _get_access_token()
    url = f"{_rally_base_url()}{WSAPI_BASE}{path}"
    async with _http_client() as client:
        resp = await client.get(
            url, params=params,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
    # WSAPI returns HTTP 200 even on query errors — surface them.
    errors = data.get("QueryResult", {}).get("Errors") or data.get("OperationResult", {}).get("Errors")
    if errors:
        raise httpx.HTTPError(f"Rally WSAPI error: {errors}")
    return data


def _state_name(state_field) -> str:
    if isinstance(state_field, dict):
        return state_field.get("_refObjectName") or state_field.get("Name") or ""
    return state_field or ""


async def _resolve_project_ref() -> str | None:
    """REF wins; else resolve NAME once and cache; else None (unscoped)."""
    if settings.RALLY_PROJECT_REF:
        return settings.RALLY_PROJECT_REF
    if not settings.RALLY_PROJECT_NAME:
        return None
    if _project_ref_cache["ref"]:
        return _project_ref_cache["ref"]

    data = await _rally_get("/project", params={
        "query": f'(Name = "{settings.RALLY_PROJECT_NAME}")',
        "fetch": "Name,_ref", "pagesize": 1,
    })
    results = data.get("QueryResult", {}).get("Results", [])
    if not results:
        logger.warning("Rally project %r not found — features will be UNSCOPED",
                       settings.RALLY_PROJECT_NAME)
        return None
    ref = results[0].get("_ref", "")
    _project_ref_cache["ref"] = ref
    logger.info("Resolved Rally project %r -> %s", settings.RALLY_PROJECT_NAME, ref)
    return ref


def _to_record(item: dict) -> dict:
    return {
        "formatted_id": item.get("FormattedID", ""),
        "name": item.get("Name", ""),
        "state": _state_name(item.get("State", "")),
        "description": item.get("Description", "") or "",
    }


async def list_features(states=("Defined", "In Progress")) -> list[dict]:
    """Features in the given states, scoped to the configured project + children."""
    state_q = " OR ".join(f'(State.Name = "{s}")' for s in states)
    params: dict = {
        "query": f"({state_q})",
        "fetch": "FormattedID,Name,Description,State",
        "pagesize": 200, "order": "FormattedID",
    }
    ref = await _resolve_project_ref()
    if ref:
        params["project"] = ref
        params["projectScopeDown"] = "true"  # include child projects

    data = await _rally_get("/portfolioitem/feature", params)
    return [_to_record(i) for i in data.get("QueryResult", {}).get("Results", [])]


async def get_feature(formatted_id: str) -> dict | None:
    """Single Feature by FormattedID (e.g. 'F12345')."""
    params: dict = {
        "query": f'(FormattedID = "{formatted_id}")',
        "fetch": "FormattedID,Name,Description,State", "pagesize": 1,
    }
    ref = await _resolve_project_ref()
    if ref:
        params["project"] = ref
    data = await _rally_get("/portfolioitem/feature", params)
    results = data.get("QueryResult", {}).get("Results", [])
    return _to_record(results[0]) if results else None


def html_to_markdown(html: str) -> str:
    """Rally Description/Notes are HTML — convert before storing or LLM ingestion."""
    if not html or not html.strip():
        return ""
    return markdownify(html, heading_style="ATX", strip=["img"]).strip()
