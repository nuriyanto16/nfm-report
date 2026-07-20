"""Definisi kolom laporan yang dipakai bersama xlsx/docx/pdf agar konsisten."""
from __future__ import annotations

from datetime import datetime
from typing import Callable, List, Optional, Tuple

from app.core.models import TaskRecord


def _d(v: Optional[datetime]) -> str:
    return v.strftime("%d/%m/%Y") if isinstance(v, datetime) else ""


def _s(v) -> str:
    return "" if v is None else str(v)


# (header, lebar kira-kira, fungsi ekstraksi)
COLUMNS: List[Tuple[str, int, Callable[[TaskRecord], str]]] = [
    ("No", 5, lambda r: _s(int(r.no)) if r.no is not None else ""),
    ("Aplikasi", 16, lambda r: _s(r.aplikasi)),
    ("Issue", 50, lambda r: _s(r.issue)),
    ("Kategori", 18, lambda r: _s(r.kategori)),
    ("Tgl Request", 12, lambda r: _d(r.tgl_request)),
    ("Tgl Mulai", 12, lambda r: _d(r.tgl_mulai)),
    ("Tgl Estimasi Selesai", 14, lambda r: _d(r.tgl_estimasi)),
    ("Tgl Selesai", 12, lambda r: _d(r.tgl_selesai)),
    ("PIC", 12, lambda r: _s(r.pic)),
    ("Request By", 16, lambda r: _s(r.request_by)),
    ("Status", 12, lambda r: _s(r.status)),
    ("Priority", 10, lambda r: _s(r.priority)),
    ("Status Deploy", 18, lambda r: _s(r.status_deploy)),
    ("Keterangan", 30, lambda r: _s(r.keterangan)),
]

HEADERS = [c[0] for c in COLUMNS]


def row_values(r: TaskRecord) -> List[str]:
    return [fn(r) for _, _, fn in COLUMNS]
