"""Unit test untuk periods, filters, aggregate."""
from __future__ import annotations

from datetime import date as _date, datetime

from app.core.aggregate import daily_breakdown, summarize
from app.core.filters import apply_filters, distinct_values
from app.core.models import TaskRecord
from app.core.periods import filter_by_period, resolve_period


def _rec(**kw):
    return TaskRecord(**kw)


def _sample():
    return [
        _rec(no=1, issue="a", status="Done", pic="Hasan", aplikasi="Pengujian (SIMPEL)",
             tgl_request=datetime(2026, 6, 3, 9, 0)),
        _rec(no=2, issue="b", status="Progress", pic="Rijal", aplikasi="Pengujian (SIMPEL)",
             tgl_request=datetime(2026, 6, 10, 9, 0)),
        _rec(no=3, issue="c", status="Done", pic="Rijal", aplikasi="Kalibrasi",
             tgl_request=datetime(2026, 6, 30, 9, 0)),
        _rec(no=4, issue="d", status="Hold", pic="Mu'in", aplikasi="Kalibrasi",
             tgl_request=datetime(2026, 5, 20, 9, 0)),
    ]


def test_daily_period():
    p = resolve_period("daily", date="2026-06-03")
    rows = filter_by_period(_sample(), p)
    assert [r.no for r in rows] == [1]


def test_daily_includes_completed_that_day():
    # Task di-request 2026-06-01 tapi SELESAI 2026-06-10 harus ikut di laporan
    # harian 2026-06-10, walau tgl_request-nya bukan hari itu.
    recs = [
        _rec(no=1, issue="req hari itu", tgl_request=datetime(2026, 6, 10)),
        _rec(no=2, issue="selesai hari itu", tgl_request=datetime(2026, 6, 1),
             tgl_selesai=datetime(2026, 6, 10)),
        _rec(no=3, issue="tak relevan", tgl_request=datetime(2026, 6, 5),
             tgl_selesai=datetime(2026, 6, 6)),
    ]
    rows = filter_by_period(recs, resolve_period("daily", date="2026-06-10"))
    assert sorted(r.no for r in rows) == [1, 2]


def test_weekly_period():
    # Minggu 2026-06-01 (Senin) .. 2026-06-07
    p = resolve_period("weekly", week_start="2026-06-01")
    rows = filter_by_period(_sample(), p)
    assert [r.no for r in rows] == [1]
    assert p.end.isoformat() == "2026-06-07"


def test_monthly_period():
    p = resolve_period("monthly", month="2026-06")
    rows = filter_by_period(_sample(), p)
    assert sorted(r.no for r in rows) == [1, 2, 3]
    assert p.label == "Juni 2026"


def test_date_field_switch():
    recs = [_rec(no=1, issue="x", tgl_request=datetime(2026, 6, 1),
                 tgl_selesai=datetime(2026, 7, 5))]
    assert filter_by_period(recs, resolve_period("monthly", month="2026-06")) == recs
    assert filter_by_period(
        recs, resolve_period("monthly", month="2026-06", date_field="tgl_selesai")
    ) == []


def test_filters_multi_dimension():
    rows = apply_filters(_sample(), {"status": ["Done"], "pic": ["Rijal"]})
    assert [r.no for r in rows] == [3]


def test_filters_case_insensitive_and_empty():
    assert len(apply_filters(_sample(), {"status": ["done"]})) == 2
    assert len(apply_filters(_sample(), {"status": []})) == 4


def test_distinct_values():
    d = distinct_values(_sample())
    assert d["status"] == ["Done", "Hold", "Progress"]
    assert "Hasan" in d["pic"]


def test_summarize():
    s = summarize(_sample())
    assert s["total"] == 4
    assert s["by_status"]["Done"] == 2
    assert list(s["by_status"].keys())[0] == "Done"  # urutan kanonik


def test_all_period_includes_everything():
    # Periode "all" mengembalikan semua record, termasuk yang tanpa tanggal.
    recs = _sample() + [_rec(no=5, issue="e", status="Done")]  # tanpa tgl_request
    p = resolve_period("all")
    assert p.label == "Semua Waktu"
    rows = filter_by_period(recs, p)
    assert sorted(r.no for r in rows) == [1, 2, 3, 4, 5]


