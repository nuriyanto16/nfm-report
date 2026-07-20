// State & aksi untuk halaman Monitoring Progress.
// Memakai endpoint /api/report yang sama, dengan tambahan periode "all" (semua waktu)
// dan menampilkan ringkasan per-status & per-PIC (bukan tabel detail).
import { ref } from "vue";
import type { ReportResponse } from "~/composables/useReport";

export type MonitorPeriod = "daily" | "weekly" | "monthly" | "all";

export function useMonitoring() {
  const sources = ref<{ id: string; name: string }[]>([]);
  const source = ref<string>("");
  const periodMode = ref<MonitorPeriod>("all");
  const dateField = ref<string>("tgl_request");

  const today = new Date().toISOString().slice(0, 10);
  const date = ref<string>(today);
  const weekStart = ref<string>(mondayOf(today));
  const month = ref<string>(today.slice(0, 7));

  const data = ref<ReportResponse | null>(null);
  const loading = ref(false);
  const initializing = ref(true);
  const error = ref<string>("");

  async function loadSources() {
    const res = await apiGet<{ sources: { id: string; name: string }[] }>("/api/sources");
    sources.value = res.sources;
    if (!source.value && res.sources.length) source.value = res.sources[0].id;
  }

  function periodParams() {
    const p: Record<string, any> = {
      source: source.value,
      period: periodMode.value,
      date_field: dateField.value,
    };
    if (periodMode.value === "daily") p.date = date.value;
    else if (periodMode.value === "weekly") p.week_start = weekStart.value;
    else if (periodMode.value === "monthly") p.month = month.value;
    return p;
  }

  async function run() {
    if (!source.value) return;
    loading.value = true;
    error.value = "";
    try {
      data.value = await apiGet<ReportResponse>("/api/report", periodParams());
    } catch (e: any) {
      error.value = e?.data?.detail || e?.message || "Gagal memuat monitoring";
      data.value = null;
    } finally {
      loading.value = false;
    }
  }

  async function init() {
    initializing.value = true;
    try {
      await loadSources();
      await run();
    } finally {
      initializing.value = false;
    }
  }

  return {
    sources, source, periodMode, dateField, date, weekStart, month,
    data, loading, initializing, error,
    loadSources, run, init,
  };
}

function mondayOf(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  const day = (d.getDay() + 6) % 7;
  d.setDate(d.getDate() - day);
  return d.toISOString().slice(0, 10);
}
