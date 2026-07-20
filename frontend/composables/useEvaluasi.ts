// State untuk modul Evaluasi Triwulan: daftar dokumen per PIC + isi HTML yang
// di-embed. Untuk sementara hanya ada satu dokumen (Tim Nuriyanto); pemilih PIC
// sudah disiapkan agar mudah bertambah.
import { ref } from "vue";

export interface EvaluasiItem {
  pic: string;
  file: string;
  title: string;
}

export function useEvaluasi() {
  const items = ref<EvaluasiItem[]>([]);
  const selected = ref<string>(""); // PIC terpilih
  const html = ref<string>("");
  const title = ref<string>("");
  const loading = ref(false);
  const initializing = ref(true);
  const error = ref("");

  async function loadList() {
    const res = await apiGet<{ items: EvaluasiItem[] }>("/api/projects/evaluasi");
    items.value = res.items;
    if (!selected.value && res.items.length) selected.value = res.items[0].pic;
  }

  async function loadContent() {
    if (!selected.value) return;
    loading.value = true;
    error.value = "";
    try {
      const base = useApiBase();
      const token = useCookie<string | null>("report_token").value;
      const url = `${base}/api/projects/evaluasi/content${buildQuery({ pic: selected.value })}`;
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`Gagal memuat dokumen (${res.status})`);
      html.value = await res.text();
      title.value = items.value.find((i) => i.pic === selected.value)?.title || "";
    } catch (e: any) {
      error.value = e?.message || "Gagal memuat dokumen evaluasi";
      html.value = "";
    } finally {
      loading.value = false;
    }
  }

  async function init() {
    initializing.value = true;
    error.value = "";
    try {
      await loadList();
      await loadContent();
    } catch (e: any) {
      error.value = e?.data?.detail || e?.message || "Gagal memuat modul evaluasi";
    } finally {
      initializing.value = false;
    }
  }

  return { items, selected, html, title, loading, initializing, error, init, loadContent };
}
