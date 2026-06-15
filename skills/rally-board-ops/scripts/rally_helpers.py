#!/usr/bin/env python3
"""
Rally API helper functions.

Usage:
    from rally_helpers import RallyClient

    client = RallyClient(access_token="<oauth_token>", project_oid="848873700905")
    
    # Create a feature
    feat = client.create_feature("P0 — Core Endpoint", "<p>Description</p>")
    
    # Create a story under it
    story, errors = client.create_story(feat["ref"], "S1: My Story", "<p>...</p>", plan_estimate=3)
    
    # Assign iteration
    client.update_story(story["oid"], Iteration=iter_ref)
    
    # Create and assign tags
    tag_refs = client.ensure_tags(["Backend", "P0", "Data-Tool"])
    client.assign_tags(story["oid"], ["Backend", "P0"])
    
    # Create task
    client.create_task(story["ref"], "Implement resolver", index=1)
"""

import requests
import time
import json
from typing import Optional

RALLY_BASE = "https://rally1.rallydev.com/slm/webservice/v2.0"
DEFAULT_DELAY = 0.35


class RallyClient:
    def __init__(self, access_token: str, project_oid: str, delay: float = DEFAULT_DELAY):
        self.base = RALLY_BASE
        self.headers = {"zsessionid": access_token, "Content-Type": "application/json"}
        self.project_oid = project_oid
        self.project_ref = f"{self.base}/project/{project_oid}"
        self.delay = delay
        self._tag_cache: dict[str, str] = {}  # name -> _ref

    # ── Core HTTP ────────────────────────────────────────────

    def _post(self, url: str, payload: dict, retries: int = 1) -> dict:
        """POST with delay and concurrency retry."""
        time.sleep(self.delay)
        r = requests.post(url, headers=self.headers, json=payload, timeout=30)
        result = r.json()
        top_key = list(result.keys())[0]
        op = result[top_key]
        errors = op.get("Errors", [])
        if errors and any("Concurrency" in e for e in errors) and retries > 0:
            time.sleep(1)
            return self._post(url, payload, retries=retries - 1)
        return result

    def _get(self, url: str) -> dict:
        r = requests.get(url, headers=self.headers, timeout=30)
        return r.json()

    def _check(self, result: dict) -> tuple[dict | None, list[str]]:
        """Extract object and errors from a create/update result."""
        top_key = list(result.keys())[0]
        op = result[top_key]
        errors = op.get("Errors", [])
        warnings = op.get("Warnings", [])
        for w in warnings:
            if "Ignored JSON element" in w:
                print(f"  WARNING: {w}")
        if errors:
            return None, errors
        return op.get("Object", op), []

    # ── Features ─────────────────────────────────────────────

    def create_feature(self, name: str, description: str = "") -> dict:
        payload = {
            "PortfolioItem/Feature": {
                "Name": name,
                "Description": description,
                "Project": self.project_ref,
            }
        }
        result = self._post(f"{self.base}/portfolioitem/feature/create", payload)
        obj, errors = self._check(result)
        if errors:
            raise Exception(f"Feature create failed: {errors}")
        return {"ref": obj["_ref"], "oid": obj["ObjectID"], "fid": obj["FormattedID"]}

    # ── Stories ──────────────────────────────────────────────

    def create_story(
        self,
        feature_ref: str,
        name: str,
        description: str,
        plan_estimate: int = 3,
        notes: str = "",
    ) -> tuple[dict | None, list[str]]:
        payload = {
            "HierarchicalRequirement": {
                "Name": name,
                "Description": description,
                "Project": self.project_ref,
                "PortfolioItem": feature_ref,
                "PlanEstimate": plan_estimate,
            }
        }
        if notes:
            payload["HierarchicalRequirement"]["Notes"] = notes
        result = self._post(f"{self.base}/hierarchicalrequirement/create", payload)
        obj, errors = self._check(result)
        if errors:
            return None, errors
        return {"ref": obj["_ref"], "oid": obj["ObjectID"], "fid": obj["FormattedID"]}, []

    def update_story(self, story_oid: int, **fields) -> tuple[bool, list[str]]:
        """Update any fields on a story. E.g. update_story(oid, PlanEstimate=5, Iteration=ref)"""
        payload = {"HierarchicalRequirement": fields}
        result = self._post(f"{self.base}/hierarchicalrequirement/{story_oid}", payload)
        _, errors = self._check(result)
        return not bool(errors), errors

    def get_story_by_fid(self, formatted_id: str) -> Optional[dict]:
        r = self._get(
            f"{self.base}/hierarchicalrequirement"
            f"?query=(FormattedID = '{formatted_id}')"
            f"&fetch=ObjectID,_ref,FormattedID,Name,PlanEstimate,Iteration,Tags,Notes"
            f"&project={self.project_ref}"
        )
        results = r.json().get("QueryResult", {}).get("Results", [])
        return results[0] if results else None

    def get_stories_by_feature(self, feature_fid: str) -> list[dict]:
        return self._query_all(
            "hierarchicalrequirement",
            f"(Feature.FormattedID = '{feature_fid}')",
            "FormattedID,Name,ObjectID,_ref,Description,Notes,Tags,PlanEstimate,Iteration,Tasks",
        )

    # ── Tasks ────────────────────────────────────────────────

    def create_task(self, story_ref: str, name: str, index: int = 1) -> tuple[bool, list[str]]:
        payload = {
            "Task": {
                "Name": name,
                "WorkProduct": story_ref,
                "Project": self.project_ref,
                "TaskIndex": index,
            }
        }
        result = self._post(f"{self.base}/task/create", payload)
        _, errors = self._check(result)
        return not bool(errors), errors

    def get_existing_tasks(self, story_ref: str) -> list[str]:
        r = self._get(f"{story_ref}/Tasks?fetch=Name&pagesize=50")
        return [t["Name"] for t in r.get("QueryResult", {}).get("Results", [])]

    # ── Tags ─────────────────────────────────────────────────

    def get_tag(self, name: str) -> Optional[dict]:
        r = self._get(f'{self.base}/tag?query=(Name = "{name}")&fetch=Name,ObjectID,_ref')
        results = r.get("QueryResult", {}).get("Results", [])
        return results[0] if results else None

    def create_tag(self, name: str) -> tuple[dict | None, list[str]]:
        payload = {"Tag": {"Name": name}}
        result = self._post(f"{self.base}/tag/create", payload)
        obj, errors = self._check(result)
        if errors:
            return None, errors
        return {"ref": obj["_ref"], "oid": obj["ObjectID"], "name": name}, []

    def ensure_tags(self, tag_names: list[str]) -> dict[str, str]:
        """Get or create tags. Returns {name: _ref} map."""
        refs = {}
        for name in tag_names:
            if name in self._tag_cache:
                refs[name] = self._tag_cache[name]
                continue
            existing = self.get_tag(name)
            if existing:
                refs[name] = existing["_ref"]
                self._tag_cache[name] = existing["_ref"]
                print(f"  TAG EXISTS: {name}")
            else:
                tag, errors = self.create_tag(name)
                if tag:
                    refs[name] = tag["ref"]
                    self._tag_cache[name] = tag["ref"]
                    print(f"  TAG CREATED: {name}")
                else:
                    print(f"  TAG FAILED: {name} -> {errors}")
        return refs

    def assign_tags(self, story_oid: int, tag_names: list[str]) -> tuple[bool, list[str]]:
        """Assign tags by name (must be in cache via ensure_tags first)."""
        tag_list = [{"_ref": self._tag_cache[n]} for n in tag_names if n in self._tag_cache]
        return self.update_story(story_oid, Tags=tag_list)

    # ── Iterations ───────────────────────────────────────────

    def get_iterations(self) -> list[dict]:
        return self._query_all(
            "iteration", "", "Name,ObjectID,StartDate,EndDate,_ref"
        )

    def assign_iteration(self, story_oid: int, iteration_ref: str) -> tuple[bool, list[str]]:
        return self.update_story(story_oid, Iteration=iteration_ref)

    # ── Field Discovery ──────────────────────────────────────

    def discover_writable_text_fields(self) -> list[dict]:
        r = self._get(
            f"{self.base}/typedefinition"
            f"?query=(Name = 'Hierarchical Requirement')&fetch=ObjectID"
        )
        type_oid = r.get("QueryResult", {}).get("Results", [{}])[0].get("ObjectID")
        if not type_oid:
            return []
        r2 = self._get(
            f"{self.base}/typedefinition/{type_oid}/Attributes"
            f"?fetch=Name,ElementName,ReadOnly,Custom,AttributeType&pagesize=200"
        )
        results = r2.get("QueryResult", {}).get("Results", [])
        return [
            {"name": a["ElementName"], "custom": a.get("Custom", False)}
            for a in results
            if a.get("AttributeType") == "TEXT" and not a.get("ReadOnly", False)
        ]

    # ── Queries ──────────────────────────────────────────────

    def _query_all(self, endpoint: str, query: str, fetch: str) -> list[dict]:
        all_results = []
        start = 1
        while True:
            url = (
                f"{self.base}/{endpoint}"
                f"?query=({query})" if query else f"{self.base}/{endpoint}?"
            )
            url += f"&fetch={fetch}&pagesize=200&start={start}&project={self.project_ref}"
            r = self._get(url)
            qr = r.get("QueryResult", {})
            results = qr.get("Results", [])
            all_results.extend(results)
            if start + len(results) > qr.get("TotalResultCount", 0):
                break
            start += 200
        return all_results


# ── Convenience: Batch Operations ────────────────────────────

def batch_update(client: RallyClient, items: list[tuple], field_name: str):
    """
    Batch update a single field on multiple stories.
    items: [(oid, formatted_id, value), ...]
    """
    print(f"Updating {field_name} on {len(items)} stories...")
    success = fail = 0
    for oid, fid, value in items:
        ok, errors = client.update_story(oid, **{field_name: value})
        if ok:
            print(f"  OK: {fid} -> {value}")
            success += 1
        else:
            print(f"  FAIL: {fid} -> {errors}")
            fail += 1
    print(f"\nDone: {success} OK, {fail} FAIL out of {len(items)}")
    return success, fail
