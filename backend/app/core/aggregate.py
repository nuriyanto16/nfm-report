"""Agregasi ringkasan untuk laporan."""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Dict, List, Optional

from app.core.models import STATUS_CANONICAL, TANPA_STATUS, TaskRecord

# Jendela "utamakan dalam satu minggu" untuk carry over (hari sebelum `day`).
CARRY_OVER_WINDOW_DAYS = 7

# Batas bawah tetap untuk rincian harian (Isu/Solved/PR/Carry Over): issue yang
# DIBUKA sebelum tanggal ini diabaikan sepenuhnya, supaya backlog lama (mis.
# Jan-Jun 2026) tidak "nyangkut" di angka laporan harian. Diminta user 2026-07.
DAILY_DATA_FLOOR = date(2026, 7, 1)


def summarize(records: List[TaskRecord]) -> Dict:
    by_status = Counter(r.status for r in records)
    by_aplikasi = Counter(r.aplikasi or "(lainnya)" for r in records)
    by_pic = Counter((r.pic or "(tanpa PIC)") for r in records)

    # Urutkan status mengikuti urutan kanonik, sisanya di belakang.
    order = STATUS_CANONICAL + [TANPA_STATUS]
    status_sorted = {s: by_status[s] for s in order if s in by_status}
    for s, c in by_status.items():
        status_sorted.setdefault(s, c)

    # Rincian per-PIC menurut status (untuk halaman Monitoring Progress).
    # {pic: {"total": n, "by_status": {status: count}, "rows_by_status": {status: [{...}]}}}
    # `rows_by_status` dipakai popover detail saat angka di tabel diklik —
    # menyertakan tanggal lengkap, Request By, & sheet/bulan asal supaya bisa
    # ditelusuri tanpa buka laporan lain.
    pic_breakdown: Dict[str, Dict] = {}
    for pic, _ in by_pic.most_common():
        pic_breakdown[pic] = {"total": 0, "by_status": {}, "rows_by_status": {}}
    for r in records:
        pic = r.pic or "(tanpa PIC)"
        entry = pic_breakdown[pic]
        entry["total"] += 1
        entry["by_status"][r.status] = entry["by_status"].get(r.status, 0) + 1
        entry["rows_by_status"].setdefault(r.status, []).append({
            "no": int(r.no) if r.no is not None else None,
            "issue": r.issue,
            "source_month": r.source_month,
            "request_by": r.request_by,
            "tgl_request": r.tgl_request.isoformat() if r.tgl_request else None,
            "tgl_mulai": r.tgl_mulai.isoformat() if r.tgl_mulai else None,
            "tgl_estimasi": r.tgl_estimasi.isoformat() if r.tgl_estimasi else None,
            "tgl_selesai": r.tgl_selesai.isoformat() if r.tgl_selesai else None,
        })

    return {
        "total": len(records),
        "by_status": status_sorted,
        "by_aplikasi": dict(by_aplikasi.most_common()),
        "by_pic": dict(by_pic.most_common()),
        "by_pic_status": pic_breakdown,
    }


