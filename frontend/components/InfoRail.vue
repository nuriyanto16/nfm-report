<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  page?: "harian" | "mingguan" | "bulanan" | "monitoring" | "project" | "evaluasi" | "sumber" | "users" | "profil" | "daily" | "weekly" | "monthly";
  activeFiltersCount?: number;
  summaryStats?: { total: number; done: number; progress: number; hold: number };
}>();

const route = useRoute();

// Auto-detect page from route path if not explicitly provided
const activePage = computed(() => {
  let p = props.page || "";
  if (!p) {
    const path = route.path;
    if (path === "/harian") p = "harian";
    else if (path === "/mingguan") p = "mingguan";
    else if (path === "/bulanan") p = "bulanan";
    else if (path === "/monitoring") p = "monitoring";
    else if (path === "/project") p = "project";
    else if (path === "/evaluasi") p = "evaluasi";
    else if (path === "/sumber") p = "sumber";
    else if (path === "/users") p = "users";
    else if (path === "/profil") p = "profil";
    else p = "harian";
  }

  // Normalize English period names to Indonesian
  if (p === "daily") return "harian";
  if (p === "weekly") return "mingguan";
  if (p === "monthly") return "bulanan";
  return p;
});

const content = computed(() => {
  const p = activePage.value;
  switch (p) {
    case "harian":
      return {
        title: "Laporan Harian",
        subtitle: "Aktivitas Harian",
        desc: "Merekap progress harian dari data summary pemeliharaan SIMPEL NextGen.",
        tips: [
          "Gunakan acuan 'Tgl Selesai' untuk memantau pekerjaan yang diselesaikan pada hari tersebut.",
          "Gunakan format WhatsApp untuk menyalin teks ringkasan secara cepat ke grup koordinasi.",
          "Ekspor XLSX/PDF untuk kebutuhan pelaporan formal ke manajemen."
        ],
        showLegend: true
      };
    case "mingguan":
      return {
        title: "Laporan Mingguan",
        subtitle: "Aktivitas Mingguan",
        desc: "Menampilkan akumulasi status pekerjaan selama rentang 7 hari kalender berjalan.",
        tips: [
          "Pastikan parameter tanggal mulai berada pada hari Senin agar perhitungan minggu kalender berjalan akurat.",
          "Laporan mingguan secara otomatis memisahkan data per-Aplikasi dan per-PIC di preview tabular.",
          "Format ekspor Word (.docx) sudah memiliki tata letak halaman yang siap cetak."
        ],
        showLegend: true
      };
    case "bulanan":
      return {
        title: "Laporan Bulanan",
        subtitle: "Aktivitas Bulanan",
        desc: "Merekap seluruh pekerjaan berdasarkan tab bulanan pada Google Sheet active.",
        tips: [
          "Laporan bulanan menyaring baris berdasarkan sheet month ('Januari', 'Februari', dst.) secara otomatis.",
          "Pastikan tahun yang dipilih sesuai dengan database spreadsheet active.",
          "Gunakan filter Aplikasi untuk melihat performa modul spesifik (Pengujian, Kalibrasi, Mobile, Infra)."
        ],
        showLegend: true
      };
    case "monitoring":
      return {
        title: "Monitoring Progress",
        subtitle: "Analitik Beban Kerja",
        desc: "Analisis performa tim, jumlah task per PIC, serta distribusi status proyek secara visual.",
        tips: [
          "Tabel per-PIC diurutkan secara otomatis dari total beban tugas terbanyak ke terkecil.",
          "Pantau status 'Hold' secara intensif agar tidak menimbulkan hambatan pada timeline utama.",
          "Gunakan filter semua waktu untuk reviu historis beban kerja tim sejak awal tahun."
        ],
        showLegend: true
      };
    case "project":
      return {
        title: "Project Management",
        subtitle: "Informasi Proyek MST",
        desc: "Overview status pengerjaan proyek strategis MST 2026, realisasi pencapaian, dan penyerapan anggaran.",
        tips: [
          "Realisasi Pencapaian dihitung dari rasio nilai pencapaian aktual terhadap total nilai kontrak proyek.",
          "Evaluasi Triwulan (TW) mengukur performa berkala untuk tiap divisi pelaksana proyek.",
          "Refresh data secara manual jika terdapat pembaruan data pada spreadsheet master proyek."
        ],
        showLegend: false,
        extraWidgets: [
          {
            title: "Indikator Kinerja",
            items: [
              "🟢 Baik: Achievement Rate >= 90%",
              "🟡 Sedang: Achievement Rate 70% - 89%",
              "🔴 Perlu Perhatian: Achievement Rate < 70%"
            ]
          }
        ]
      };
    case "evaluasi":
      return {
        title: "Evaluasi Triwulan",
        subtitle: "Panduan Evaluasi",
        desc: "Dokumen reviu triwulanan tim pelaksana & target kerja triwulan selanjutnya per PIC.",
        tips: [
          "File html harus diletakkan pada folder 'LAPORAN' di backend dengan format penamaan '*_Tim_<PIC>.html'.",
          "Gunakan tombol 'Buka di tab baru' untuk kenyamanan membaca dokumen dalam ukuran penuh.",
          "Dokumen ini digunakan sebagai bahan rapat evaluasi triwulanan BBPPT."
        ],
        showLegend: false
      };
    case "sumber":
      return {
        title: "Sumber Data",
        subtitle: "Konfigurasi Spreadsheet",
        desc: "Daftar spreadsheet aktif yang digunakan sebagai basis data rekapitulasi laporan.",
        tips: [
          "Pastikan URL/Spreadsheet ID terdaftar di config/sources.yaml.",
          "Mapping kolom diatur secara dinamis per-sumber agar fleksibel jika terjadi penambahan kolom baru.",
          "Hubungi IT Administrator jika ingin melakukan migrasi database atau integrasi API baru."
        ],
        showLegend: false
      };
    case "users":
      return {
        title: "Manajemen User",
        subtitle: "Hak Akses & Peran",
        desc: "Pengaturan akun pengguna, peran (role), dan menu aplikasi yang diizinkan untuk diakses.",
        tips: [
          "Hak akses menu diatur per-Role melalui tab 'Manajemen Role'.",
          "Gunakan switch aktif untuk menonaktifkan sementara user tanpa menghapus data historisnya.",
          "Password awal yang dibuat harus langsung diganti oleh pengguna bersangkutan di menu Profil."
        ],
        showLegend: false
      };
    case "profil":
      return {
        title: "Profil & Keamanan",
        subtitle: "Keamanan Akun",
        desc: "Detail informasi akun Anda dan menu perubahan kata sandi untuk menjaga keamanan sistem.",
        tips: [
          "Gunakan kombinasi minimal 8 karakter dengan angka dan simbol untuk kekuatan password baru.",
          "Administrator tidak dapat melihat password Anda (telah dienkripsi satu arah dengan Hash bcrypt).",
          "Pastikan keluar (logout) jika selesai menggunakan perangkat publik."
        ],
        showLegend: false
      };
  }
});
</script>

