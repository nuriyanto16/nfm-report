# Implementation Plan — Aplikasi Penarik Laporan SIMPEL NEXTGEN

> Aplikasi untuk menarik / merekap laporan kegiatan dari sumber data existing
> (Google Sheet "SUMMARY PEMELIHARAAN SIMPEL NEXTGEN") dan meng-export-nya ke
> **XLSX / PDF / Word** dengan tarikan **per Hari, per Minggu, per Bulan** serta
> **filter status yang dinamis**.

---

## 1. Tujuan & Ruang Lingkup

Membangun aplikasi web internal yang:

1. **Menarik data laporan** dari sumber existing secara dinamis (saat ini Google
   Sheet, ke depan bisa sumber lain).
2. Menyediakan **3 menu tarik laporan**:
   - **Per Hari** — rekap aktivitas/task pada tanggal tertentu.
   - **Per Minggu** — rekap rentang 7 hari (Senin–Minggu / custom).
   - **Per Bulan** — rekap satu bulan penuh (mengikuti tab bulanan di sheet).
3. **Export** ke format yang sama seperti folder `LAPORAN/` saat ini:
   - `.xlsx` (rekap tabel)
   - `.pdf` (laporan siap cetak)
   - `.docx` (laporan Word)
4. **Filter dinamis berdasarkan status** (Done, Progress, Hold, Back Log, To Do)
   dan dimensi lain (PIC, Kategori, Priority, Status Deploy, Aplikasi/section).
5. **Sumber data dinamis** — URL/ID spreadsheet & mapping kolom dapat diganti
   lewat konfigurasi tanpa ubah kode.

### Acuan output existing (`LAPORAN/`)
- `Rekap_Task_Outstanding_SIMPEL_NEXTGEN_Jan-Jun_2026.xlsx`
- `Laporan_Task_Outstanding_SIMPEL_NEXTGEN_Jan-Jun_2026.docx`
- `Laporan_Task_Outstanding_SIMPEL_NEXTGEN_Jan-Jun_2026.pdf`

Format & layout export baru harus konsisten dengan ketiga file ini.

---

## 2. Sumber Data (Existing)

**Spreadsheet:** "SUMMARY PEMELIHARAAN SIMPEL NEXTGEN 2026"
`https://docs.google.com/spreadsheets/d/1T1dVSovHhNoyj74HPcOEr72rUu2wljpDZgvJQRMwEhg/edit`

Download semua tab tanpa auth (sheet di-share publik):
```
GET https://docs.google.com/spreadsheets/d/<ID>/export?format=xlsx
```

### Struktur sheet bulanan (`01. Jan 2026` … `06. Juni 2026`)
- Header di **baris 3**, data mulai **baris 4**.
- Kolom:

  | Kol | Field | Kol | Field |
  |-----|-------|-----|-------|
  | A | NO | I | PIC |
  | B | ISSUE | J | KATEGORI |
  | C | PATH MENU | K | **STATUS** |
  | D | TGL REQUEST | L | PRIORITY |
  | E | TGL MULAI | M | STATUS DEPLOY |
  | F | TGL ESTIMASI SELESAI | N | Last Update |
  | G | TGL SELESAI | P | KETERANGAN |
  | H | REQUEST BY | | |

- **Section marker** di kolom A: `1. Pengujian` (=SIMPEL), `2. Kalibrasi`,
  `3. Mobile`, `4. Infra`.
- **STATUS valid:** `Done`, `Progress`, `Hold`, `Back Log`, `To Do`.
- **Aturan parsing (penting):**
  - Hanya ambil baris di mana **kolom A numerik** dan **kolom B tidak kosong**.
  - Buang baris `STATUS` (header berulang) dan baris numerik mini-recap (noise).
  - **Berhenti parsing** saat ketemu blok kedua `CHANGE REQUEST...` →
    `BULAN DESEMBER 2025` (aplikasi legacy non-SIMS: CAT, ISR QR Code, Antrian
    Online, SERENA, SIPUT, Seenow) agar tidak double-count.

> Aturan di atas akan diabstraksi menjadi **adapter** sehingga sumber/mapping
> kolom bisa dikonfigurasi (lihat §5).

---

## 3. Rekomendasi Tech Stack

Pertimbangan utama: **ringan**, mudah deploy on-prem, dan ekosistem **export
xlsx/pdf/docx** yang matang. Inti aplikasi adalah *parsing spreadsheet +
generate dokumen* — di sinilah Python unggul jauh.

