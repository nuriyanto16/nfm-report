"""Filter engine dinamis untuk TaskRecord.

Dimensi filter dideklarasikan sekali di FILTERABLE; menambah dimensi baru
cukup tambah entri di sini (tidak perlu ubah endpoint). Setiap dimensi
mendukung multi-nilai (OR di dalam dimensi, AND antar dimensi).
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from app.core.models import TaskRecord

# nama filter -> atribut TaskRecord
FILTERABLE: Dict[str, str] = {
    "status": "status",
    "pic": "pic",
    "kategori": "kategori",
    "priority": "priority",
    "status_deploy": "status_deploy",
    "aplikasi": "aplikasi",
    "source_month": "source_month",
}


def _norm(v) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def apply_filters(
    records: List[TaskRecord], selected: Dict[str, Iterable[str]]
) -> List[TaskRecord]:
    """Terapkan dict {dimensi: [nilai,...]} ke records.

    Nilai dibandingkan case-insensitive. Dimensi tak dikenal diabaikan;
    dimensi dengan daftar kosong diabaikan (= tidak memfilter).
    """
    active = {}
    for key, values in selected.items():
        attr = FILTERABLE.get(key)
        if not attr or not values:
            continue
        wanted = {v.strip().lower() for v in values if v and v.strip()}
        if wanted:
            active[attr] = wanted

    if not active:
        return list(records)

    out = []
    for r in records:
        ok = True
        for attr, wanted in active.items():
            val = _norm(getattr(r, attr, None))
            if (val or "").lower() not in wanted:
                ok = False
                break
        if ok:
            out.append(r)
    return out


def distinct_values(records: List[TaskRecord]) -> Dict[str, List[str]]:
    """Nilai unik per dimensi (untuk mengisi UI filter secara dinamis)."""
    result: Dict[str, set] = {key: set() for key in FILTERABLE}
    for r in records:
        for key, attr in FILTERABLE.items():
            v = _norm(getattr(r, attr, None))
            if v:
                result[key].add(v)
    return {key: sorted(vals) for key, vals in result.items()}
