"""Render PDF dengan meng-convert DOCX via LibreOffice headless.

Keputusan proyek: PDF harus 1:1 dengan Word, jadi PDF diturunkan dari docx
yang sama (bukan render HTML terpisah). Membutuhkan `soffice` (LibreOffice)
tersedia di PATH atau di-set lewat env SOFFICE_BIN.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.report import ReportResult
from app.exporters.docx import render_docx


def _find_soffice() -> str:
    cand = os.environ.get("SOFFICE_BIN")
    if cand and Path(cand).exists():
        return cand
    for name in ("soffice", "soffice.exe", "libreoffice"):
        path = shutil.which(name)
        if path:
            return path
    # Lokasi default Windows.
    for p in (
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ):
        if Path(p).exists():
            return p
    raise RuntimeError(
        "LibreOffice (soffice) tidak ditemukan. Install LibreOffice atau set "
        "env SOFFICE_BIN. Diperlukan untuk export PDF (1:1 dengan Word)."
    )


def render_pdf(result: ReportResult) -> bytes:
    soffice = _find_soffice()
    docx_bytes = render_docx(result)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        src = tmp_path / "report.docx"
        src.write_bytes(docx_bytes)
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir",
             str(tmp_path), str(src)],
            check=True, capture_output=True, timeout=120,
            env={**os.environ, "HOME": str(tmp_path)},
        )
        pdf = tmp_path / "report.pdf"
        if not pdf.exists():
            raise RuntimeError("Konversi PDF gagal: file output tidak dibuat.")
        return pdf.read_bytes()