def test_summarize_by_pic_status():
    s = summarize(_sample())
    bps = s["by_pic_status"]
    assert bps["Rijal"]["total"] == 2
    assert bps["Rijal"]["by_status"] == {"Progress": 1, "Done": 1}
    assert bps["Hasan"]["by_status"]["Done"] == 1


def test_summarize_pic_tanpa_pic():
    recs = [_rec(no=1, issue="x", status="To Do")]  # pic None
    s = summarize(recs)
    assert s["by_pic_status"]["(tanpa PIC)"]["total"] == 1


def test_summarize_pic_rows_by_status_detail():
    # Detail popover: Bulan (source_month), No issue, Request By & tanggal
    # lengkap (request/mulai/estimasi/selesai) per sel status.
    recs = [
        _rec(no=1, issue="x", status="Hold", pic="Riki", source_month="06. Juni 2026",
             request_by="Pa Galih", tgl_request=datetime(2026, 6, 3, 9, 0),
             tgl_mulai=datetime(2026, 6, 4, 8, 0)),
        _rec(no=2, issue="y", status="Hold", pic="Riki", source_month="07. Juli 2026"),
    ]
    s = summarize(recs)
    rows = s["by_pic_status"]["Riki"]["rows_by_status"]["Hold"]
    assert [r["no"] for r in rows] == [1, 2]
    assert [r["source_month"] for r in rows] == ["06. Juni 2026", "07. Juli 2026"]
    assert rows[0]["request_by"] == "Pa Galih"
    assert rows[0]["tgl_request"] == "2026-06-03T09:00:00"
    assert rows[0]["tgl_mulai"] == "2026-06-04T08:00:00"
    assert rows[0]["tgl_estimasi"] is None and rows[0]["tgl_selesai"] is None
    assert rows[1]["request_by"] is None and rows[1]["tgl_request"] is None


def test_daily_breakdown_flags():
    # Definisi (dikoreksi user 2026-07-17 utk isu #33 (10 Jul, masih Progress)
    # yang sebelumnya hilang dari Isu/PR & share WA krn dibatasi jendela 7
    # hari; invarian: Solved + PR = Isu):
    # - Isu    : muncul HARI INI, ATAU masih PR (belum selesai, apapun umur
    #            backlog-nya), ATAU SELESAI hari ini (apapun tanggal
    #            dibukanya).
    # - Solved : selesai TEPAT hari ini, apapun tanggal dibukanya.
    # - PR     : SEMUA issue (sejak floor) yang belum selesai s/d hari ini,
    #            tidak dibatasi jendela minggu ini.
    # - PR Solved : subset Solved yg dibuka SEBELUM hari ini (bukan issue baru).
    # - Carry Over: SUBSET dari PR — dibuka SEBELUM jendela minggu ini, masih
    #            belum selesai (penanda backlog lama, tetap ikut PR/Isu).
    # (day=10 Juli supaya window_start=4 Juli, masih setelah DAILY_DATA_FLOOR
    # 1 Juli, jadi skenario carry over/pr_solved bisa diuji tanpa kena floor.)
    day = _date(2026, 7, 10)
    period_rows = [
        # masuk & selesai 10 Juli -> isu (baru hari ini) + solved
        _rec(no=60, issue="baru-selesai", tgl_request=datetime(2026, 7, 10),
             tgl_selesai=datetime(2026, 7, 10)),
        # masuk 10 Juli, belum selesai -> isu + pr
        _rec(no=67, issue="pr-a", tgl_request=datetime(2026, 7, 10)),
        _rec(no=68, issue="pr-b", tgl_request=datetime(2026, 7, 10)),
        # masuk 9 Juli (dlm jendela, BUKAN hari ini), selesai 10 Juli ->
        # solved + isu (baru kelar hari ini, walau dibuka kemarin) + pr_solved
        _rec(no=53, issue="masuk-minggu-lalu-solved-hari-ini",
             tgl_request=datetime(2026, 7, 9), tgl_selesai=datetime(2026, 7, 10)),
    ]
    # Masuk SEBELUM jendela (window_start = 4 Juli) tapi SETELAH floor (1 Juli),
    # belum selesai -> tetap isu + pr (skrg tak dibatasi jendela), DAN ditandai
    # carry_over krn di luar jendela minggu ini.
    carry = _rec(no=40, issue="open-lama", tgl_request=datetime(2026, 7, 2))
    # Backlog lama (di luar jendela minggu ini), baru SELESAI HARI INI ->
    # solved + isu (baru kelar hari ini) + pr_solved.
    old_solved_today = _rec(no=41, issue="lama-baru-selesai-hari-ini",
                             tgl_request=datetime(2026, 7, 2),
                             tgl_selesai=datetime(2026, 7, 10))
    # Masuk SEBELUM DAILY_DATA_FLOOR (1 Juli) -> harus diabaikan total, tidak
    # ikut isu/solved/pr/carry_over sama sekali.
    pre_floor = _rec(no=99, issue="backlog-sangat-lama",
                      tgl_request=datetime(2026, 6, 20))
    all_recs = period_rows + [carry, old_solved_today, pre_floor]

    b = daily_breakdown(period_rows, day, all_records=all_recs)
    assert b["total"] == 4
    assert b["window_start"] == "2026-07-04" and b["window_end"] == "2026-07-10"
    assert b["isu"] == 6 and sorted(b["isu_no"]) == [40, 41, 53, 60, 67, 68]
    assert b["solved"] == 3 and sorted(b["solved_no"]) == [41, 53, 60]
    assert b["pr"] == 3 and sorted(b["pr_no"]) == [40, 67, 68]
    assert b["pr_solved"] == 2 and sorted(b["pr_solved_no"]) == [41, 53]
    assert b["carry_over"] == 1 and b["carry_over_no"] == [40]
    assert len(b["carry_over_rows"]) == 1 and b["carry_over_rows"][0]["no"] == 40
    assert len(b["isu_rows"]) == 6 and len(b["solved_rows"]) == 3
    assert len(b["pr_rows"]) == 3
    assert 99 not in b["isu_no"] and 99 not in b["carry_over_no"] and 99 not in b["solved_no"]


