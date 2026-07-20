"""Loader konfigurasi sumber data (`config/sources.yaml`)."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import yaml

_DEFAULT = Path(__file__).resolve().parent.parent / "config" / "sources.yaml"


def _config_path() -> Path:
    return Path(os.environ.get("SOURCES_CONFIG", _DEFAULT))


@lru_cache(maxsize=1)
def load_sources() -> List[Dict[str, Any]]:
    path = _config_path()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("sources", [])


def get_source(source_id: str) -> Dict[str, Any]:
    for s in load_sources():
        if s.get("id") == source_id:
            return s
    raise KeyError(f"Sumber data tidak ditemukan: {source_id!r}")


def reset_config_cache() -> None:
    load_sources.cache_clear()