<template>
  <aside class="info-rail-card">
    <div class="rail-header">
      <div class="rail-logo">✨</div>
      <div class="rail-title-group">
        <h3>{{ content.title }}</h3>
        <span>{{ content.subtitle }}</span>
      </div>
    </div>

    <div class="rail-divider" />

    <!-- Dynamic Live Summary Widget -->
    <div v-if="summaryStats" class="rail-section live-stats-box">
      <h4 class="rail-sub-title">⚡ Metric Ringkas</h4>
      <div class="mini-kpi-grid">
        <div class="mini-kpi">
          <span>Total</span>
          <strong>{{ summaryStats.total }}</strong>
        </div>
        <div class="mini-kpi green">
          <span>Done</span>
          <strong>{{ summaryStats.done }}</strong>
        </div>
        <div class="mini-kpi cyan">
          <span>Progress</span>
          <strong>{{ summaryStats.progress }}</strong>
        </div>
        <div class="mini-kpi red">
          <span>Hold</span>
          <strong>{{ summaryStats.hold }}</strong>
        </div>
      </div>
    </div>

    <!-- Dynamic Active Filter Indicator Widget -->
    <div v-if="activeFiltersCount" class="rail-section active-filter-box">
      <div class="active-filter-badge">
        <span>🔍 Filter Aktif</span>
        <span class="count-tag">{{ activeFiltersCount }} Dimensi</span>
      </div>
    </div>

    <div class="rail-section">
      <p class="rail-desc">{{ content.desc }}</p>
    </div>

    <div class="rail-section">
      <h4 class="rail-sub-title">💡 Petunjuk &amp; Tips</h4>
      <ul class="rail-tips-list">
        <li v-for="(tip, index) in content.tips" :key="index">
          {{ tip }}
        </li>
      </ul>
    </div>

    <div v-if="content.showLegend" class="rail-section">
      <h4 class="rail-sub-title">🏷️ Legenda Status</h4>
      <div class="rail-legend-grid">
        <div class="rail-legend-item">
          <span class="legend-dot s-Done" />
          <span>Done</span>
        </div>
        <div class="rail-legend-item">
          <span class="legend-dot s-Progress" />
          <span>Progress</span>
        </div>
        <div class="rail-legend-item">
          <span class="legend-dot s-ToDo" />
          <span>To Do</span>
        </div>
        <div class="rail-legend-item">
          <span class="legend-dot s-Hold" />
          <span>Hold</span>
        </div>
        <div class="rail-legend-item">
          <span class="legend-dot s-BackLog" />
          <span>Back Log</span>
        </div>
      </div>
    </div>

    <div v-if="content.extraWidgets" class="rail-section">
      <div v-for="(widget, idx) in content.extraWidgets" :key="idx" class="rail-extra-widget">
        <h4 class="rail-sub-title">📊 {{ widget.title }}</h4>
        <ul class="rail-extra-list">
          <li v-for="(item, itemIdx) in widget.items" :key="itemIdx">
            {{ item }}
          </li>
        </ul>
      </div>
    </div>

    <!-- System Status Box -->
    <div class="rail-section sys-box">
      <h4 class="rail-sub-title">🛡️ Status Sistem</h4>
      <div class="sys-status-list">
        <div class="sys-item">
          <span class="sys-dot live" />
          <span>Live Data Sync</span>
        </div>
        <div class="sys-item">
          <span class="sys-dot ok" />
          <span>Fast Export Ready</span>
        </div>
      </div>
    </div>

    <div class="rail-footer">
      <span>FAST REPORT v1.1.0</span>
      <span>MULTI-PROJECT REPORT</span>
    </div>
  </aside>
