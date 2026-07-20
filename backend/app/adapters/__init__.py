"""Registry adapter sumber data.

Menambah sumber jenis baru = buat kelas turunan SourceAdapter lalu daftarkan
di ADAPTERS dengan kunci = nilai `type` pada sources.yaml.
"""
from __future__ import annotations

from typing import Any, Dict

from .base import SourceAdapter
from .google_sheet import GoogleSheetAdapter

ADAPTERS = {
    "google_sheet": GoogleSheetAdapter,
}


def build_adapter(source: Dict[str, Any]) -> SourceAdapter:
    stype = source.get("type")
    if stype not in ADAPTERS:
        raise ValueError(f"Tipe sumber tidak didukung: {stype!r}")
    return ADAPTERS[stype](source)


__all__ = ["SourceAdapter", "GoogleSheetAdapter", "build_adapter", "ADAPTERS"]
