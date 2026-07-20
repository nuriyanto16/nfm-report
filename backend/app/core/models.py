"""Model data internal yang dipakai seluruh aplikasi.

Semua adapter sumber data wajib menormalisasi barisnya menjadi `TaskRecord`,
sehingga period/filter/aggregate/exporter tidak peduli sumbernya dari mana.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_serializer

# Status kanonik. Nilai mentah dinormalisasi ke salah satu ini; baris tanpa
# status diberi label TANPA_STATUS agar tetap bisa difilter/ditampilkan.
STATUS_CANONICAL = ["Done", "Progress", "Hold", "Back Log", "To Do"]
TANPA_STATUS = "Tanpa Status"


def canonical_status(raw: Optional[str]) -> str:
    """Map nilai status mentah ke bentuk kanonik (case/spacing-insensitive)."""
    if raw is None:
        return TANPA_STATUS
    s = " ".join(str(raw).split()).strip()
    if not s:
        return TANPA_STATUS
    low = s.lower().replace("-", " ")
    table = {
        "done": "Done",
        "selesai": "Done",
        "progress": "Progress",
        "in progress": "Progress",
        "on progress": "Progress",
        "hold": "Hold",
        "on hold": "Hold",
        "pending": "Hold",
        "back log": "Back Log",
        "backlog": "Back Log",
        "to do": "To Do",
        "todo": "To Do",
        "open": "To Do",
    }
    return table.get(low, s)  # nilai tak dikenal dipertahankan apa adanya


class TaskRecord(BaseModel):
    """Satu baris task hasil normalisasi dari sheet bulanan."""

    no: Optional[float] = None
    issue: str = ""
    path_menu: Optional[str] = None
    tgl_request: Optional[datetime] = None
    tgl_mulai: Optional[datetime] = None
    tgl_estimasi: Optional[datetime] = None
    tgl_selesai: Optional[datetime] = None
    request_by: Optional[str] = None
    pic: Optional[str] = None
    kategori: Optional[str] = None
    status: str = TANPA_STATUS          # sudah kanonik
    status_raw: Optional[str] = None    # nilai asli dari sheet
    priority: Optional[str] = None
    status_deploy: Optional[str] = None
    last_update: Optional[datetime] = None
    keterangan: Optional[str] = None

    aplikasi: str = ""        # dari section marker (Pengujian/Kalibrasi/...)
    source_id: str = ""       # id sumber data
    source_month: str = ""    # nama tab bulan, mis. "06. Juni 2026"

    @field_serializer(
        "tgl_request", "tgl_mulai", "tgl_estimasi",
        "tgl_selesai", "last_update",
    )
    def _ser_dt(self, v: Optional[datetime]):
        return v.isoformat() if v else None

    def date_for(self, field: str) -> Optional[date]:
        """Ambil nilai date dari kolom acuan periode (mis. 'tgl_request')."""
        v = getattr(self, field, None)
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        return None
