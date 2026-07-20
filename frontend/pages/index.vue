<script setup lang="ts">
import { ref, computed, onMounted } from "vue";

// Access report API base & auth
const sources = ref<{ id: string; name: string }[]>([]);
const selectedSource = ref<string>("");
const loading = ref(true);
const error = ref("");

// Raw data storage
const summary = ref<any>(null);
const rows = ref<any[]>([]);

const STATUS_COLORS: Record<string, string> = {
  Done: "#22c55e",
  Progress: "#38bdf8",
  "To Do": "#f59e0b",
  Hold: "#f87171",
  "Back Log": "#64748b",
  "Tanpa Status": "#94a3b8",
};

async function loadDashboardData() {
  loading.value = true;
  error.value = "";
  try {
    const sRes = await apiGet<{ sources: { id: string; name: string }[] }>("/api/sources");
    sources.value = sRes.sources || [];
    if (!selectedSource.value && sources.value.length) {
      selectedSource.value = sources.value[0].id;
    }

    if (selectedSource.value) {
      const reportRes = await apiGet<any>(`/api/report?source=${encodeURIComponent(selectedSource.value)}&period_mode=all`);
      summary.value = reportRes.summary || null;
      rows.value = reportRes.rows || [];
    }
  } catch (e: any) {
    error.value = e?.message || "Gagal memuat data dashboard";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadDashboardData();
});

// Computed Metrics
const totalTasks = computed(() => summary.value?.total || 0);

const statusCounts = computed(() => {
  const byStatus = summary.value?.by_status || {};
  return {
    done: byStatus["Done"] || 0,
    progress: byStatus["Progress"] || 0,
    todo: byStatus["To Do"] || 0,
    hold: byStatus["Hold"] || 0,
    backlog: byStatus["Back Log"] || 0,
  };
});

const completionRate = computed(() => {
  if (!totalTasks.value) return 0;
  return Math.round((statusCounts.value.done / totalTasks.value) * 100);
});

// High priority items
const highPriorityCount = computed(() => {
  return rows.value.filter((r) => r.priority && r.priority.toLowerCase().includes("high")).length;
});

// Donut Chart calculation
const donutSlices = computed(() => {
  const byStatus = summary.value?.by_status || {};
  const total = totalTasks.value || 1;
  let accumulatedAngle = 0;

  return Object.entries(byStatus).map(([status, count]) => {
    const value = Number(count);
    const percentage = Math.round((value / total) * 100);
    const angle = (value / total) * 360;
    const startAngle = accumulatedAngle;
    accumulatedAngle += angle;

    return {
      status,
      count: value,
      percentage,
      color: STATUS_COLORS[status] || "#94a3b8",
      startAngle,
      endAngle: accumulatedAngle,
    };
  });
});