</template>

<style scoped>
.info-rail-card {
  background: var(--panel, #161b22);
  border: 1px solid var(--border, rgba(48, 66, 100, 0.55));
  border-radius: var(--radius, 14px);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 18px;
  position: sticky;
  top: 88px;
  max-height: calc(100vh - 110px);
  overflow-y: auto;
}

.rail-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rail-logo {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm, 9px);
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.3);
  color: var(--cyan, #38bdf8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.rail-title-group {
  display: flex;
  flex-direction: column;
}

.rail-title-group h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--text, #f1f5f9);
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.rail-title-group span {
  font-size: 11px;
  color: var(--cyan, #38bdf8);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.rail-divider {
  height: 1px;
  background: linear-gradient(90deg, rgba(56, 189, 248, 0.3) 0%, rgba(56, 189, 248, 0.05) 100%);
}

.live-stats-box {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 10px;
  padding: 12px;
}
.mini-kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-top: 6px;
}
.mini-kpi {
  background: #0f172a;
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 6px;
  padding: 6px 10px;
  display: flex;
  flex-direction: column;
}
.mini-kpi span { font-size: 10px; color: var(--text-dim, #94a3b8); font-weight: 600; text-transform: uppercase; }
.mini-kpi strong { font-size: 16px; color: #ffffff; font-weight: 800; font-family: 'Plus Jakarta Sans', sans-serif; }
.mini-kpi.green strong { color: #22c55e; }
.mini-kpi.cyan strong { color: #38bdf8; }
.mini-kpi.red strong { color: #f87171; }

.active-filter-box {
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 8px;
  padding: 8px 12px;
}
.active-filter-badge {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11.5px;
  font-weight: 700;
  color: var(--cyan, #38bdf8);
}
.count-tag {
  background: var(--cyan, #38bdf8);
  color: #0a0e17;
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 999px;
}

.rail-desc {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--text-sub, #cbd5e1);
}

.rail-sub-title {
  margin: 0 0 8px 0;
  font-size: 11.5px;
  font-weight: 700;
  color: var(--cyan, #38bdf8);
  font-family: 'Plus Jakarta Sans', sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.rail-tips-list {
  margin: 0;
  padding: 0 0 0 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rail-tips-list li {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-sub, #cbd5e1);
}

.rail-tips-list li::marker {
  color: var(--cyan, #38bdf8);
}

.rail-legend-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.rail-legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text, #f1f5f9);
  font-weight: 600;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-dot.s-Done { background-color: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.4); }
.legend-dot.s-Progress { background-color: #38bdf8; box-shadow: 0 0 6px rgba(56,189,248,0.4); }
.legend-dot.s-ToDo { background-color: #f59e0b; box-shadow: 0 0 6px rgba(245,158,11,0.4); }
.legend-dot.s-Hold { background-color: #f87171; box-shadow: 0 0 6px rgba(248,113,113,0.4); }
.legend-dot.s-BackLog { background-color: #64748b; }

.rail-extra-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rail-extra-list li {
  font-size: 11.5px;
  color: var(--text-sub, #cbd5e1);
  padding: 6px 10px;
  background: rgba(30, 41, 59, 0.6);
  border-radius: var(--radius-sm, 9px);
  border-left: 3px solid var(--cyan, #38bdf8);
}

.sys-box {
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 10px;
}
.sys-status-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.sys-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11.5px;
  color: var(--text-sub, #cbd5e1);
  font-weight: 500;
}
.sys-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.sys-dot.live { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
.sys-dot.ok { background: #38bdf8; box-shadow: 0 0 6px #38bdf8; }

.rail-footer {
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px solid var(--border-soft, rgba(48, 66, 100, 0.28));
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-dim, #94a3b8);
  font-weight: 600;
  letter-spacing: 0.05em;
}
</style>
