"""Resolusi periode laporan: Harian / Mingguan / Bulanan.

Semua periode dihitung terhadap satu kolom tanggal acuan (`date_field`),
default `tgl_request` sesuai keputusan proyek.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from datetime import date as date_cls
from typing import List, Optional

from app.core.models import TaskRecord

VALID_DATE_FIELDS = [
    "tgl_request", "tgl_mulai", "tgl_estimasi", "tgl_selesai", "last_update",
]
DEFAULT_DATE_FIELD = "tgl_request"


@dataclass
class Period:
    mode: str            # daily | weekly | monthly
    start: date
    end: date            # inklusif
    label: str
    date_field: str

    def contains(self, d: Optional[date]) -> bool:
        if self.mode == "all":
            return True  # all-time: semua record ikut, termasuk tanpa tanggal
        return d is not None and self.start <= d <= self.end


_MONTH_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def resolve_period(
    mode: str,
    *,
    date_field: str = DEFAULT_DATE_FIELD,
    date: Optional[str] = None,
    week_start: Optional[str] = None,
    month: Optional[str] = None,
) -> Period:
    """Bangun Period dari parameter request.

    - daily:   butuh `date` (YYYY-MM-DD).
    - weekly:  `week_start` (YYYY-MM-DD); jika kosong, pakai Senin minggu ini.
    - monthly: `month` (YYYY-MM); jika kosong, pakai bulan berjalan.
    """
    if date_field not in VALID_DATE_FIELDS:
        raise ValueError(f"date_field tidak valid: {date_field!r}")

    if mode == "daily":
        d = _parse_date(date) if date else _today()
        return Period("daily", d, d, d.strftime("%d %B %Y"), date_field)

    if mode == "weekly":
        if week_start:
            start = _parse_date(week_start)
        else:
            today = _today()
            start = today - timedelta(days=today.weekday())  # Senin
        end = start + timedelta(days=6)
        label = f"{start.strftime('%d %b %Y')} - {end.strftime('%d %b %Y')}"
        return Period("weekly", start, end, label, date_field)

    if mode == "all":
        return Period("all", date_cls.min, date_cls.max, "Semua Waktu", date_field)

    if mode == "monthly":
        if month:
            y, m = (int(x) for x in month.split("-"))
        else:
            t = _today()
            y, m = t.year, t.month
        start = date_cls(y, m, 1)
        end = date_cls(y + 1, 1, 1) - timedelta(days=1) if m == 12 \
            else date_cls(y, m + 1, 1) - timedelta(days=1)
        label = f"{_MONTH_ID[m - 1]} {y}"
        return Period("monthly", start, end, label, date_field)

    raise ValueError(f"mode periode tidak valid: {mode!r}")


def _today() -> date:
    return datetime.now().date()


def filter_by_period(records: List[TaskRecord], period: Period) -> List[TaskRecord]:
    # Mode harian: selain kolom acuan, record yang TGL SELESAI-nya jatuh di hari
    # itu juga ikut terbawa (task yang selesai hari tsb wajib muncul), kecuali
    # acuannya memang sudah tgl_selesai.
    if period.mode == "daily" and period.date_field != "tgl_selesai":
        return [
            r for r in records
            if period.contains(r.date_for(period.date_field))
            or period.contains(r.date_for("tgl_selesai"))
        ]
    return [r for r in records if period.contains(r.date_for(period.date_field))]