### ✅ Rekomendasi (dipilih)

| Layer | Pilihan | Alasan |
|-------|---------|--------|
| **Backend** | **Python + FastAPI** | Async, ringan, ekosistem export terbaik: `openpyxl`/`pandas` (xlsx), `python-docx` (Word), `WeasyPrint`/`docxtpl→LibreOffice` (PDF). Parsing sheet jadi trivial. |
| **Frontend** | **Nuxt 3 (Vue 3) + Nuxt UI / Tailwind** | Ringan, SSR opsional, DX bagus, sesuai preferensi. Komponen tabel + filter cepat dibuat. |
| **HTTP/State FE** | `$fetch` / Pinia | Bawaan Nuxt, tanpa dependency berat. |
| **Container** | Docker Compose (api + web) | Deploy on-prem sederhana. |

### Kenapa **bukan Go** untuk backend?
Go memang lebih "enteng" untuk runtime, tapi ekosistem generate **Word & PDF**
jauh lebih lemah (`excelize` bagus untuk xlsx, tapi docx/pdf perlu kerja
manual / LibreOffice headless). Karena fitur inti = export 3 format dari data
spreadsheet, **Python lebih cepat selesai & lebih maintainable**. Go cocok bila
nanti butuh service throughput tinggi — tidak relevan untuk tool rekap internal.

### Alternatif "all-in-one" (bila ingin 1 bahasa)
- **Nuxt 3 (Nitro server) full TypeScript** — pakai `exceljs` (xlsx), `docx`
  (Word), `puppeteer`/`playwright` (PDF dari HTML). Valid bila tim lebih kuat
  JS, tapi PDF via headless Chromium lebih berat dari WeasyPrint.

### Libraries kunci (stack terpilih)
```
Backend (Python):
  fastapi, uvicorn          # web
  httpx                     # download sheet (export?format=xlsx)
  openpyxl / pandas         # baca sheet + tulis xlsx
  python-docx / docxtpl     # generate .docx (sumber tunggal laporan)
  LibreOffice (soffice)     # convert docx→pdf (1:1 dgn Word) — bukan lib pip
  jinja2                    # opsional, templating konten docx
  pydantic-settings         # config sumber data dinamis

Frontend (Nuxt 3):
  @nuxt/ui / tailwindcss    # UI + tabel + filter
  pinia                     # state filter
  dayjs                     # util tanggal (hari/minggu/bulan)
```

---

## 4. Arsitektur

```
┌─────────────────────┐        REST/JSON        ┌──────────────────────────┐
│   Nuxt 3 Frontend    │  ───────────────────►   │     FastAPI Backend       │
│  - Menu Harian       │                         │                          │
│  - Menu Mingguan     │   GET /api/report       │  ┌────────────────────┐  │
│  - Menu Bulanan      │   GET /api/export/...    │  │  SourceAdapter     │  │
│  - Filter dinamis    │   GET /api/filters       │  │  (GoogleSheet)     │  │
│  - Preview tabel     │   GET /api/sources       │  └─────────┬──────────┘  │
└─────────────────────┘                         │            │ download    │
                                                 │            ▼             │
                                                 │  ┌────────────────────┐  │
                                                 │  │  Parser/Normalizer │  │
                                                 │  │  → list[TaskRecord]│  │
                                                 │  └─────────┬──────────┘  │
                                                 │            ▼             │
                                                 │  ┌────────────────────┐  │
                                                 │  │ Aggregator (D/W/M) │  │
                                                 │  │ + Filter engine    │  │
                                                 │  └─────────┬──────────┘  │
                                                 │            ▼             │
                                                 │  ┌────────────────────┐  │
                                                 │  │ Exporter            │  │
                                                 │  │ xlsx / pdf / docx   │  │
                                                 │  └────────────────────┘  │
                                                 └──────────────────────────┘
                                                       ▲ cache (sheet xlsx, TTL)
```

### Model data internal (`TaskRecord`)
Hasil normalisasi dari semua tab bulanan menjadi satu list seragam:
```python
TaskRecord:
  no: int
  issue: str
  path_menu: str | None
  tgl_request / tgl_mulai / tgl_estimasi / tgl_selesai: date | None
  request_by: str | None
  pic: str | None
  kategori: str | None
  status: Literal["Done","Progress","Hold","Back Log","To Do"]
  priority: str | None
  status_deploy: str | None
  last_update: date | None
  keterangan: str | None
  aplikasi: str        # dari section marker (Pengujian/Kalibrasi/Mobile/Infra)
  source_month: str    # nama tab bulan
```

