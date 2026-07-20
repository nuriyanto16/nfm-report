"""Unit test parser GoogleSheetAdapter (hermetik, pakai xlsx sintetis)."""
from __future__ import annotations

import os

import pytest

from app.adapters.google_sheet import GoogleSheetAdapter
from app.core.models import TANPA_STATUS


def test_parses_only_valid_data_rows(synthetic_source):
    recs = GoogleSheetAdapter(synthetic_source).fetch()
    issues = [r.issue for r in recs]

    # Baris valid dari Juni (3 Pengujian + 1 Kalibrasi) + 1 Mei.
    assert "Bug notifikasi WA" in issues
    assert "Kalibrasi fitur copy" in issues
    assert "Task Mei" in issues
    # Noise & legacy tidak ikut.
    assert "JANGAN ikut terhitung (legacy)" not in issues
    assert all("STATUS" != i for i in issues)
    # 5 baris valid dari Juni + 1 dari Mei; baris ISSUE kosong & noise di-skip.
    assert len(recs) == 6


def test_stops_at_legacy_block(synthetic_source):
    recs = GoogleSheetAdapter(synthetic_source).fetch()
    assert not any("legacy" in r.issue.lower() for r in recs)
    assert all(r.source_month in ("06. Juni 2026", "05. Mei 2026") for r in recs)


def test_section_marker_sets_aplikasi(synthetic_source):
    recs = GoogleSheetAdapter(synthetic_source).fetch()
    by_issue = {r.issue: r for r in recs}
    assert by_issue["Bug notifikasi WA"].aplikasi == "Pengujian (SIMPEL)"
    assert by_issue["Kalibrasi fitur copy"].aplikasi == "Kalibrasi"


def test_status_normalized_and_blank_handled(synthetic_source):
    recs = GoogleSheetAdapter(synthetic_source).fetch()
    by_issue = {r.issue: r for r in recs}
    assert by_issue["Bug notifikasi WA"].status == "Done"
    assert by_issue["Tambah fitur export"].status == "Progress"
    assert by_issue["Cek log email"].status == "Back Log"
    assert by_issue["Issue tanpa status"].status == TANPA_STATUS


def test_dates_and_metadata(synthetic_source):
    recs = GoogleSheetAdapter(synthetic_source).fetch()
    r = {x.issue: x for x in recs}["Bug notifikasi WA"]
    assert r.tgl_request is not None
    assert r.date_for("tgl_request").isoformat() == "2026-06-03"
    assert r.pic == "Hasan"
    assert r.source_id == "test-src"


def test_blank_request_date_is_none(synthetic_source):
    recs = GoogleSheetAdapter(synthetic_source).fetch()
    r = {x.issue: x for x in recs}["Cek log email"]
    assert r.tgl_request is None
    assert r.date_for("tgl_request") is None


# --- integration opsional terhadap sheet asli --------------------------------
REAL = os.environ.get("REAL_SHEET_PATH")


@pytest.mark.skipif(not REAL, reason="set REAL_SHEET_PATH untuk uji sheet asli")
def test_real_sheet_smoke():
    src = {
        "id": "simpel-nextgen-2026",
        "type": "google_sheet",
        "local_path": REAL,
        "sheet_pattern": r"^\d{2}\. .+ \d{4}$",
        "layout": {
            "data_start_row": 4,
            "columns": {
                "no": 0, "issue": 1, "path_menu": 2, "tgl_request": 3,
                "tgl_mulai": 4, "tgl_estimasi": 5, "tgl_selesai": 6,
                "request_by": 7, "pic": 8, "kategori": 9, "status": 10,
                "priority": 11, "status_deploy": 12, "last_update": 13,
                "keterangan": 15,
            },
            "section_markers": {
                "1. Pengujian": "Pengujian (SIMPEL)",
                "2. Kalibrasi": "Kalibrasi",
                "3. Mobile": "Mobile",
                "4. Infra": "Infra",
            },
            "stop_markers": [
                "CHANGE REQUEST (CR)/FEEDBACK USER",
                "BULAN DESEMBER 2025",
            ],
        },
    }
    recs = GoogleSheetAdapter(src).fetch()
    assert len(recs) > 100
    # Tidak ada record dari blok legacy.
    assert not any("seenow" in (r.issue or "").lower() for r in recs)
    months = {r.source_month for r in recs}
    assert any("Juni" in m for m in months)
