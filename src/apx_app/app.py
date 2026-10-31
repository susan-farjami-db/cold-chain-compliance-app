"""Cold Chain — T-Val compliance app v2 (FastAPI + React SPA).

A polished "Modern SaaS (light)" rebuild of the v1 Dash app. Same data
tables, same proven atomic save semantics (see backend.py) — only the UI
and transport (JSON API + Vite-built static assets) are new.

FastAPI serves:
  - GET  /api/data   -> compliance rows, unit dropdown, tval statuses, user
  - POST /api/save   -> atomic INSERT OVERWRITE, auto-stamps changed rows
  - /*               -> the built React SPA (static assets from ./static)
"""
import os
import re
import uuid
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from databricks.sdk import WorkspaceClient

import backend

app = FastAPI(title="Cold Chain — T-Val Compliance")

STATIC_DIR = Path(__file__).parent / "static"

_ws = None
_name_cache: dict[str, str] = {}


def _workspace_client():
    global _ws
    if _ws is None:
        _ws = WorkspaceClient()  # app service principal
    return _ws


def _name_from_email(email: str) -> str:
    """Fallback: turn 'jane.doe@example.com' into 'Jane Doe'."""
    local = email.split("@")[0]
    parts = [p for p in re.split(r"[._-]+", local) if p]
    return " ".join(w.capitalize() for w in parts) if parts else email


def _display_name_for(email: str) -> str:
    """Resolve a friendly display name for the signed-in user's email.

    Tries the Unity Catalog / SCIM user directory first (exact name), then
    falls back to a title-cased name derived from the email. Cached per email.
    """
    if not email or "@" not in email:
        return email or "unknown-user"
    if email in _name_cache:
        return _name_cache[email]
    name = None
    try:
        for u in _workspace_client().users.list(filter=f'userName eq "{email}"', count=1):
            if u.display_name:
                name = u.display_name
                break
    except Exception:
        name = None
    if not name:
        name = _name_from_email(email)
    _name_cache[email] = name
    return name


def _current_user(request: Request) -> str:
    """Display name of the signed-in app user (from the forwarded credential)."""
    h = request.headers
    email = h.get("X-Forwarded-Email") or h.get("X-Forwarded-Preferred-Username") or ""
    return _display_name_for(email) if email else "unknown-user"


class SaveRequest(BaseModel):
    rows: list[dict]


@app.get("/api/data")
def get_data(request: Request):
    user = _current_user(request)
    try:
        rows = backend.load_compliance()
        for r in rows:
            r["row_id"] = str(uuid.uuid4())
        units = backend.load_units()
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"{e}"})
    return {
        "rows": rows,
        "units": units,
        "tval_statuses": backend.TVAL_STATUSES,
        "user": user,
    }


@app.post("/api/save")
def post_save(payload: SaveRequest, request: Request):
    user = _current_user(request)
    try:
        today = date.today().isoformat()
        # Snapshot the DB state so we only auto-stamp genuinely changed/new rows.
        original_by_unit = {}
        for r in backend.load_compliance():
            unit = (r.get("unit_number") or "").strip()
            if unit:
                original_by_unit[unit] = {f: r.get(f) for f in backend.EDITABLE_FIELDS}

        to_write = []
        changed = 0
        for r in payload.rows:
            unit = (r.get("unit_number") or "").strip()
            if not unit:
                continue
            original = original_by_unit.get(unit)
            is_changed = original is None or any(
                (r.get(f) or "") != (original.get(f) or "") for f in backend.EDITABLE_FIELDS
            )
            row = dict(r)
            if is_changed:
                row["last_update_date"] = today
                row["updated_by"] = user
                changed += 1
            to_write.append(row)

        backend.save_compliance(to_write)

        rows = backend.load_compliance()
        for r in rows:
            r["row_id"] = str(uuid.uuid4())
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"{e}"})
    return {"saved": True, "changed": changed, "user": user, "rows": rows}


# --- Static SPA (mounted last so /api routes win) ------------------------------
if (STATIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    candidate = STATIC_DIR / full_path
    if full_path and candidate.is_file():
        return FileResponse(candidate)
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse(status_code=503, content={"detail": "Frontend not built"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("DATABRICKS_APP_PORT", "8080")),
    )
