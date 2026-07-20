# Aplikasi Penarik Laporan SIMPEL NEXTGEN

Aplikasi web untuk menarik & merekap laporan kegiatan dari sumber existing
(Google Sheet "SUMMARY PEMELIHARAAN SIMPEL NEXTGEN"), dengan tarikan **per Hari /
per Minggu / per Bulan**, **filter status (dan dimensi lain) yang dinamis**, serta
**export ke XLSX / Word / PDF** mengikuti format folder `LAPORAN/`.

Detail rancangan ada di [implementation.md](implementation.md).

## Arsitektur

| Layer | Teknologi |
|-------|-----------|
| Backend | Python + FastAPI (parsing sheet, period/filter/aggregate, exporter) |
| Frontend | Nuxt 3 (Vue 3) |
| Export | `openpyxl` (xlsx), `python-docx` (docx), LibreOffice headless (docx→pdf 1:1) |
| Sumber data | Dinamis via `backend/app/config/sources.yaml` (pola `SourceAdapter`) |

```
backend/   FastAPI + adapter + exporter (+ tests)
frontend/  Nuxt 3 (3 menu: Harian / Mingguan / Bulanan)
LAPORAN/   contoh output existing (acuan format)
```

## Menjalankan dengan Docker (paling mudah)

```bash
# (opsional) set kredensial basic auth
export BASIC_AUTH_USER=admin BASIC_AUTH_PASS=rahasia
docker compose up --build
```
- Frontend: http://localhost:3000
- API + dokumen Swagger: http://localhost:8000/docs

Image backend sudah memuat LibreOffice sehingga export PDF langsung jalan.

## Menjalankan manual (dev)

### Backend
```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Export PDF butuh LibreOffice. Bila tidak ada di PATH, set `SOFFICE_BIN`, mis.
`set SOFFICE_BIN=C:\Program Files\LibreOffice\program\soffice.exe`.

### Frontend
```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
```

### Test backend
```bash
cd backend
set PYTHONPATH=.
pytest -q
# uji terhadap sheet asli (opsional): set REAL_SHEET_PATH=path\ke\sheet.xlsx
```

## Endpoint utama

| Method | Path | Keterangan |
|--------|------|------------|
| GET | `/api/sources` | daftar sumber data |
| GET | `/api/filters?source=` | nilai distinct untuk filter dinamis |
| GET | `/api/report?source=&period=daily\|weekly\|monthly&...` | data + ringkasan |
| GET | `/api/export?...&format=xlsx\|pdf\|docx` | unduh laporan |
| POST | `/api/refresh?source=` | invalidasi cache, tarik ulang sheet |

Parameter periode: `date=YYYY-MM-DD` (daily), `week_start=YYYY-MM-DD` (weekly),
`month=YYYY-MM` (monthly). Acuan tanggal default `tgl_request`, dapat diganti via
`date_field`. Filter multi-nilai dipisah koma, mis. `status=Done,Progress`.

## Menambah sumber data baru

Tambahkan entri di [backend/app/config/sources.yaml](backend/app/config/sources.yaml).
Untuk jenis sumber baru (mis. database), buat adapter turunan `SourceAdapter` di
`backend/app/adapters/` lalu daftarkan di `ADAPTERS`.

## Keamanan

HTTP Basic auth aktif bila `BASIC_AUTH_USER` & `BASIC_AUTH_PASS` di-set (lihat
[backend/.env.example](backend/.env.example)). Tanpa itu, auth dilewati (dev).
