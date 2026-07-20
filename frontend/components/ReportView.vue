<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { useReport } from "~/composables/useReport";

const props = defineProps<{ period: "daily" | "weekly" | "monthly" }>();

const r = useReport(props.period);

onMounted(async () => {
  await r.init();
});

watch(r.source, async () => {
  await r.loadFilters();
  r.resetFilters();
  await r.run();
});

// Auto-tarik saat parameter periode / acuan / filter berubah.
watch(() => JSON.stringify(r.selected), () => r.run());
watch([r.date, r.weekStart, r.month, r.dateField], () => {
  if (!r.initializing.value) r.run();
});

const titles = {
  daily: "Laporan Harian",
  weekly: "Laporan Mingguan",
  monthly: "Laporan Bulanan",
};

const MONTHS = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
];

const monthNum = computed<number>({
  get: () => Number(r.month.value.split("-")[1]),
  set: (m) => {
    const y = r.month.value.split("-")[0];
    r.month.value = `${y}-${String(m).padStart(2, "0")}`;
  },
});
const yearNum = computed<number>({
  get: () => Number(r.month.value.split("-")[0]),
  set: (y) => {
    const m = r.month.value.split("-")[1];
    r.month.value = `${y}-${m}`;
  },
});
const years = computed(() => {
  const cy = new Date().getFullYear();
  const out: number[] = [];
  for (let y = cy + 1; y >= 2024; y--) out.push(y);
  return out;
});

// Quick Presets
function setToday() {
  r.date.value = new Date().toISOString().slice(0, 10);
}
function setThisMonday() {
  const d = new Date();
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  const mon = new Date(d.setDate(diff));
  r.weekStart.value = mon.toISOString().slice(0, 10);
}
function setThisMonth() {
  const now = new Date();
  monthNum.value = now.getMonth() + 1;
  yearNum.value = now.getFullYear();
}

// Stats & filter counts for InfoRail
const activeFiltersCount = computed(() => {
  return r.FILTER_DIMS.reduce((n, d) => n + (r.selected[d]?.length || 0), 0);
});

const summaryStats = computed(() => {
  if (!r.data.value?.summary) return undefined;
  const s = r.data.value.summary;
  const bs = s.by_status || {};
  return {
    total: s.total || 0,
    done: bs["Done"] || 0,
    progress: bs["Progress"] || 0,
    hold: bs["Hold"] || 0,
  };
});
</script>

