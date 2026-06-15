"""Rally API routes (FastAPI example).

Three endpoints: config probe, list features (with already-imported flag),
import selected, and sync one. Adapt persistence calls to your ORM.
"""

from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.core.database import get_session
from app.models.database import Workspace  # your entity with rally_* columns
from app.services.rally_service import list_features, get_feature, html_to_markdown

router = APIRouter(prefix="/rally", tags=["rally"])


def _gateway_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=502, detail=f"Rally request failed: {exc}")


@router.get("/config")
async def rally_config():
    return {"rally_enabled": settings.rally_enabled}


@router.get("/features")
async def list_rally_features(db: AsyncSession = Depends(get_session)):
    if not settings.rally_enabled:
        raise HTTPException(400, "Rally integration is not configured")
    try:
        features = await list_features()
    except httpx.HTTPError as exc:
        raise _gateway_error(exc) from exc

    rows = await db.execute(
        select(Workspace.rally_feature_id).where(
            Workspace.rally_feature_id.isnot(None),
            Workspace.deleted_at.is_(None),
        )
    )
    imported = set(rows.scalars().all())
    return [
        {
            "formatted_id": f["formatted_id"],
            "name": f["name"],
            "state": f["state"],
            "description_preview": html_to_markdown(f["description"])[:200],
            "already_imported": f["formatted_id"] in imported,
        }
        for f in features
    ]


@router.post("/import")
async def import_rally_features(feature_ids: list[str], db: AsyncSession = Depends(get_session)):
    if not settings.rally_enabled:
        raise HTTPException(400, "Rally integration is not configured")
    results = []
    for fid in feature_ids:
        results.append(await _import_one(fid, db))
    return {"results": results}


@router.post("/{workspace_id}/sync")
async def sync_rally_workspace(workspace_id: int, db: AsyncSession = Depends(get_session)):
    """Refresh name + state ONLY. Never touches downstream/user-edited content."""
    if not settings.rally_enabled:
        raise HTTPException(400, "Rally integration is not configured")
    ws = await db.get(Workspace, workspace_id)
    if not ws or ws.deleted_at is not None:
        raise HTTPException(404, "Workspace not found")
    if not ws.rally_feature_id:
        raise HTTPException(400, "Workspace is not a Rally import")
    try:
        feature = await get_feature(ws.rally_feature_id)
    except httpx.HTTPError as exc:
        raise _gateway_error(exc) from exc
    if not feature:
        raise HTTPException(404, f"Feature {ws.rally_feature_id} not found in Rally")
    ws.name = feature["name"]
    ws.rally_state = feature["state"]
    ws.rally_last_synced_at = datetime.utcnow()
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    return ws


async def _import_one(fid: str, db: AsyncSession) -> dict:
    """Create or reactivate a workspace from a Rally feature. Best-effort."""
    existing = (
        await db.execute(select(Workspace).where(Workspace.rally_feature_id == fid))
    ).scalar_one_or_none()
    if existing and existing.deleted_at is None:
        return {"formatted_id": fid, "status": "error", "message": "Already imported"}

    try:
        feature = await get_feature(fid)
    except httpx.HTTPError as exc:
        return {"formatted_id": fid, "status": "error", "message": f"Rally request failed: {exc}"}
    if not feature:
        return {"formatted_id": fid, "status": "error", "message": "Not found in Rally"}

    now = datetime.utcnow()
    if existing:  # soft-deleted -> reactivate, preserving downstream data
        existing.deleted_at = None
        existing.name = feature["name"]
        existing.rally_state = feature["state"]
        existing.rally_last_synced_at = now
        ws = existing
    else:
        ws = Workspace(
            name=feature["name"],
            rally_feature_id=fid,
            rally_state=feature["state"],
            rally_last_synced_at=now,
        )
    db.add(ws)
    await db.commit()
    await db.refresh(ws)

    # Store the source document (HTML -> Markdown). Optional post-processing
    # (e.g. LLM parsing) should be best-effort: never abort the import on failure.
    # md = html_to_markdown(feature["description"]); persist md against ws.id ...

    return {"formatted_id": fid, "name": feature["name"],
            "workspace_id": ws.id, "status": "success"}
