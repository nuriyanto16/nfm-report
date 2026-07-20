// State & aksi untuk satu halaman laporan (harian/mingguan/bulanan).
import { reactive, ref, computed } from "vue";

export interface ReportRow {
  no: number | null;
  issue: string;
  aplikasi: string;
  kategori: string | null;
  tgl_request: string | null;
  tgl_mulai: string | null;
  tgl_estimasi: string | null;
  tgl_selesai: string | null;
  pic: string | null;
  request_by: string | null;
  status: string;
  priority: string | null;
  status_deploy: string | null;
  keterangan: string | null;
  source_month: string;
}

export interface PicRowRef {
  no: number | null;
  issue: string;
  source_month: string;
  request_by: string | null;
  tgl_request: string | null;
  tgl_mulai: string | null;
  tgl_estimasi: string | null;
  tgl_selesai: string | null;
}

export interface PicBreakdown {
  total: number;
  by_status: Record<string, number>;
  rows_by_status: Record<string, PicRowRef[]>;
}

// Rincian harian: PR/Isu mencakup SEMUA backlog yang belum selesai (sejak
// DAILY_DATA_FLOOR), tidak dibatasi jendela 7 hari — lihat backend aggregate.py.
export interface DailyBreakdown {
  total: number;
  window_start: string;
  window_end: string;
  isu: number;         // baru hari ini + PR + selesai hari ini
  solved: number;      // selesai hari ini
  pr: number;          // semua yg belum selesai s/d hari ini
  pr_solved: number;   // backlog lama yang baru selesai hari ini
  carry_over: number;  // subset PR: backlog >1 minggu, masih belum selesai
  isu_no: number[];
  solved_no: number[];
  pr_no: number[];
  pr_solved_no: number[];
  carry_over_no: number[];
  isu_rows: ReportRow[];
  solved_rows: ReportRow[];
  pr_rows: ReportRow[];
  carry_over_rows: ReportRow[];
}

export interface ReportResponse {
  meta: any;
  summary: {
    total: number;
    by_status: Record<string, number>;
    by_aplikasi: Record<string, number>;
    by_pic: Record<string, number>;
    by_pic_status: Record<string, PicBreakdown>;
    daily?: DailyBreakdown;
  };
  rows: ReportRow[];
}

const FILTER_DIMS = ["status", "aplikasi", "pic", "kategori", "priority", "status_deploy"] as const;
type FilterDim = (typeof FILTER_DIMS)[number];

