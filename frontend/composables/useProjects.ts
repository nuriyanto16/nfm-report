// State & aksi untuk halaman Project Management (khusus superadmin).
// Mengambil daftar proyek + ringkasan/evaluasi triwulan dari /api/projects*.
import { computed, ref } from "vue";

export interface Project {
  no: number;
  section: string;
  instansi: string;
  nama_pekerjaan: string;
  bendera: string;
  pic_names: string[];
  status: string;
  progress: number; // 0..1
  triwulan: string;
  mulai_kontrak: string | null;
  akhir_kontrak: string | null;
  nilai_project: number;
  estimasi_pencairan: number;
  nilai_pencapaian: number;
  nilai_pencairan: number;
  keterangan: string;
}

export interface TriwulanRow {
  triwulan: string;
  count: number;
  done: number;
  progress: number;
  nilai_project: number;
  nilai_pencapaian: number;
  nilai_pencairan: number;
  avg_progress: number;
  achievement_rate: number;
  overdue: number;
  evaluasi: string;
}

export interface RiskRow {
  no: number;
  instansi: string;
  nama_pekerjaan: string;
  pic: string;
  bendera: string;
  akhir_kontrak: string | null;
  progress: number;
  status: string;
  days: number;
  triwulan: string;
}

export interface ProjectSummary {
  source: string;
  generated_at: string;
  totals: {
    projects: number;
    nilai_project: number;
    estimasi_pencairan: number;
    nilai_pencapaian: number;
    nilai_pencairan: number;
    avg_progress: number;
    achievement_rate: number;
    pencairan_rate: number;
    done: number;
    overdue: number;
  };
  by_status: Record<string, number>;
  by_section: Record<string, number>;
  by_bendera: Record<string, number>;
  by_pic: { pic: string; total: number; done: number; nilai_pencapaian: number; done_rate: number }[];
  triwulan: TriwulanRow[];
  alerts: { overdue: RiskRow[]; due_soon: RiskRow[] };
}

export interface Filters {
  sections: string[];
  statuses: string[];
  pics: string[];
  benderas: string[];
  triwulan: string[];
}

export interface LoadMapping {
  members: string[];
  projects: { no: number; instansi: string; nama: string; pic_utama: string; tahun: string; progress: number; total_mapping: number; alloc: Record<string, number> }[];
  member_totals: { member: string; total_load: number; projects: number }[];
  counts: { total: number; done: number };
}
export interface TargetData {
  months: { month: string; sheet: string; total: number; by_status: Record<string, number>; items: { group: string; instansi: string; kegiatan: string; target: string; status: string; keterangan: string }[] }[];
  by_status: Record<string, number>;
}
export interface TwData {
  divisions: { division: string; sheet: string; total: number; done: number; by_status: Record<string, number>; items: { group: string; no: number; instansi: string; kegiatan: string; pic: string; tahun: string; target_tw: string; progress: number | null; status: string; keterangan: string }[] }[];
}

export function useProjects() {
  const summary = ref<ProjectSummary | null>(null);
  const projects = ref<Project[]>([]);
  const filters = ref<Filters>({ sections: [], statuses: [], pics: [], benderas: [], triwulan: [] });
  const loadMapping = ref<LoadMapping | null>(null);
  const targets = ref<TargetData | null>(null);
  const tw = ref<TwData | null>(null);

  const f = ref({ section: "", status: "", pic: "", bendera: "", triwulan: "", q: "" });

  const loading = ref(false);
  const initializing = ref(true);
  const refreshing = ref(false);
  const error = ref("");

  function params() {
    return {
      section: f.value.section,
      status: f.value.status,
      pic: f.value.pic,
      bendera: f.value.bendera,
      triwulan: f.value.triwulan,
      q: f.value.q,
    };
  }

  async function loadList() {
    loading.value = true;
    error.value = "";
    try {
      const res = await apiGet<{ projects: Project[]; count: number }>("/api/projects", params());
      projects.value = res.projects;
    } catch (e: any) {
      error.value = e?.data?.detail || e?.message || "Gagal memuat proyek";
      projects.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function init() {
    initializing.value = true;
    error.value = "";
    try {
      const [flt, summ, lm, tg, twd] = await Promise.all([
        apiGet<Filters>("/api/projects/filters"),
        apiGet<ProjectSummary>("/api/projects/summary"),
        apiGet<LoadMapping>("/api/projects/load-mapping"),
        apiGet<TargetData>("/api/projects/targets"),
        apiGet<TwData>("/api/projects/tw"),
      ]);
      filters.value = flt;
      summary.value = summ;
      loadMapping.value = lm;
      targets.value = tg;
      tw.value = twd;
      await loadList();
    } catch (e: any) {
      error.value = e?.data?.detail || e?.message || "Gagal memuat data project management";
    } finally {
      initializing.value = false;
    }
  }

  // Muat ulang dari Excel (tombol Refresh Data), lalu tarik ulang semua dataset.
  async function refreshData() {
    refreshing.value = true;
    error.value = "";
    try {
      await apiSend("/api/projects/refresh", "POST");
      await init();
    } catch (e: any) {
      error.value = e?.message || "Gagal refresh data";
    } finally {
      refreshing.value = false;
    }
  }

  function resetFilters() {
    f.value = { section: "", status: "", pic: "", bendera: "", triwulan: "", q: "" };
    loadList();
  }

  async function exportXlsx() {
    const base = useApiBase();
    const token = useCookie<string | null>("report_token").value;
    const url = `${base}/api/projects/export${buildQuery(params())}`;
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      error.value = `Export gagal (${res.status})`;
      return;
    }
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "project-management-summary.xlsx";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(a.href);
  }

  const hasFilter = computed(() =>
    Object.entries(f.value).some(([, v]) => v !== "")
  );

  return {
    summary, projects, filters, loadMapping, targets, tw,
    f, loading, initializing, refreshing, error,
    hasFilter, init, loadList, resetFilters, exportXlsx, refreshData,
  };
}