def daily_breakdown(
    records: List[TaskRecord],
    day: date,
    all_records: Optional[List[TaskRecord]] = None,
) -> Dict:
    """Rincian laporan harian untuk `day`.

    `records` = baris hasil filter periode harian (dipakai utk `total`).
    `all_records` = seluruh record (sudah kena filter dimensi, TANPA filter
    periode) — dipakai menghitung isu/solved/pr/carry over karena bisa
    menjangkau tanggal di luar `day`. Bila tidak diberikan, jatuh balik ke
    `records`.

    Definisi flag:
    - pr         : SEMUA issue (sejak `DAILY_DATA_FLOOR`) yang BELUM selesai
                   s/d `day`, apapun tanggal dibukanya — bukan cuma yang
                   dibuka dalam 7 hari terakhir. Sebelum koreksi 2026-07-17,
                   `pr` dibatasi jendela 7 hari (day-6..day) sehingga backlog
                   yang lebih tua (mis. issue #33, dibuka 10 Jul, masih
                   Progress) hilang dari Isu/PR di laporan & share WA — hanya
                   nongol di kartu "Carry Over" pada halaman web. Sekarang
                   backlog lama TETAP masuk PR/Isu selama belum selesai.
    - isu        : Issue yang MUNCUL hari ini (tgl_request == day) DIGABUNG
                   dengan `pr` (semua issue yang masih belum selesai) DAN
                   `solved` (selesai hari ini) — union tanpa duplikat.
    - solved     : Issue yang SELESAI hari ini (tgl_selesai == day), APAPUN
                   tanggal dibukanya (issue baru hari ini yang lgs kelar,
                   maupun PR/backlog lama yang baru kelar hari ini).
    - pr_solved  : SUBSET dari solved — yang dibuka SEBELUM hari ini (bukan
                   issue baru hari ini), utk penanda "PR lama akhirnya solved".
    - carry_over : SUBSET dari `pr` — issue yang masuk SEBELUM jendela minggu
                   ini (>6 hari) dan masih belum selesai s/d `day`. Dulu
                   dikecualikan dari `pr`/Isu & share WA; sekarang cuma
                   penanda "PR yang sudah menumpuk lama" (dipakai kartu
                   ringkasan web & marker ⏳ di share WA), TETAP ikut
                   terhitung di `pr`/`isu`.

    Issue yang tgl_request-nya SEBELUM `DAILY_DATA_FLOOR` diabaikan sepenuhnya
    dari seluruh flag di atas, supaya backlog lama tidak membanjiri laporan.

    Menyertakan daftar nomor issue (`*_no`) DAN baris penuh (`*_rows`) karena
    jendela lebih lebar dari periode harian sehingga tak semua row ada di
    `records`/`rows` laporan.
    """
    pool = all_records if all_records is not None else records
    pool = [
        r for r in pool
        if (req := r.date_for("tgl_request")) is not None and req >= DAILY_DATA_FLOOR
    ]
    window_start = day - timedelta(days=CARRY_OVER_WINDOW_DAYS - 1)

    today_new, pr, solved, carry_over = [], [], [], []
    for r in pool:
        req = r.date_for("tgl_request")
        done = r.date_for("tgl_selesai")
        if req == day:
            today_new.append(r)
        still_open = done is None or done > day
        if req <= day and still_open:
            pr.append(r)
            if req < window_start:
                carry_over.append(r)
        if done == day:
            solved.append(r)

    # Isu = baru hari ini, ATAU masih PR minggu ini, ATAU selesai hari ini
    # (union tanpa duplikat) — issue yang baru SELESAI hari ini harus tetap
    # terhitung sbg Isu meski sudah tidak lolos syarat `pr` (done == day,
    # bukan lagi "belum selesai"). Tanpa ini Solved+PR != Isu.
    seen = set()
    isu: List[TaskRecord] = []
    for r in today_new + pr + solved:
        if id(r) not in seen:
            seen.add(id(r))
            isu.append(r)

    # PR Solved = subset dari solved yang dibuka SEBELUM hari ini (backlog
    # lama yang baru kelar hari ini), bukan issue baru hari ini yang lgs solved.
    pr_solved = [r for r in solved if r.date_for("tgl_request") != day]

    def sort_rows(rs: List[TaskRecord]) -> List[TaskRecord]:
        return sorted(
            rs, key=lambda r: (r.date_for("tgl_request") or date.min, r.no or 0)
        )

    isu, solved, pr, pr_solved, carry_over = (
        sort_rows(isu), sort_rows(solved), sort_rows(pr),
        sort_rows(pr_solved), sort_rows(carry_over),
    )

    def nos(rs: List[TaskRecord]) -> List[int]:
        return [int(r.no) for r in rs if r.no is not None]

    def dump(rs: List[TaskRecord]) -> List[Dict]:
        return [r.model_dump() for r in rs]

    return {
        "total": len(records),
        "window_start": window_start.isoformat(),
        "window_end": day.isoformat(),
        "isu": len(isu),
        "solved": len(solved),
        "pr": len(pr),
        "pr_solved": len(pr_solved),
        "carry_over": len(carry_over),
        "isu_no": nos(isu),
        "solved_no": nos(solved),
        "pr_no": nos(pr),
        "pr_solved_no": nos(pr_solved),
        "carry_over_no": nos(carry_over),
        "isu_rows": dump(isu),
        "solved_rows": dump(solved),
        "pr_rows": dump(pr),
        "carry_over_rows": dump(carry_over),
    }