---

## 5. Sumber Data Dinamis (Konfigurasi)

Abstraksi `SourceAdapter` agar sumber bisa diganti tanpa ubah kode inti.

`config/sources.yaml`:
```yaml
sources:
  - id: simpel-nextgen-2026
    name: "SUMMARY PEMELIHARAAN SIMPEL NEXTGEN 2026"
    type: google_sheet
    spreadsheet_id: "1T1dVSovHhNoyj74HPcOEr72rUu2wljpDZgvJQRMwEhg"
    sheet_pattern: '^\d{2}\. .+ 2026$'   # cocokkan tab bulanan
    layout:
      header_row: 3
      data_start_row: 4
      columns: { no: A, issue: B, path_menu: C, tgl_request: D, tgl_mulai: E,
                 tgl_estimasi: F, tgl_selesai: G, request_by: H, pic: I,
                 kategori: J, status: K, priority: L, status_deploy: M,
                 last_update: N, keterangan: P }
      section_markers: ["1. Pengujian","2. Kalibrasi","3. Mobile","4. Infra"]
      stop_marker: "CHANGE REQUEST"      # berhenti sebelum blok legacy
      valid_status: ["Done","Progress","Hold","Back Log","To Do"]
```
Interface: `SourceAdapter.fetch() -> list[TaskRecord]`. Implementasi pertama
`GoogleSheetAdapter`; penambahan sumber baru = adapter baru, UI memilih dari
`GET /api/sources`.

---

## 6. Logika Periode (Harian / Mingguan / Bulanan)

Dasar penanggalan memakai **`Tgl Request`** (kolom D) sebagai acuan default —
laporan = task yang *masuk/di-request* pada periode tersebut. Kolom acuan lain
(`tgl_selesai`, `tgl_mulai`, `last_update`) tetap dapat dipilih lewat parameter
`date_field`.

- **Harian:** `date == ?date` → contoh tarik 2026-06-27.
- **Mingguan:** `week_start <= date <= week_end` (default Senin–Minggu; bisa
  custom range).
- **Bulanan:** filter `month == ?month` **atau** langsung pakai data tab bulanan
  (`source_month`). Mengikuti perilaku rekap existing.

Setiap mode menghasilkan: **daftar task** + **ringkasan agregat** (count per
status, per aplikasi, per PIC).

---

## 7. API Design (FastAPI)

```
GET  /api/sources
        → daftar sumber yang tersedia (dari sources.yaml)

GET  /api/filters?source=simpel-nextgen-2026
        → nilai distinct untuk filter dinamis
          { status:[...], pic:[...], kategori:[...], priority:[...],
            status_deploy:[...], aplikasi:[...], months:[...] }

GET  /api/report?source=&period=daily|weekly|monthly
        &date=YYYY-MM-DD            # daily
        &week_start=YYYY-MM-DD      # weekly (opsional, default minggu berjalan)
        &month=YYYY-MM              # monthly
        &date_field=tgl_request|tgl_selesai|tgl_mulai|last_update   # default: tgl_request
        &status=Done,Progress       # filter dinamis (multi, comma-sep)
        &pic=&kategori=&priority=&status_deploy=&aplikasi=
        → { meta:{...}, summary:{ by_status:{}, by_aplikasi:{}, by_pic:{} },
            rows:[ TaskRecord... ] }

GET  /api/export?<param sama spt /api/report>&format=xlsx|pdf|docx
        → file download (Content-Disposition), nama mengikuti pola existing:
          Rekap_<scope>_SIMPEL_NEXTGEN_<periode>.<ext>

POST /api/refresh?source=...        # invalidasi cache, tarik ulang sheet
```

Filter bersifat **dinamis & komposabel**: query engine menerima dict filter →
diterapkan ke list `TaskRecord`. Menambah dimensi filter cukup tambah field di
mapping, tidak perlu endpoint baru.

---

## 8. Export (samakan dengan `LAPORAN/`)