export function useReport(period: "daily" | "weekly" | "monthly") {
  const sources = ref<{ id: string; name: string }[]>([]);
  const source = ref<string>("");
  const dateField = ref<string>("tgl_request");

  const today = new Date().toISOString().slice(0, 10);
  const date = ref<string>(today);
  const weekStart = ref<string>(mondayOf(today));
  const month = ref<string>(today.slice(0, 7));

  const filterValues = ref<Record<string, string[]>>({});
  const selected = reactive<Record<FilterDim, string[]>>({
    status: [], aplikasi: [], pic: [], kategori: [], priority: [], status_deploy: [],
  });

  const data = ref<ReportResponse | null>(null);
  const loading = ref(false);
  const initializing = ref(true);
  const error = ref<string>("");

  async function loadSources() {
    const res = await apiGet<{ sources: { id: string; name: string }[] }>("/api/sources");
    sources.value = res.sources;
    if (!source.value && res.sources.length) source.value = res.sources[0].id;
  }

  async function loadFilters() {
    if (!source.value) return;
    const res = await apiGet<{ values: Record<string, string[]> }>("/api/filters", { source: source.value });
    filterValues.value = res.values;
  }

  function periodParams(extra?: Record<string, any>) {
    const p: Record<string, any> = { source: source.value, period, date_field: dateField.value };
    if (period === "daily") p.date = date.value;
    else if (period === "weekly") p.week_start = weekStart.value;
    else p.month = month.value;
    for (const dim of FILTER_DIMS) if (selected[dim].length) p[dim] = selected[dim];
    return { ...p, ...extra };
  }

  // `force` = tarik ulang data dari sumber (abaikan cache). Dipakai tombol
  // "Tarik Laporan"; watcher otomatis tetap pakai cache biar hemat.
  async function run(force = false) {
    if (!source.value) return;
    loading.value = true;
    error.value = "";
    try {
      data.value = await apiGet<ReportResponse>(
        "/api/report", periodParams(force ? { refresh: 1 } : undefined),
      );
    } catch (e: any) {
      error.value = e?.data?.detail || e?.message || "Gagal memuat laporan";
      data.value = null;
    } finally {
      loading.value = false;
    }
  }

  function toggle(dim: FilterDim, value: string) {
    const arr = selected[dim];
    const i = arr.indexOf(value);
    if (i >= 0) arr.splice(i, 1);
    else arr.push(value);
  }

  function resetFilters() {
    for (const dim of FILTER_DIMS) selected[dim] = [];
  }

  const downloading = ref<string>("");
  async function download(format: "xlsx" | "pdf" | "docx") {
    downloading.value = format;
    error.value = "";
    try {
      await downloadExport({ ...periodParams(), format });
    } catch (e: any) {
      error.value = e?.message || "Gagal mengunduh file";
    } finally {
      downloading.value = "";
    }
  }

  // Inisialisasi awal halaman: muat sumber + filter + laporan pertama.
  async function init() {
    initializing.value = true;
    try {
      await loadSources();
      await loadFilters();
      await run();
    } finally {
      initializing.value = false;
    }
  }

  const hasData = computed(() => !!data.value && data.value.rows.length > 0);

  // --- Export WhatsApp (salin ke clipboard) ---
  const copied = ref(false);
  function buildWaText(): string {
    const d = data.value;
    if (!d) return "";
    const title = TITLES[period];
    const lines: string[] = [];
    lines.push(`*FAST REPORT — ${d.meta.source_name}*`);
    lines.push(`_${title} — ${d.meta.period.label}_`);
    lines.push("");

    const daily = d.summary.daily;
    if (period === "daily" && daily) {
      // WA share menampilkan 3 kelompok: Isu, Solved, PR. Sejak koreksi
      // 2026-07-17 (isu #33, dibuka 10 Jul, sempat hilang dari WA krn
      // kepotong jendela 7 hari), backlog lama yang masih belum selesai
      // TETAP ikut PR/Isu — bukan cuma yang dibuka dalam seminggu terakhir.
      // - Isu    : issue yang muncul HARI INI + PR (semua yg belum selesai,
      //            apapun umurnya) + yang baru selesai hari ini.
      // - Solved : issue yang selesai TEPAT hari ini, baik yang baru dibuka
      //            hari ini maupun PR/backlog lama yang baru kelar hari ini.
      // - PR     : semua issue yang belum beres s/d hari ini (termasuk
      //            backlog lama / carry over, ditandai ⏳ di detail).
      lines.push(`*${waDayName(d.meta.period.start)}*`);
      lines.push(`- Isu: ${daily.isu}${waNos(daily.isu_no)}`);
      lines.push(`- Solved: ${daily.solved}${waNos(daily.solved_no)}`);
      lines.push(`- PR: ${daily.pr}${waNos(daily.pr_no)}`);

      // Detail dikelompokkan supaya jelas issue nomor berapa + sheet mana.
      const prSolvedSet = new Set(daily.pr_solved_no);
      const carryOverSet = new Set(daily.carry_over_no);
      const isuRows = daily.isu_rows || [];
      const solvedRows = daily.solved_rows || [];
      const prRows = daily.pr_rows || [];

      lines.push("");
      lines.push("Detail:");

      if (isuRows.length) {
        lines.push("");
        lines.push(`🆕 *Issue (${isuRows.length}):*`);
        for (const row of isuRows) {
          const co = row.no != null && carryOverSet.has(row.no) ? "⏳ " : "";
          lines.push(...waDetail(row, { prefix: co }));
        }
      }
      if (solvedRows.length) {
        lines.push("");
        lines.push(`✅ *Solved (${solvedRows.length}):*`);
        for (const row of solvedRows) {
          const co = row.no != null && prSolvedSet.has(row.no) ? "➰ " : "";
          lines.push(...waDetail(row, { prefix: co }));
        }
      }
      if (prRows.length) {
        lines.push("");
        lines.push(`📝 *PR (${prRows.length}):*`);
        for (const row of prRows) {
          const co = row.no != null && carryOverSet.has(row.no) ? "⏳ " : "";
          lines.push(...waDetail(row, { prefix: co }));
        }
      }
      if (prSolvedSet.size) {
        lines.push("");
        lines.push(`➰ _= issue lama (bukan baru hari ini) yang baru selesai hari ini._`);
      }
      if (carryOverSet.size) {
        lines.push("");
        lines.push(`⏳ _= backlog lama (>1 minggu) yang masih belum selesai._`);
      }
    } else {
      lines.push(`Total: *${d.summary.total}* task`);
      for (const [status, count] of Object.entries(d.summary.by_status)) {
        lines.push(`${STATUS_EMOJI[status] || "▫️"} ${status}: ${count}`);
      }
      if (d.rows.length) {
        lines.push("");
        lines.push("*Detail:*");
        for (const row of d.rows) lines.push(...waDetail(row));
      }
    }
    return lines.join("\n");
  }

  async function copyWhatsApp() {
    const text = buildWaText();
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Fallback bila Clipboard API tak tersedia (mis. http non-secure).
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  }

  return {
    FILTER_DIMS, sources, source, dateField, date, weekStart, month,
    filterValues, selected, data, loading, initializing, error, hasData, downloading,
    loadSources, loadFilters, run, toggle, resetFilters, download, init,
    copied, copyWhatsApp,
  };
}

