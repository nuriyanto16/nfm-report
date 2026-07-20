"""Endpoint REST aplikasi laporan."""
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from app.core import repository
from app.core.config import load_sources
from app.core.filters import FILTERABLE, distinct_values
from app.core.periods import VALID_DATE_FIELDS
from app.core.report import build_report
from app.exporters import export_report, EXPORT_FORMATS
from app.security import auth_enabled, current_user, login, menus_of, require_menu

# Menu-menu yang tergolong "laporan"; punya salah satu = boleh tarik data.
REPORT_MENUS = {"harian", "mingguan", "bulanan", "monitoring"}

# Endpoint auth (tanpa proteksi).
auth_router = APIRouter(prefix="/api")


class LoginBody(BaseModel):
    username: str
    password: str


@auth_router.get("/auth/config")
def auth_config():
    return {"auth_enabled": auth_enabled()}


@auth_router.post("/login")
def do_login(body: LoginBody):
    return login(body.username, body.password)


# Endpoint terproteksi (butuh user terautentikasi & aktif).
router = APIRouter(prefix="/api", dependencies=[Depends(current_user)])


def require_report_access(user=Depends(current_user)):
    """Boleh tarik/ekspor laporan bila punya minimal satu menu laporan."""
    if not (REPORT_MENUS & set(menus_of(user))):
        raise HTTPException(403, "Anda tidak punya akses ke laporan")
    return user


def _parse_filters(
    status: Optional[str], pic: Optional[str], kategori: Optional[str],
    priority: Optional[str], status_deploy: Optional[str],
    aplikasi: Optional[str], source_month: Optional[str],
) -> Dict[str, List[str]]:
    raw = {
        "status": status, "pic": pic, "kategori": kategori,
        "priority": priority, "status_deploy": status_deploy,
        "aplikasi": aplikasi, "source_month": source_month,
    }
    out: Dict[str, List[str]] = {}
    for key, val in raw.items():
        if val:
            vals = [v.strip() for v in val.split(",") if v.strip()]
            if vals:
                out[key] = vals
    return out


@router.get("/sources", dependencies=[Depends(require_report_access)])
def get_sources():
    return {"sources": repository.list_sources()}


@router.get("/data-sources", dependencies=[Depends(require_menu("sources"))])
def data_sources():
    """Daftar sumber data (read-only) + link ke sheet — untuk menu Sumber Data."""
    out = []
    for s in load_sources():
        link = ""
        if s.get("type") == "google_sheet" and s.get("spreadsheet_id"):
            link = f"https://docs.google.com/spreadsheets/d/{s['spreadsheet_id']}/edit"
        out.append({
            "id": s.get("id"),
            "name": s.get("name", s.get("id")),
            "type": s.get("type"),
            "link": link,
        })
    return {"sources": out}


@router.get("/filters", dependencies=[Depends(require_report_access)])
def get_filters(source: str = Query(...)):
    try:
        records = repository.get_records(source)
    except KeyError:
        raise HTTPException(404, f"Sumber tidak ditemukan: {source}")
    values = distinct_values(records)
    return {
        "dimensions": list(FILTERABLE.keys()),
        "date_fields": VALID_DATE_FIELDS,
        "values": values,
    }


@router.get("/report", dependencies=[Depends(require_report_access)])
def get_report(
    source: str = Query(...),
    period: str = Query(..., pattern="^(daily|weekly|monthly|all)$"),
    date: Optional[str] = None,
    week_start: Optional[str] = None,
    month: Optional[str] = None,
    date_field: str = "tgl_request",
    status: Optional[str] = None,
    pic: Optional[str] = None,
    kategori: Optional[str] = None,
    priority: Optional[str] = None,
    status_deploy: Optional[str] = None,
    aplikasi: Optional[str] = None,
    source_month: Optional[str] = None,
    refresh: bool = False,
):
    filters = _parse_filters(status, pic, kategori, priority,
                             status_deploy, aplikasi, source_month)
    try:
        result = build_report(
            source, period, date_field=date_field, date=date,
            week_start=week_start, month=month, filters=filters,
            force=refresh,
        )
    except KeyError:
        raise HTTPException(404, f"Sumber tidak ditemukan: {source}")
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {
        "meta": result.meta(),
        "summary": result.summary,
        "rows": [r.model_dump() for r in result.rows],
    }


@router.get("/export", dependencies=[Depends(require_report_access)])
def export(
    source: str = Query(...),
    period: str = Query(..., pattern="^(daily|weekly|monthly)$"),
    format: str = Query(..., pattern="^(xlsx|pdf|docx)$"),
    date: Optional[str] = None,
    week_start: Optional[str] = None,
    month: Optional[str] = None,
    date_field: str = "tgl_request",
    status: Optional[str] = None,
    pic: Optional[str] = None,
    kategori: Optional[str] = None,
    priority: Optional[str] = None,
    status_deploy: Optional[str] = None,
    aplikasi: Optional[str] = None,
    source_month: Optional[str] = None,
):
    filters = _parse_filters(status, pic, kategori, priority,
                             status_deploy, aplikasi, source_month)
    try:
        result = build_report(
            source, period, date_field=date_field, date=date,
            week_start=week_start, month=month, filters=filters,
        )
    except KeyError:
        raise HTTPException(404, f"Sumber tidak ditemukan: {source}")
    except ValueError as e:
        raise HTTPException(400, str(e))

    content, filename, media_type = export_report(result, format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/refresh", dependencies=[Depends(require_report_access)])
def refresh(source: str = Query(...)):
    try:
        n = repository.refresh(source)
    except KeyError:
        raise HTTPException(404, f"Sumber tidak ditemukan: {source}")
    return {"source": source, "records": n, "status": "refreshed"}
