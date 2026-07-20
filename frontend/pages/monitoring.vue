<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useMonitoring } from "~/composables/useMonitoring";

const m = useMonitoring();

onMounted(async () => {
  await m.init();
});

// Auto-tarik saat sumber / parameter periode berubah.
watch(m.source, () => { if (!m.initializing.value) m.run(); });
watch([m.periodMode, m.date, m.weekStart, m.month, m.dateField], () => {
  if (!m.initializing.value) m.run();
});

const MONTHS = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
];
const monthNum = computed<number>({
  get: () => Number(m.month.value.split("-")[1]),
  set: (v) => { m.month.value = `${m.month.value.split("-")[0]}-${String(v).padStart(2, "0")}`; },
});
const yearNum = computed<number>({
  get: () => Number(m.month.value.split("-")[0]),
  set: (v) => { m.month.value = `${v}-${m.month.value.split("-")[1]}`; },
});
const years = computed(() => {
  const cy = new Date().getFullYear();
  const out: number[] = [];
  for (let y = cy + 1; y >= 2024; y--) out.push(y);
  return out;
});

// Kolom status untuk tabel per-PIC (ikuti urutan kanonik dari by_status).
const statusCols = computed(() =>
  m.data.value ? Object.keys(m.data.value.summary.by_status) : []
);
// Baris per-PIC, urut total terbanyak.
const picRows = computed(() => {
  if (!m.data.value) return [];
  return Object.entries(m.data.value.summary.by_pic_status)
    .map(([pic, b]) => ({ pic, total: b.total, by_status: b.by_status, rows_by_status: b.rows_by_status }))
    .sort((a, b) => b.total - a.total);
});
function badge(status: string) {
  return "badge s-" + status.replace(/\s/g, "");
}

// Detail on-click: tampilkan minimal Bulan & No issue untuk sel yang diklik
// (mempermudah menyisir mana yang Hold/Back Log/To Do/Tanpa Status).
// Panel muncul di tengah layar (lihat CellDetailPopover.vue).
const detail = ref<{ title: string; rows: any[] } | null>(null);
function showDetail(pic: string, status: string, rows: any[]) {
  detail.value = { title: `${pic} — ${status} (${rows.length})`, rows };
}
</script>

<template>
  <div>
    <template v-if="m.initializing.value">
      <SkeletonControls :fields="3" />
      <div class="panel"><SkeletonReport /></div>
    </template>

    <template v-else>
      <div class="page-grid">
        <div class="page-body">
          <div class="panel">
            <div class="panel-title"><span class="dot" />Parameter Monitoring</div>
            <div class="controls">
              <div class="field">
                <label>📂 Sumber Data</label>
                <select v-model="m.source.value">
                  <option v-for="s in m.sources.value" :key="s.id" :value="s.id">{{ s.name }}</option>
                </select>
              </div>

              <div class="field">
                <label>⏱️ Periode</label>
                <select v-model="m.periodMode.value">
                  <option value="daily">Harian</option>
                  <option value="weekly">Mingguan</option>
                  <option value="monthly">Bulanan</option>
                  <option value="all">Semua Waktu</option>
                </select>
              </div>

              <div class="field" v-if="m.periodMode.value === 'daily'">
                <label>📅 Tanggal</label>
                <input type="date" v-model="m.date.value" />
              </div>
              <div class="field" v-else-if="m.periodMode.value === 'weekly'">
                <label>🗓️ Mulai Minggu (Senin)</label>
                <input type="date" v-model="m.weekStart.value" />
              </div>
              <template v-else-if="m.periodMode.value === 'monthly'">
                <div class="field">
                  <label>📆 Bulan</label>
                  <select v-model.number="monthNum">
                    <option v-for="(mo, i) in MONTHS" :key="i" :value="i + 1">{{ mo }}</option>
                  </select>
                </div>
                <div class="field">
                  <label>Tahun</label>
                  <select v-model.number="yearNum">
                    <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
                  </select>
                </div>
              </template>

              <div class="field" v-if="m.periodMode.value !== 'all'">
                <label>🎯 Acuan Tanggal</label>
                <select v-model="m.dateField.value">
                  <option value="tgl_request">Tgl Request</option>
                  <option value="tgl_mulai">Tgl Mulai</option>
                  <option value="tgl_selesai">Tgl Selesai</option>
                  <option value="last_update">Last Update</option>
                </select>
              </div>
            </div>
          </div>

          <div v-if="m.error.value" class="error">{{ m.error.value }}</div>

          <SkeletonReport v-if="m.loading.value" />

          <template v-else-if="m.data.value">
            <!-- Monitoring per Status -->
            <div class="panel">
              <div class="row-between report-head">
                <div class="report-title">
                  <h2>Monitoring per Status</h2>
                  <span class="period-pill">{{ m.data.value.meta.period.label }}</span>
                </div>
              </div>
              <SummaryCards :summary="m.data.value.summary" />
            </div>

            <!-- Monitoring per PIC -->
            <div class="panel">
              <div class="row-between report-head">
                <div class="report-title">
                  <h2>Monitoring per PIC</h2>
                  <span class="period-pill">{{ picRows.length }} PIC</span>
                </div>
              </div>

              <div v-if="!picRows.length" class="empty-state">
                <div class="empty-ico">🗂️</div>
                <p>Tidak ada task untuk periode ini.</p>
              </div>

              <div v-else class="table-scroll">
                <table class="report">
                  <thead>
                    <tr>
                      <th>PIC</th>
                      <th>Total</th>
                      <th v-for="s in statusCols" :key="s">{{ s }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in picRows" :key="row.pic">
                      <td>{{ row.pic }}</td>
                      <td><strong>{{ row.total }}</strong></td>
                      <td v-for="s in statusCols" :key="s">
                        <button
                          v-if="row.by_status[s]"
                          type="button"
                          :class="badge(s)"
                          class="badge-btn"
                          @click="showDetail(row.pic, s, row.rows_by_status[s] || [])"
                        >{{ row.by_status[s] }}</button>
                        <span v-else class="muted">–</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </template>
        </div>

        <aside class="page-rail">
          <InfoRail page="monitoring" />
        </aside>
      </div>

      <CellDetailPopover
        v-if="detail"
        :title="detail.title"
        :rows="detail.rows"
        @close="detail = null"
      />
    </template>
  </div>
</template>
