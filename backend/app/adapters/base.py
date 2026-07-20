"""Kontrak adapter sumber data."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.core.models import TaskRecord


class SourceAdapter(ABC):
    """Setiap sumber data mengimplementasikan ini.

    Tujuannya: apa pun bentuk sumbernya (Google Sheet, DB, CSV, API),
    keluarannya selalu `list[TaskRecord]` yang seragam.
    """

    def __init__(self, source: Dict[str, Any]):
        self.source = source
        self.source_id = source.get("id", "")
        self.name = source.get("name", self.source_id)

    @abstractmethod
    def fetch(self) -> List[TaskRecord]:
        """Tarik & normalisasi seluruh data sumber menjadi TaskRecord."""
        raise NotImplementedError
