"""Dispatcher exporter laporan ke xlsx / pdf / docx."""
from __future__ import annotations

import re
import unicodedata
from typing import Tuple

from app.core.report import ReportResult

EXPORT_FORMATS = ["xlsx", "pdf", "docx"]

_MEDIA = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}


def build_filename(result: ReportResult, ext: str) -> str:
    scope = {"daily": "Harian", "weekly": "Mingguan", "monthly": "Bulanan"}.get(
        result.period.mode, result.period.mode
    )
    label = result.period.label
    raw = f"FastReport_{result.source_id}_{scope}_{label}"
    slug = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9]+", "_", slug).strip("_")
    return f"{slug}.{ext}"


def export_report(result: ReportResult, fmt: str) -> Tuple[bytes, str, str]:
    """Kembalikan (content_bytes, filename, media_type)."""
    if fmt == "xlsx":
        from app.exporters.xlsx import render_xlsx
        content = render_xlsx(result)
    elif fmt == "docx":
        from app.exporters.docx import render_docx
        content = render_docx(result)
    elif fmt == "pdf":
        from app.exporters.pdf import render_pdf
        content = render_pdf(result)
    else:
        raise ValueError(f"Format tidak didukung: {fmt}")
    return content, build_filename(result, fmt), _MEDIA[fmt]
