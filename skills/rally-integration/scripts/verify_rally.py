#!/usr/bin/env python3
"""Verify Rally connectivity BEFORE writing any app code.

Authenticates, optionally resolves a project by name, and prints a feature count.
Run this first to eliminate trial-and-error. Stdlib only (uses urllib) — no installs.

Usage:
  # OAuth2 client credentials
  python verify_rally.py \
    --client-id <id> --client-secret <secret> \
    --project-name "OCM - Implementation"

  # Static API key / bearer token
  python verify_rally.py \
    --api-key <key> \
    --project-ref "https://rally1.rallydev.com/slm/webservice/v2.0/project/12345"

  # Discover the exact project name
  python verify_rally.py --client-id <id> --client-secret <secret> --find-project OCM

Flags:
  --base-url      default https://rally1.rallydev.com/slm/webservice/v2.0
  --auth-url      default https://rally1.rallydev.com/login/oauth2/token
  --no-ssl-verify disable TLS verification (corporate proxies)
  --states        comma list, default "Defined,In Progress"
"""
import argparse
import json
import ssl
import sys
import urllib.parse
import urllib.request

WSAPI = "/slm/webservice/v2.0"


def make_ctx(verify: bool):
    if verify:
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    print("[warn] TLS verification DISABLED", file=sys.stderr)
    return ctx


def normalize_base(base: str) -> str:
    base = base.rstrip("/")
    if base.endswith(WSAPI):
        base = base[: -len(WSAPI)]
    return base


def get_token(auth_url, client_id, client_secret, ctx) -> str:
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }).encode()
    req = urllib.request.Request(
        auth_url, data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, context=ctx) as r:
        return json.load(r)["access_token"]


def rally_get(base, path, token, params, ctx) -> dict:
    url = f"{normalize_base(base)}{WSAPI}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, context=ctx) as r:
        return json.load(r)


def state_name(v):
    if isinstance(v, dict):
        return v.get("_refObjectName") or v.get("Name") or ""
    return v or ""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="https://rally1.rallydev.com/slm/webservice/v2.0")
    p.add_argument("--auth-url", default="https://rally1.rallydev.com/login/oauth2/token")
    p.add_argument("--client-id")
    p.add_argument("--client-secret")
    p.add_argument("--api-key", help="static bearer token (skips OAuth2)")
    p.add_argument("--project-name")
    p.add_argument("--project-ref")
    p.add_argument("--find-project", metavar="SUBSTR",
                   help="list projects whose Name contains SUBSTR, then exit")
    p.add_argument("--states", default="Defined,In Progress")
    p.add_argument("--no-ssl-verify", action="store_true")
    args = p.parse_args()

    ctx = make_ctx(not args.no_ssl_verify)

    # --- auth ---
    if args.api_key:
        token = args.api_key
        print("[ok] using static API key / bearer token")
    elif args.client_id and args.client_secret:
        try:
            token = get_token(args.auth_url, args.client_id, args.client_secret, ctx)
            print("[ok] OAuth2 token acquired")
        except Exception as e:
            print(f"[fail] auth failed: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("[fail] provide --api-key OR (--client-id and --client-secret)", file=sys.stderr)
        sys.exit(2)

    # --- discover project names ---
    if args.find_project:
        data = rally_get(args.base_url, "/project", token, {
            "query": f'(Name contains "{args.find_project}")',
            "fetch": "Name,_ref", "pagesize": 50,
        }, ctx)
        results = data.get("QueryResult", {}).get("Results", [])
        print(f"\nProjects matching {args.find_project!r} ({len(results)}):")
        for r in results:
            print(f"  {r.get('Name')!r}  ->  {r.get('_ref')}")
        return

    # --- resolve project ref ---
    project_ref = args.project_ref
    if not project_ref and args.project_name:
        data = rally_get(args.base_url, "/project", token, {
            "query": f'(Name = "{args.project_name}")',
            "fetch": "Name,_ref", "pagesize": 1,
        }, ctx)
        results = data.get("QueryResult", {}).get("Results", [])
        if not results:
            print(f"[warn] project {args.project_name!r} NOT found — "
                  f"features will be UNSCOPED. Try --find-project.", file=sys.stderr)
        else:
            project_ref = results[0]["_ref"]
            print(f"[ok] resolved {args.project_name!r} -> {project_ref}")

    # --- fetch features ---
    states = " OR ".join(f'(State.Name = "{s.strip()}")' for s in args.states.split(","))
    params = {
        "query": f"({states})",
        "fetch": "FormattedID,Name,Description,State",
        "pagesize": 200, "order": "FormattedID",
    }
    if project_ref:
        params["project"] = project_ref
        params["projectScopeDown"] = "true"

    data = rally_get(args.base_url, "/portfolioitem/feature", token, params, ctx)
    qr = data.get("QueryResult", {})
    if qr.get("Errors"):
        print(f"[fail] WSAPI errors: {qr['Errors']}", file=sys.stderr)
        sys.exit(1)
    results = qr.get("Results", [])
    total = qr.get("TotalResultCount", len(results))

    print(f"\n[ok] {total} feature(s) total, {len(results)} on this page"
          f"{' (PAGE CAPPED at 200 — paginate or scope down)' if len(results) == 200 else ''}")
    for f in results[:5]:
        print(f"  {f.get('FormattedID')} | {state_name(f.get('State'))} | {f.get('Name','')[:60]}")


if __name__ == "__main__":
    main()
