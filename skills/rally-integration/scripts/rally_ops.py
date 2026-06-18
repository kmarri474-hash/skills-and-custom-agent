#!/usr/bin/env python3
"""Rally operations CLI — reports & CRUD via the OAuth2 authorization_code flow.

Distilled from a real session: pull reports, create stories/tasks, set Acceptance
Criteria, move stories between iterations, and resolve users. Handles token caching
(so the single-use auth code is exchanged only once), pagination, the c_AcceptanceCriteria
custom field, and concurrency-conflict retries.

Reads creds from .env: RALLY_CLIENT_ID, RALLY_CLIENT_SECRET, RALLY_REDIRECT_URI
(default https://localhost:3000/callbace), optional RALLY_SSL_VERIFY (default false).

Requires: requests. (urllib3 warnings silenced when SSL verify is off.)

Typical flow
------------
  # 1) print the login URL, user logs in, copies ?code=XXXX from the address bar
  python rally_ops.py auth-url

  # 2) first call exchanges the code and caches the token (rally_token.txt);
  #    subsequent calls reuse the cached token until it expires
  python rally_ops.py --code XXXX report --project "CM | Team Nebula" --kind feature
  python rally_ops.py report --feature F1852252 --kind story
  python rally_ops.py find-user --name Xu
  python rally_ops.py create-story --feature F1852252 --name "..." \
      --owner user@optum.com --iteration "2026 Iteration 13 (6/17 to 6/30)" \
      --description-file body.html --ac-file ac.html --tasks-file tasks.json
  python rally_ops.py set-ac --story US10684787 --ac-file ac.html
  python rally_ops.py move-iteration --story US10552982 --to ""   # "" = backlog

tasks-file is JSON: [{"name": "...", "estimate": 4.0}, ...]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass

ROOT = "https://rally1.rallydev.com"
BASE = f"{ROOT}/slm/webservice/v2.0"
AUTH = f"{ROOT}/login/oauth2/auth"
TOKEN = f"{ROOT}/login/oauth2/token"
TOKEN_CACHE = Path("rally_token.txt")
AC_FIELD = "c_AcceptanceCriteria"


def load_env() -> dict:
    env = {}
    p = Path(".env")
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = load_env()
CLIENT_ID = ENV.get("RALLY_CLIENT_ID", "")
CLIENT_SECRET = ENV.get("RALLY_CLIENT_SECRET", "")
REDIRECT_URI = ENV.get("RALLY_REDIRECT_URI", "https://localhost:3000/callbace")
VERIFY = ENV.get("RALLY_SSL_VERIFY", "false").lower() == "true"


def auth_url() -> str:
    from urllib.parse import urlencode
    return AUTH + "?" + urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "alm",  # REQUIRED
    })


def get_token(code: str | None) -> str:
    # reuse cached token if still valid
    if TOKEN_CACHE.exists():
        cached = TOKEN_CACHE.read_text().strip()
        if cached:
            t = requests.get(f"{BASE}/subscription",
                             headers={"Authorization": f"Bearer {cached}",
                                      "Accept": "application/json"},
                             verify=VERIFY, timeout=30)
            if t.status_code == 200:
                return cached
    if not code:
        sys.exit("No valid cached token. Run `auth-url`, log in, and pass --code XXXX "
                 "(the code is single-use).")
    r = requests.post(TOKEN, data={
        "grant_type": "authorization_code", "code": code,
        "redirect_uri": REDIRECT_URI, "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }, verify=VERIFY, timeout=30)
    if r.status_code != 200:
        sys.exit(f"Token exchange failed ({r.status_code}): {r.text[:300]}\n"
                 "If this says code_not_found, the code was already used — get a fresh one.")
    tok = r.json()["access_token"]
    TOKEN_CACHE.write_text(tok)
    return tok


class Rally:
    def __init__(self, token: str):
        self.hg = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        self.hp = {**self.hg, "Content-Type": "application/json"}

    def get(self, path, **params):
        r = requests.get(f"{BASE}/{path}", params=params, headers=self.hg,
                         verify=VERIFY, timeout=60)
        r.raise_for_status()
        qr = r.json().get("QueryResult", {})
        if qr.get("Errors"):
            sys.exit(f"WSAPI error: {qr['Errors']}")
        return qr

    def get_all(self, path, **params):
        params.setdefault("pagesize", 200)
        out, start = [], 1
        while True:
            qr = self.get(path, start=start, **params)
            res = qr.get("Results", [])
            out.extend(res)
            if len(out) >= qr.get("TotalResultCount", 0) or not res:
                break
            start += len(res)
        return out

    def first(self, path, **params):
        res = self.get(path, **params).get("Results", [])
        return res[0] if res else None

    def post(self, url_or_path, body, retries=4):
        url = url_or_path if url_or_path.startswith("http") else f"{BASE}/{url_or_path}"
        last = None
        for _ in range(retries):
            r = requests.post(url, headers=self.hp, data=json.dumps(body),
                              verify=VERIFY, timeout=30)
            j = r.json()
            env = j.get("CreateResult") or j.get("OperationResult") or {}
            errs = env.get("Errors") or []
            if r.status_code == 200 and not errs:
                return env
            last = errs or r.text[:300]
            if not any("Concurrency conflict" in str(e) for e in errs):
                break
            time.sleep(0.5)
        sys.exit(f"POST failed: {last}")


def ref_of(obj):
    return obj["_ref"] if obj else None


def name_of(v):
    return (v.get("_refObjectName") or v.get("Name") or "") if isinstance(v, dict) else (v or "")


def resolve_owner(r: Rally, who: str):
    o = r.first("user", query=f'(EmailAddress = "{who}")', fetch="DisplayName,EmailAddress,_ref")
    if not o:
        o = r.first("user", query=f'(UserName = "{who}")', fetch="DisplayName,EmailAddress,_ref")
    if not o:
        sys.exit(f"User '{who}' not found (case-sensitive). Try `find-user --name <surname>`.")
    return o


def resolve_feature(r: Rally, fid: str):
    f = r.first("portfolioitem/feature", query=f'(FormattedID = "{fid}")',
                fetch="FormattedID,Name,Project,_ref")
    if not f:
        sys.exit(f"Feature {fid} not found.")
    return f


def resolve_iteration(r: Rally, name: str, project_ref: str):
    it = r.first("iteration", query=f'(Name = "{name}")', project=project_ref,
                 projectScopeUp="true", projectScopeDown="true", fetch="Name,_ref")
    if not it:
        sys.exit(f"Iteration '{name}' not found in project scope.")
    return it


# ---- commands ----
def cmd_auth_url(_r, _a):
    print(auth_url())


def cmd_find_user(r, a):
    seen = {}
    for q in (f'(DisplayName contains "{a.name}")',
              f'(EmailAddress contains "{a.name}")',
              f'(LastName = "{a.name}")'):
        for u in r.get_all("user", query=q, fetch="DisplayName,EmailAddress,UserName"):
            seen[u.get("UserName")] = u
    for u in sorted(seen.values(), key=lambda x: x.get("DisplayName", "")):
        print(f"  {u.get('DisplayName')} | {u.get('EmailAddress')} | {u.get('UserName')}")
    print(f"\n{len(seen)} match(es).")


def cmd_report(r, a):
    if a.kind == "feature":
        rows = r.get_all("portfolioitem/feature",
                         query=f'(Project.Name = "{a.project}")' if a.project else None,
                         project=a.project_ref, projectScopeDown="true" if a.project_ref else None,
                         fetch="FormattedID,Name,State,Project", order="FormattedID ASC")
        for x in rows:
            print(f"{x.get('FormattedID')} | {name_of(x.get('State')):14} | {x.get('Name','')}")
    else:
        q = f'(Feature.FormattedID = "{a.feature}")' if a.feature else \
            (f'(Iteration.Name = "{a.iteration}")' if a.iteration else None)
        rows = r.get_all("hierarchicalrequirement", query=q,
                         fetch="FormattedID,Name,ScheduleState,Iteration,Feature,Owner",
                         order="FormattedID ASC")
        for x in rows:
            print(f"{x.get('FormattedID')} | {name_of(x.get('ScheduleState')):12} | "
                  f"{name_of(x.get('Iteration'))[:28]:28} | {x.get('Name','')}")
    print(f"\nTotal: {len(rows)}")


def cmd_create_story(r, a):
    feature = resolve_feature(r, a.feature)
    project_ref = ref_of(feature.get("Project"))
    owner = resolve_owner(r, a.owner)
    body = {"HierarchicalRequirement": {
        "Name": a.name, "Project": project_ref,
        "PortfolioItem": ref_of(feature), "Owner": ref_of(owner),
    }}
    if a.description_file:
        body["HierarchicalRequirement"]["Description"] = Path(a.description_file).read_text()
    if a.iteration:
        body["HierarchicalRequirement"]["Iteration"] = ref_of(resolve_iteration(r, a.iteration, project_ref))
    if a.ac_file:
        body["HierarchicalRequirement"][AC_FIELD] = Path(a.ac_file).read_text()
    obj = r.post("hierarchicalrequirement/create", body)["Object"]
    story_ref, fid = obj["_ref"], obj["FormattedID"]
    print(f"Created {fid} — {a.name}")

    if a.ac_file:  # verify AC persisted
        chk = r.first("hierarchicalrequirement", query=f'(FormattedID = "{fid}")', fetch=AC_FIELD)
        print(f"  AC field: {'OK' if chk.get(AC_FIELD) else 'EMPTY — check field name!'}")

    if a.tasks_file:
        tasks = json.loads(Path(a.tasks_file).read_text())
        for t in tasks:
            tobj = r.post("task/create", {"Task": {
                "Name": t["name"], "WorkProduct": story_ref, "Owner": ref_of(owner),
                "Estimate": t.get("estimate", 0), "Project": project_ref,
            }})["Object"]
            print(f"  task {tobj['FormattedID']}: {t['name'][:50]}")


def cmd_set_ac(r, a):
    s = r.first("hierarchicalrequirement", query=f'(FormattedID = "{a.story}")', fetch="_ref")
    if not s:
        sys.exit(f"Story {a.story} not found.")
    r.post(s["_ref"], {"HierarchicalRequirement": {AC_FIELD: Path(a.ac_file).read_text()}})
    chk = r.first("hierarchicalrequirement", query=f'(FormattedID = "{a.story}")', fetch=AC_FIELD)
    print(f"{a.story}: AC {'set OK' if chk.get(AC_FIELD) else 'EMPTY — check field name!'}")


def cmd_move_iteration(r, a):
    s = r.first("hierarchicalrequirement", query=f'(FormattedID = "{a.story}")',
                fetch="_ref,Iteration,Project")
    if not s:
        sys.exit(f"Story {a.story} not found.")
    target = None
    if a.to:
        target = ref_of(resolve_iteration(r, a.to, ref_of(s.get("Project"))))
    r.post(s["_ref"], {"HierarchicalRequirement": {"Iteration": target}})
    print(f"{a.story}: moved to {'backlog' if not a.to else a.to}")


def main():
    p = argparse.ArgumentParser(description="Rally operations CLI")
    p.add_argument("--code", help="authorization code (first call only; single-use)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth-url")

    fu = sub.add_parser("find-user"); fu.add_argument("--name", required=True)

    rp = sub.add_parser("report")
    rp.add_argument("--kind", choices=["feature", "story"], required=True)
    rp.add_argument("--project"); rp.add_argument("--project-ref")
    rp.add_argument("--feature"); rp.add_argument("--iteration")

    cs = sub.add_parser("create-story")
    cs.add_argument("--feature", required=True); cs.add_argument("--name", required=True)
    cs.add_argument("--owner", required=True); cs.add_argument("--iteration")
    cs.add_argument("--description-file"); cs.add_argument("--ac-file")
    cs.add_argument("--tasks-file")

    sa = sub.add_parser("set-ac")
    sa.add_argument("--story", required=True); sa.add_argument("--ac-file", required=True)

    mi = sub.add_parser("move-iteration")
    mi.add_argument("--story", required=True)
    mi.add_argument("--to", default="", help='target iteration name; "" = backlog')

    a = p.parse_args()

    if a.cmd == "auth-url":
        cmd_auth_url(None, a); return

    rally = Rally(get_token(a.code))
    {
        "find-user": cmd_find_user, "report": cmd_report,
        "create-story": cmd_create_story, "set-ac": cmd_set_ac,
        "move-iteration": cmd_move_iteration,
    }[a.cmd](rally, a)


if __name__ == "__main__":
    main()
