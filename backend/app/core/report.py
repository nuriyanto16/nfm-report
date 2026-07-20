"""Service laporan: gabungkan period + filter + aggregate jadi satu hasil.

Dipakai bersama oleh endpoint JSON (/api/report) dan exporter (xlsx/pdf/docx)
sehingga data preview & data export selalu identik.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from app.core import repository
from app.core.aggregate import daily_breakdown, summarize
from app.core.filters import apply_filters
from app.core.models import TaskRecord
from app.core.periods import (
    DEFAULT_DATE_FIELD,
    Period,
    filter_by_period,
    resolve_period,
)


@dataclass
class ReportResult:
    source_id: str
    source_name: str
    period: Period
    filters: Dict[str, List[str]]
    rows: List[TaskRecord]
    summary: Dict = field(default_factory=dict)

    def meta(self) -> Dict:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "period": {
                "mode": self.period.mode,
                "start": self.period.start.isoformat(),
                "end": self.period.end.isoformat(),
                "label": self.period.label,
                "date_field": self.period.date_field,
            },
            "filters": self.filters,
            "count": len(self.rows),
        }


def build_report(
    source_id: str,
    mode: str,
    *,
    date_field: str = DEFAULT_DATE_FIELD,
    date: Optional[str] = None,
    week_start: Optional[str] = None,
    month: Optional[str] = None,
    filters: Optional[Dict[str, Iterable[str]]] = None,
    force: bool = False,
) -> ReportResult:
    source = next(
        (s for s in repository.list_sources() if s["id"] == source_id), None
    )
    if source is None:
        raise KeyError(source_id)

    period = resolve_period(
        mode, date_field=date_field, date=date,
        week_start=week_start, month=month,
    )
    records = repository.get_records(source_id, force=force)
    # Filter dimensi lebih dulu supaya `records` (all-time, sudah terfilter)
    # bisa dipakai menghitung Carry Over di luar periode harian.
    filters = {k: list(v) for k, v in (filters or {}).items() if v}
    records = apply_filters(records, filters)
    rows = filter_by_period(records, period)
    # Urutkan kronologis berdasarkan kolom acuan, lalu NO.
    rows.sort(key=lambda r: (r.date_for(period.date_field) or _MIN, r.no or 0))

    summary = summarize(rows)
    # Laporan harian: lampirkan rincian isu / solved / pr / carry over.
    if period.mode == "daily":
        summary["daily"] = daily_breakdown(rows, period.start, all_records=records)

    return ReportResult(
        source_id=source_id,
        source_name=source["name"],
        period=period,
        filters=filters,
        rows=rows,
        summary=summary,
    )


from datetime import date as _date  # noqa: E402
_MIN = _date.min