// SVG Path helper for Donut
function getDonutPath(startAngle: number, endAngle: number, radius = 80, innerRadius = 52) {
  if (endAngle - startAngle >= 359.9) {
    endAngle = startAngle + 359.9;
  }
  const rad1 = ((startAngle - 90) * Math.PI) / 180;
  const rad2 = ((endAngle - 90) * Math.PI) / 180;

  const cx = 100, cy = 100;
  const x1 = cx + radius * Math.cos(rad1);
  const y1 = cy + radius * Math.sin(rad1);
  const x2 = cx + radius * Math.cos(rad2);
  const y2 = cy + radius * Math.sin(rad2);

  const ix1 = cx + innerRadius * Math.cos(rad2);
  const iy1 = cy + innerRadius * Math.sin(rad2);
  const ix2 = cx + innerRadius * Math.cos(rad1);
  const iy2 = cy + innerRadius * Math.sin(rad1);

  const largeArc = endAngle - startAngle > 180 ? 1 : 0;

  return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} L ${ix1} ${iy1} A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${ix2} ${iy2} Z`;
}

// PIC Workload Breakdown
const picChartData = computed(() => {
  const byPic = summary.value?.by_pic_status || {};
  return Object.entries(byPic)
    .map(([pic, data]: [string, any]) => ({
      pic,
      total: data.total || 0,
      done: data.by_status?.Done || 0,
      progress: data.by_status?.Progress || 0,
      hold: data.by_status?.Hold || 0,
      other: (data.total || 0) - (data.by_status?.Done || 0) - (data.by_status?.Progress || 0) - (data.by_status?.Hold || 0),
    }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 8); // Top 8 PICs
});

const maxPicTotal = computed(() => {
  return Math.max(...picChartData.value.map((p) => p.total), 1);
});

// App Breakdown Data
const appChartData = computed(() => {
  const byApp = summary.value?.by_aplikasi || {};
  const total = totalTasks.value || 1;
  return Object.entries(byApp)
    .map(([app, count]) => ({
      name: app,
      count: Number(count),
      pct: Math.round((Number(count) / total) * 100),
    }))
    .sort((a, b) => b.count - a.count);
});

// Critical / Focus Items requiring Executive Review
const criticalItems = computed(() => {
  return rows.value
    .filter((r) => r.status === "Progress" || r.status === "Hold")
    .slice(0, 6);
});

// Active hover item for chart tooltips
const hoveredStatus = ref<string | null>(null);
</script>

<template>
  <div class="dash-wrap">
    <!-- Header Executive Banner -->
    <div class="dash-head">
      <div class="dash-head-text">
        <div class="dash-badge">EXECUTIVE DASHBOARD</div>
        <h1>Monitoring Executive &amp; Performa Sistem</h1>
        <p>Ringkasan analitik real-time progress pekerjaan, distribusi status, dan performa tim.</p>
      </div>

      <div class="dash-actions">
        <div class="field">
          <label>Sumber Data</label>
          <select v-model="selectedSource" @change="loadDashboardData">
            <option v-for="s in sources" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </div>
        <button class="btn-refresh" :disabled="loading" @click="loadDashboardData" title="Refresh Data">
          <span :class="{ spinning: loading }">🔄</span> Refresh
        </button>
      </div>
    </div>

    <!-- Error Banner -->
    <div v-if="error" class="error">{{ error }}</div>

    <!-- Skeleton Loader -->
    <div v-if="loading" class="skel-wrap">
      <div class="skel-cards">
        <div v-for="i in 4" :key="i" class="skel skel-card" />
      </div>
      <div class="skel-grid">
        <div class="skel skel-chart" />
        <div class="skel skel-chart" />
      </div>
    </div>

    <template v-else>
      <!-- KPI Top Metrics Bar -->
      <div class="dash-kpi-grid">
        <div class="kpi-card kpi-total">
          <div class="kpi-icon">📊</div>
          <div class="kpi-content">
            <span class="kpi-label">TOTAL TUGAS / ISU</span>
            <div class="kpi-value">{{ totalTasks }}</div>
            <span class="kpi-sub">Akumulasi seluruh sumber</span>
          </div>
        </div>

        <div class="kpi-card kpi-rate">
          <div class="kpi-icon">🎯</div>
          <div class="kpi-content">
            <span class="kpi-label">TITINGKAT PENYELESAIAN</span>
            <div class="kpi-value">{{ completionRate }}%</div>
            <div class="kpi-progress-bar">
              <span :style="{ width: completionRate + '%' }" />
            </div>
          </div>
        </div>

        <div class="kpi-card kpi-progress">
          <div class="kpi-icon">🔄</div>
          <div class="kpi-content">
            <span class="kpi-label">DALAM PROSES (PROGRESS)</span>
            <div class="kpi-value">{{ statusCounts.progress }}</div>
            <span class="kpi-sub">Pekerjaan aktif berjalan</span>
          </div>
        </div>

        <div class="kpi-card kpi-hold">
          <div class="kpi-icon">⚠️</div>
          <div class="kpi-content">
            <span class="kpi-label">TERTAHAN (HOLD)</span>
            <div class="kpi-value">{{ statusCounts.hold }}</div>
            <span class="kpi-sub">Memerlukan perhatian</span>
          </div>
        </div>

        <div class="kpi-card kpi-priority">
          <div class="kpi-icon">🔥</div>
          <div class="kpi-content">
            <span class="kpi-label">PRIORITAS TINGGI</span>
            <div class="kpi-value">{{ highPriorityCount }}</div>
            <span class="kpi-sub">Tugas kategori High</span>
          </div>
        </div>
      </div>

      <!-- Main Visual Charts Grid -->
      <div class="dash-charts-grid">
        <!-- Donut Chart: Status Distribution -->
        <div class="panel chart-panel">
          <div class="panel-head">
            <h3>📊 Distribusi Status Pekerjaan</h3>
            <span class="panel-sub">Persentase status dari total {{ totalTasks }} isu</span>
          </div>

          <div class="donut-body">
            <div class="svg-container">
              <svg viewBox="0 0 200 200" class="donut-svg">
                <g v-for="slice in donutSlices" :key="slice.status">
                  <path
                    :d="getDonutPath(slice.startAngle, slice.endAngle)"
                    :fill="slice.color"
                    class="donut-segment"
                    :class="{ active: hoveredStatus === slice.status }"
                    @mouseenter="hoveredStatus = slice.status"
                    @mouseleave="hoveredStatus = null"
                  />
                </g>
              </svg>

              <div class="donut-center">
                <span class="center-num">{{ totalTasks }}</span>
                <span class="center-label">Total Task</span>
              </div>
            </div>

            <!-- Legend List -->
            <div class="donut-legend">
              <div
                v-for="slice in donutSlices"
                :key="slice.status"
                class="legend-row"
                :class="{ active: hoveredStatus === slice.status }"
                @mouseenter="hoveredStatus = slice.status"
                @mouseleave="hoveredStatus = null"
              >
                <span class="leg-dot" :style="{ backgroundColor: slice.color }" />
                <span class="leg-name">{{ slice.status }}</span>
                <span class="leg-val">{{ slice.count }}</span>
                <span class="leg-pct">{{ slice.percentage }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Bar Chart: PIC Workload & Productivity -->
        <div class="panel chart-panel">
          <div class="panel-head">
            <h3>👥 Beban Kerja &amp; Performa per PIC</h3>
            <span class="panel-sub">Distribusi tugas pada 8 PIC terbanyak</span>
          </div>

          <div class="pic-chart-body">
            <div v-for="p in picChartData" :key="p.pic" class="pic-bar-row">
              <div class="pic-name-col">
                <strong>👤 {{ p.pic }}</strong>
                <span>{{ p.total }} Task</span>
              </div>

              <div class="pic-bar-wrap">
                <div class="stacked-bar">
                  <span
                    v-if="p.done"
                    class="bar-seg"
                    :style="{ width: (p.done / maxPicTotal * 100) + '%', backgroundColor: STATUS_COLORS.Done }"
                    title="Done"
                  />
                  <span
                    v-if="p.progress"
                    class="bar-seg"
                    :style="{ width: (p.progress / maxPicTotal * 100) + '%', backgroundColor: STATUS_COLORS.Progress }"
                    title="Progress"
                  />
                  <span
                    v-if="p.hold"
                    class="bar-seg"
                    :style="{ width: (p.hold / maxPicTotal * 100) + '%', backgroundColor: STATUS_COLORS.Hold }"
                    title="Hold"
                  />
                  <span
                    v-if="p.other"
                    class="bar-seg"
                    :style="{ width: (p.other / maxPicTotal * 100) + '%', backgroundColor: '#64748b' }"
                    title="Lainnya"
                  />
                </div>
              </div>
            </div>

            <div class="chart-legend-mini">
              <span><i style="background: #22c55e" /> Done</span>
              <span><i style="background: #38bdf8" /> Progress</span>
              <span><i style="background: #f87171" /> Hold</span>
              <span><i style="background: #64748b" /> ToDo/Backlog</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Application Modules Breakdown + Critical Items Grid -->
      <div class="dash-bottom-grid">
        <!-- App Module Cards -->
        <div class="panel app-panel">
          <div class="panel-head">
            <h3>🗂️ Distribusi Modul Aplikasi</h3>
            <span class="panel-sub">Alokasi tugas berdasarkan modul sistem</span>
          </div>

          <div class="app-cards-list">
            <div v-for="app in appChartData" :key="app.name" class="app-card-item">
              <div class="app-card-head">
                <strong>{{ app.name }}</strong>
                <span class="app-badge">{{ app.count }} Tasks ({{ app.pct }}%)</span>
              </div>
              <div class="app-progress">
                <span :style="{ width: app.pct + '%' }" />
              </div>
            </div>
          </div>
        </div>

        <!-- Focus Items Table -->
        <div class="panel focus-panel">
          <div class="panel-head">
            <h3>⚡ Fokus Perhatian Executive (Progress &amp; Hold)</h3>
            <span class="panel-sub">Daftar isu aktif yang sedang dikerjakan atau tertahan</span>
          </div>

          <div class="table-scroll focus-table-wrap">
            <table class="report">
              <thead>
                <tr>
                  <th>No</th>
                  <th>Isu / Pekerjaan</th>
                  <th>PIC</th>
                  <th>Status</th>
                  <th>Priority</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in criticalItems" :key="item.no || item.issue">
                  <td>#{{ item.no || '-' }}</td>
                  <td class="ket-cell">
                    <strong>{{ item.issue }}</strong>
                    <div class="muted small">{{ item.aplikasi }} · Sheet: {{ item.source_month }}</div>
                  </td>
                  <td>👤 {{ item.pic || '-' }}</td>
                  <td>
                    <span class="badge" :class="'s-' + item.status">{{ item.status }}</span>
                  </td>
                  <td>
                    <span
                      class="chip"
                      :class="{ 'on': item.priority && item.priority.toLowerCase().includes('high') }"
                    >
                      {{ item.priority || 'Normal' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dash-wrap {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Head Banner */
.dash-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.12), rgba(99, 102, 241, 0.08));
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: var(--radius, 14px);
  padding: 28px 32px;
  box-shadow: var(--shadow-sm);
  flex-wrap: wrap;
  gap: 20px;
}
.dash-head-text h1 {
  margin: 8px 0 4px;
  font-size: 24px;
  font-weight: 800;
  color: #ffffff;
}
.dash-head-text p {
  margin: 0;
  color: var(--text-sub, #cbd5e1);
  font-size: 14px;
}
.dash-badge {
  display: inline-block;
  background: var(--cyan, #38bdf8);
  color: #0a0e17;
  font-size: 10px;
  font-weight: 800;
  padding: 3px 10px;
  border-radius: 999px;
  letter-spacing: 0.08em;
}

.dash-actions {
  display: flex;
  align-items: flex-end;
  gap: 14px;
}
.btn-refresh {
  height: 40px;
  padding: 0 18px;
  background: #0f172a;
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: var(--radius-sm, 9px);
  color: var(--cyan, #38bdf8);
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all .18s;
}
.btn-refresh:hover:not(:disabled) {
  background: rgba(56, 189, 248, 0.15);
  border-color: var(--cyan, #38bdf8);
}
.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }

/* Top KPI Grid */
.dash-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}
.kpi-card {
  background: var(--panel, #1e293b);
  border: 1px solid var(--border, rgba(56, 189, 248, 0.28));
  border-radius: var(--radius, 14px);
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  box-shadow: var(--shadow-sm);
  transition: all .2s ease;
}
.kpi-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
  border-color: var(--border-glow, rgba(56, 189, 248, 0.45));
}
.kpi-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.kpi-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}
.kpi-label {
  font-size: 10.5px;
  font-weight: 700;
  color: var(--cyan, #38bdf8);
  letter-spacing: 0.06em;
}
.kpi-value {
  font-size: 28px;
  font-weight: 800;
  color: #ffffff;
  line-height: 1.1;
  margin: 4px 0;
  font-family: 'Plus Jakarta Sans', sans-serif;
}
.kpi-sub {
  font-size: 11px;
  color: var(--text-dim, #94a3b8);
  font-weight: 500;
}
.kpi-progress-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  overflow: hidden;
  margin-top: 6px;
}
.kpi-progress-bar span {
  display: block;
  height: 100%;
  background: var(--cyan, #38bdf8);
  box-shadow: 0 0 8px var(--cyan);
  transition: width .6s ease;
}

/* Charts Grid */
.dash-charts-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 20px;
}
@media (max-width: 1080px) {
  .dash-charts-grid { grid-template-columns: 1fr; }
}

.chart-panel {
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}
.panel-head {
  margin-bottom: 20px;
}
.panel-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  font-family: 'Plus Jakarta Sans', sans-serif;
}
.panel-sub {
  font-size: 12px;
  color: var(--text-sub, #cbd5e1);
  display: block;
  margin-top: 2px;
}

/* Donut Body */
.donut-body {
  display: flex;
  align-items: center;
  gap: 28px;
  flex-wrap: wrap;
  justify-content: center;
  padding: 10px 0;
}
.svg-container {
  position: relative;
  width: 190px;
  height: 190px;
}
.donut-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.donut-segment {
  transition: all .25s ease;
  cursor: pointer;
}
.donut-segment:hover, .donut-segment.active {
  filter: brightness(1.2);
  transform: scale(1.03);
  transform-origin: center;
}
.donut-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
.center-num {
  font-size: 26px;
  font-weight: 800;
  color: #ffffff;
  line-height: 1;
}
.center-label {
  font-size: 11px;
  color: var(--text-sub, #cbd5e1);
  font-weight: 600;
}

/* Donut Legend */
.donut-legend {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  min-width: 180px;
}
.legend-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid transparent;
  transition: all .18s;
  cursor: pointer;
}
.legend-row:hover, .legend-row.active {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.3);
}
.leg-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.leg-name {
  font-size: 12.5px;
  font-weight: 600;
  color: #f1f5f9;
  flex: 1;
}
.leg-val {
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
}
.leg-pct {
  font-size: 11px;
  color: var(--cyan, #38bdf8);
  font-weight: 700;
  min-width: 36px;
  text-align: right;
}

/* PIC Bar Chart */
.pic-chart-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.pic-bar-row {
  display: grid;
  grid-template-columns: 140px 1fr;
  align-items: center;
  gap: 14px;
}
.pic-name-col strong {
  display: block;
  font-size: 13px;
  color: #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pic-name-col span {
  font-size: 11px;
  color: var(--text-dim, #94a3b8);
  font-weight: 500;
}
.pic-bar-wrap {
  width: 100%;
}
.stacked-bar {
  height: 14px;
  background: #0f172a;
  border-radius: 999px;
  overflow: hidden;
  display: flex;
  border: 1px solid rgba(56, 189, 248, 0.2);
}
.bar-seg {
  height: 100%;
  transition: width .5s ease;
}

.chart-legend-mini {
  display: flex;
  gap: 16px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border-soft);
  font-size: 11px;
  color: var(--text-sub);
  flex-wrap: wrap;
}
.chart-legend-mini span {
  display: flex;
  align-items: center;
  gap: 6px;
}
.chart-legend-mini i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

/* Bottom Grid */
.dash-bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1.3fr;
  gap: 20px;
}
@media (max-width: 1080px) {
  .dash-bottom-grid { grid-template-columns: 1fr; }
}

.app-cards-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.app-card-item {
  background: #0f172a;
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 10px;
  padding: 12px 16px;
}
.app-card-head {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 8px;
}
.app-card-head strong { color: #f1f5f9; }
.app-badge { font-size: 11px; color: var(--cyan); font-weight: 700; }
.app-progress {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  overflow: hidden;
}
.app-progress span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--cyan), var(--indigo));
}

.focus-table-wrap {
  max-height: 280px;
}
.small { font-size: 11px; margin-top: 2px; }

/* Skeleton */
.skel-wrap { display: flex; flex-direction: column; gap: 20px; }
.skel-chart { height: 260px; border-radius: var(--radius); }
.skel-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
</style>