<template>
  <div>
    <!-- Saat inisialisasi: tampilkan skeleton untuk SEMUA panel. -->
    <template v-if="r.initializing.value">
      <SkeletonControls :fields="3" />
      <SkeletonFilter :groups="6" />
      <div class="panel"><SkeletonReport /></div>
    </template>

    <template v-else>
      <div class="page-grid">
        <div class="page-body">
          <div class="panel param-panel">
            <div class="row-between param-head">
              <div class="panel-title"><span class="dot" />Parameter Utama Laporan</div>
              <div class="preset-btns">
                <button v-if="period === 'daily'" class="preset-btn" @click="setToday">📅 Hari Ini</button>
                <button v-else-if="period === 'weekly'" class="preset-btn" @click="setThisMonday">🗓️ Senin Ini</button>
                <button v-else class="preset-btn" @click="setThisMonth">📆 Bulan Ini</button>
              </div>
            </div>

            <div class="controls">
              <div class="field">
                <label>📂 Sumber Data</label>
                <select v-model="r.source.value">
                  <option v-for="s in r.sources.value" :key="s.id" :value="s.id">{{ s.name }}</option>
                </select>
              </div>

              <div class="field" v-if="period === 'daily'">
                <label>📅 Tanggal</label>
                <input type="date" v-model="r.date.value" />
              </div>
              <div class="field" v-else-if="period === 'weekly'">
                <label>🗓️ Mulai Minggu (Senin)</label>
                <input type="date" v-model="r.weekStart.value" />
              </div>
              <template v-else>
                <div class="field">
                  <label>📆 Bulan</label>
                  <select v-model.number="monthNum">
                    <option v-for="(m, i) in MONTHS" :key="i" :value="i + 1">{{ m }}</option>
                  </select>
                </div>
                <div class="field">
                  <label>Tahun</label>
                  <select v-model.number="yearNum">
                    <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
                  </select>
                </div>
              </template>

              <div class="field">
                <label>🎯 Acuan Tanggal</label>
                <select v-model="r.dateField.value">
                  <option value="tgl_request">Tgl Request</option>
                  <option value="tgl_mulai">Tgl Mulai</option>
                  <option value="tgl_selesai">Tgl Selesai</option>
                  <option value="last_update">Last Update</option>
                </select>
              </div>

              <button class="btn btn-run" @click="r.run(true)">
                <span v-if="r.loading.value">⏳ Memuat…</span>
                <span v-else>🔍 Tarik Laporan</span>
              </button>
            </div>
          </div>

          <FilterBar
            :dims="r.FILTER_DIMS"
            :values="r.filterValues.value"
            :selected="r.selected"
            @toggle="r.toggle"
            @reset="() => { r.resetFilters(); r.run(); }"
          />

          <div class="panel">
            <div class="row-between report-head">
              <div class="report-title">
                <h2>{{ titles[period] }}</h2>
                <span class="period-pill" v-if="r.data.value">{{ r.data.value.meta.period.label }}</span>
              </div>
              <div class="export-group">
                <span class="export-label">Ekspor:</span>
                <button class="exp exp-xls" :disabled="!r.hasData.value || r.downloading.value === 'xlsx'" @click="r.download('xlsx')">
                  {{ r.downloading.value === 'xlsx' ? '…' : 'Excel' }}
                </button>
                <button class="exp exp-doc" :disabled="!r.hasData.value || r.downloading.value === 'docx'" @click="r.download('docx')">
                  {{ r.downloading.value === 'docx' ? '…' : 'Word' }}
                </button>
                <button class="exp exp-pdf" :disabled="!r.hasData.value || r.downloading.value === 'pdf'" @click="r.download('pdf')">
                  {{ r.downloading.value === 'pdf' ? '…' : 'PDF' }}
                </button>
                <button class="exp exp-wa" :disabled="!r.hasData.value" @click="r.copyWhatsApp()" title="Salin teks laporan format WhatsApp ke clipboard">
                  {{ r.copied.value ? '✓ Tersalin' : '💬 WhatsApp' }}
                </button>
              </div>
            </div>

            <div v-if="r.error.value" class="error">{{ r.error.value }}</div>
            <SkeletonReport v-if="r.loading.value" />

            <template v-else-if="r.data.value">
              <SummaryCards :summary="r.data.value.summary" style="margin-bottom: 16px" />
              <ReportTable v-if="r.hasData.value" :rows="r.data.value.rows" />
              <div v-else class="empty-state">
                <div class="empty-ico">🗂️</div>
                <p>Tidak ada task untuk periode &amp; filter ini.</p>
                <span>Coba ubah bulan, acuan tanggal, atau reset filter.</span>
              </div>
            </template>
          </div>
        </div>

        <aside class="page-rail">
          <InfoRail
            :page="period"
            :activeFiltersCount="activeFiltersCount"
            :summaryStats="summaryStats"
          />
        </aside>
      </div>
    </template>
  </div>
</template>

<style scoped>
.param-panel {
  border-left: 3px solid var(--cyan, #38bdf8);
}
.param-head {
  margin-bottom: 14px;
}
.preset-btns {
  display: flex;
  gap: 8px;
}
.preset-btn {
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.3);
  color: var(--cyan, #38bdf8);
  font-size: 11.5px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  cursor: pointer;
  transition: all .18s;
}
.preset-btn:hover {
  background: var(--cyan, #38bdf8);
  color: #0a0e17;
}
</style>
