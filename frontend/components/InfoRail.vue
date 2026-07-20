<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  page?: "harian" | "mingguan" | "bulanan" | "monitoring" | "project" | "evaluasi" | "sumber" | "users" | "profil" | "daily" | "weekly" | "monthly";
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

  // Normalize English period names to Indonesian to match the switch cases
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
          "Pantau status 'Hold' secara intensif agar tidak menimbulkan hambatan (bottleneck) pada timeline utama.",
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

    <div class="rail-footer">
      <span>FAST REPORT v1.1.0</span>
      <span>MULTI-PROJECT REPORT</span>
    </div>
  </aside>
</template>

<style scoped>
.info-rail-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: sticky;
  top: 92px; /* aligns below the topbar */
  max-height: calc(100vh - 120px);
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
  border-radius: var(--radius-sm);
  background: var(--accent-light);
  border: 1px solid var(--accent);
  color: var(--accent);
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
  color: var(--primary);
  font-family: 'Sora', sans-serif;
}

.rail-title-group span {
  font-size: 11px;
  color: var(--accent);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.rail-divider {
  height: 1px;
  background: linear-gradient(90deg, rgba(197, 160, 89, 0.3) 0%, rgba(197, 160, 89, 0.05) 100%);
}

.rail-desc {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--text);
  opacity: 0.85;
}

.rail-sub-title {
  margin: 0 0 10px 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--primary);
  font-family: 'Sora', sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.rail-tips-list {
  margin: 0;
  padding: 0 0 0 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rail-tips-list li {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text);
  opacity: 0.8;
}

.rail-tips-list li::marker {
  color: var(--accent);
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
  font-size: 11.5px;
  color: var(--text);
  font-weight: 500;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-dot.s-Done { background-color: #137333; }
.legend-dot.s-Progress { background-color: #b06000; }
.legend-dot.s-ToDo { background-color: #1a73e8; }
.legend-dot.s-Hold { background-color: #c5221f; }
.legend-dot.s-BackLog { background-color: #5f6368; }

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
  color: var(--text);
  padding: 6px 10px;
  background: var(--border-soft);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
}

.rail-footer {
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px solid var(--border-soft);
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--muted);
  font-weight: 500;
}
</style>