const TITLES: Record<string, string> = {
  daily: "Laporan Harian",
  weekly: "Laporan Mingguan",
  monthly: "Laporan Bulanan",
};

const STATUS_EMOJI: Record<string, string> = {
  Done: "✅",
  Progress: "🔄",
  Hold: "⏸️",
  "Back Log": "📋",
  "To Do": "📝",
  "Tanpa Status": "❔",
};

const WA_MONTH_ID = [
  "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
  "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
];

const WA_DAY_ID = [
  "Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu",
];

// Nama hari (Indonesia) dari tanggal ISO "YYYY-MM-DD".
function waDayName(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso + "T00:00:00");
  if (isNaN(d.getTime())) return "";
  return WA_DAY_ID[d.getDay()];
}

// Daftar nomor issue -> " (#53, #67)"; kosong -> "".
function waNos(nos: number[]): string {
  if (!nos || !nos.length) return "";
  return ` (${nos.map((n) => `#${n}`).join(", ")})`;
}

// Baris detail satu task: dipimpin nomor issue (#53) agar jelas issue mana.
// Baris terakhir menyebut sheet/bulan asal data (source_month) agar mudah
// ditelusuri ke sumbernya.
function waDetail(row: ReportRow, opts: { prefix?: string } = {}): string[] {
  const app = row.aplikasi ? `_[${row.aplikasi}]_ ` : "";
  const no = row.no != null ? `#${row.no}` : "#-";
  const pic = row.pic || "-";
  return [
    `${opts.prefix || ""}${no} ${app}${row.issue}`,
    `   👤 ${pic} • ${row.status}`,
    `   📅 Req: ${waDateTime(row.tgl_request)} • Selesai: ${waDateTime(row.tgl_selesai)}`,
    `   📄 Sheet: ${row.source_month || "-"}`,
  ];
}

// Format tanggal+jam ISO -> "10 Jun 2026 14.30"; jam disertakan hanya bila
// datanya memang punya komponen waktu (bukan 00.00). Kosong/null -> "-".
function waDateTime(iso: string | null): string {
  if (!iso) return "-";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "-";
  const day = `${d.getDate()} ${WA_MONTH_ID[d.getMonth()]} ${d.getFullYear()}`;
  if (d.getHours() || d.getMinutes()) {
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    return `${day} ${hh}.${mm}`;
  }
  return day;
}

function mondayOf(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  const day = (d.getDay() + 6) % 7;
  d.setDate(d.getDate() - day);
  return d.toISOString().slice(0, 10);
}