def test_daily_breakdown_carry_over_window():
    # Backlog di luar jendela 7 hari tetap terhitung "pr" (dan Isu), tapi
    # ditandai "carry_over" sbg subset yg sudah lama menumpuk.
    day = _date(2026, 7, 10)
    within = _rec(no=1, issue="masih-minggu-ini",
                  tgl_request=datetime(2026, 7, 5))          # 5 hari lalu
    stale = _rec(no=2, issue="sudah-lama",
                 tgl_request=datetime(2026, 7, 1))           # tepat di floor, > 1 minggu
    b = daily_breakdown([], day, all_records=[within, stale])
    assert b["carry_over"] == 1 and b["carry_over_no"] == [2]
    assert b["pr"] == 2 and sorted(b["pr_no"]) == [1, 2]


def test_daily_breakdown_data_floor():
    # Issue yang dibuka SEBELUM DAILY_DATA_FLOOR (1 Juli 2026) diabaikan total,
    # bahkan sebagai carry over, supaya backlog lama tidak membanjiri laporan.
    day = _date(2026, 7, 10)
    pre_floor_open = _rec(no=1, issue="backlog-lama", tgl_request=datetime(2026, 5, 1))
    pre_floor_solved = _rec(no=2, issue="lama-solved",
                             tgl_request=datetime(2026, 5, 1),
                             tgl_selesai=datetime(2026, 7, 9))
    b = daily_breakdown([], day, all_records=[pre_floor_open, pre_floor_solved])
    assert b["isu"] == 0 and b["solved"] == 0 and b["pr"] == 0 and b["carry_over"] == 0


def test_daily_breakdown_no_carry_over_first_day():
    # Hari pertama: tidak ada carry over, isu/solved/pr = record hari itu saja.
    day = _date(2026, 7, 1)
    recs = [
        _rec(no=1, issue="a", tgl_request=datetime(2026, 7, 1),
             tgl_selesai=datetime(2026, 7, 1)),
        _rec(no=2, issue="b", tgl_request=datetime(2026, 7, 1)),
    ]
    b = daily_breakdown(recs, day)
    assert b["carry_over"] == 0 and b["carry_over_no"] == []
    assert b["isu"] == 2 and b["solved"] == 1 and b["pr"] == 1