| Format | Library | Catatan |
|--------|---------|---------|
| **XLSX** | `openpyxl` | Header berwarna, freeze pane, autofilter, sheet "Rekap" + "Summary". Tiru gaya `Rekap_Task_Outstanding_*.xlsx`. |
| **DOCX** | `python-docx` (+`docxtpl` bila perlu template) | Judul, periode, tabel task, ringkasan status. Tiru `Laporan_Task_Outstanding_*.docx`. |
| **PDF** | **docx → PDF via LibreOffice headless** (`soffice --headless --convert-to pdf`) | **Dipilih: PDF harus 1:1 dengan Word.** PDF di-generate dari file `.docx` yang sama, sehingga layout identik. Konsekuensi: LibreOffice harus tersedia di server/Docker image. |

Karena PDF diturunkan dari docx, **docx adalah satu-satunya template laporan**
(dibangun via `python-docx`/`docxtpl`) → konsistensi 1:1 antara Word dan PDF
otomatis terjaga. (WeasyPrint/HTML tidak dipakai untuk laporan utama.)

---

## 9. Struktur Proyek

```
SIMPEL-NEXTGEN-BBPPT/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + routes
│   │   ├── api/                 # routers: sources, filters, report, export
│   │   ├── adapters/
│   │   │   ├── base.py          # SourceAdapter interface
│   │   │   └── google_sheet.py  # parsing sesuai §2
│   │   ├── core/
│   │   │   ├── models.py        # TaskRecord (pydantic)
│   │   │   ├── periods.py       # daily/weekly/monthly
│   │   │   ├── filters.py       # filter engine dinamis
│   │   │   └── aggregate.py     # summary by status/pic/aplikasi
│   │   ├── exporters/
│   │   │   ├── xlsx.py
│   │   │   ├── docx.py          # template laporan tunggal
│   │   │   └── pdf.py           # docx → pdf via LibreOffice headless
│   │   ├── auth.py              # HTTP Basic auth (dependency FastAPI)
│   │   └── config/sources.yaml
│   ├── tests/                   # unit test parser + filter + export
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # Nuxt 3
│   ├── pages/
│   │   ├── index.vue
│   │   ├── harian.vue
│   │   ├── mingguan.vue
│   │   └── bulanan.vue
│   ├── components/
│   │   ├── FilterBar.vue        # filter status dll (dinamis dari /api/filters)
│   │   ├── ReportTable.vue
│   │   ├── SummaryCards.vue
│   │   └── ExportButtons.vue    # xlsx / pdf / docx
│   ├── composables/useReport.ts
│   └── nuxt.config.ts
├── LAPORAN/                     # output existing (acuan format)
├── docker-compose.yml
└── implementation.md
```

---

## 10. Tahapan Pengerjaan (Milestones)

1. **M1 — Backend parsing & model.** GoogleSheetAdapter download + parse semua
   tab bulanan → `list[TaskRecord]`; unit test dengan aturan noise/stop-marker
   (§2). Output JSON benar = pondasi semua fitur.
2. **M2 — Period + filter engine + agregasi.** Endpoint `/api/report` &
   `/api/filters` untuk daily/weekly/monthly + filter status dinamis.
3. **M3 — Exporter xlsx.** Samakan dengan `Rekap_Task_Outstanding_*.xlsx`.
4. **M4 — Exporter docx & pdf.** Template Jinja2 bersama; verifikasi visual vs
   file existing.
5. **M5 — Frontend Nuxt.** 3 menu (harian/mingguan/bulanan), FilterBar dinamis,
   tabel preview, tombol export.
6. **M6 — Konfigurasi sumber dinamis + cache + refresh.** `sources.yaml`,
   cache xlsx (TTL), endpoint refresh.
7. **M7 — Basic auth + Dockerize & deploy.** HTTP Basic auth (env var),
   docker-compose (api+web, image backend sudah include LibreOffice), README.

---

## 11. Keputusan & Catatan

**Keputusan yang sudah ditetapkan:**
- **Acuan tanggal Harian/Mingguan/Bulanan:** **`Tgl Request`** (kolom D) sebagai
  default; kolom acuan lain tetap bisa dipilih via `date_field`.
- **PDF:** harus **1:1 dengan Word** → di-generate dari docx via **LibreOffice
  headless** (LibreOffice masuk ke Docker image backend).
- **Autentikasi:** **HTTP Basic auth** di level aplikasi (kredensial dari env
  var, dependency FastAPI di semua endpoint).

**Masih perlu dikonfirmasi nanti:**
- **Sumber selain Google Sheet** (mis. database SIMPEL langsung) — abstraksi
  `SourceAdapter` sudah disiapkan agar tinggal tambah adapter.
```

