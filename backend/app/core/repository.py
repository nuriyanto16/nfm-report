"""Pengambilan records per sumber, dengan cache TTL sederhana di memori.

Cache mencegah download spreadsheet berulang pada tiap request. Bisa
di-invalidasi lewat refresh() (dipakai endpoint POST /api/refresh).
"""
from __future__ import annotations

import os
import threading
import time
from typing import Dict, List, Tuple

from app.adapters import build_adapter
from app.core.config import get_source, load_sources
from app.core.models import TaskRecord

_CACHE_TTL = float(os.environ.get("CACHE_TTL_SECONDS", "300"))
_lock = threading.Lock()
_cache: Dict[str, Tuple[float, List[TaskRecord]]] = {}


def list_sources() -> List[Dict]:
    return [
        {"id": s["id"], "name": s.get("name", s["id"]), "type": s.get("type")}
        for s in load_sources()
    ]


def get_records(source_id: str, *, force: bool = False) -> List[TaskRecord]:
    now = time.time()
    with _lock:
        cached = _cache.get(source_id)
        if not force and cached and (now - cached[0]) < _CACHE_TTL:
            return cached[1]

    # Fetch di luar lock (I/O lambat) lalu simpan.
    records = build_adapter(get_source(source_id)).fetch()
    with _lock:
        _cache[source_id] = (time.time(), records)
    return records


def refresh(source_id: str) -> int:
    records = get_records(source_id, force=True)
    return len(records)


def clear_cache() -> None:
    with _lock:
        _cache.clear()
