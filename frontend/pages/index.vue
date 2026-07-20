<script setup lang="ts">
import { ref, computed, onMounted } from "vue";

// Access report API base & auth
const sources = ref<{ id: string; name: string }[]>([]);
const selectedSource = ref<string>("");
const loading = ref(true);
const error = ref("");
const picSearch = ref("");

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
      const reportRes = await apiGet<any>(`/api/report?source=${encodeURIComponent(selectedSource.value)}&period=all`);
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

// PIC Workload & Productivity Detailed Analytics
const picDetailedData = computed(() => {
  const byPic = summary.value?.by_pic_status || {};
  const list = Object.entries(byPic).map(([pic, data]: [string, any]) => {
    const total = data.total || 0;
    const done = data.by_status?.Done || 0;
    const progress = data.by_status?.Progress || 0;
    const hold = data.by_status?.Hold || 0;
    const todo = data.by_status?.["To Do"] || 0;
    const backlog = data.by_status?.["Back Log"] || 0;
    const rate = total > 0 ? Math.round((done / total) * 100) : 0;

    let performanceLabel = "Normal";
    let performanceClass = "perf-ok";
    if (hold > 0) {
      performanceLabel = "Perlu Perhatian";
      performanceClass = "perf-warning";
    } else if (rate >= 75) {
      performanceLabel = "Sangat Baik";
      performanceClass = "perf-high";
    }

    // Avatar initials
    const parts = pic.split(/[,\s]+/);
    const initials = parts.length > 1
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : pic.slice(0, 2).toUpperCase();

    return {
      pic,
      initials,
      total,
      done,
      progress,
      hold,
      todo,
      backlog,
      rate,
      performanceLabel,
      performanceClass,
    };
  }).sort((a, b) => b.total - a.total);

  if (!picSearch.value.trim()) return list;
  const q = picSearch.value.toLowerCase();
  return list.filter((p) => p.pic.toLowerCase().includes(q));
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
        <p>Ringkasan analitik real-time progress pekerjaan, beban kerja PIC, dan performa tim.</p>
      </div>

      <div class="dash-actions">
        <div class="field">
          <label>Sumber Data</label>
          <select v-model="selectedSource" @change="loadDashboardData">
            <option v-for="s in sources" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </div>
        <button class="btn-refresh" :disabled="loading" @click="loadDashboardData" title="Refresh Data">
          <span :class="{ spinning: loading }"><UiIcon name="refresh" :size="16" /></span> Refresh
        </button>
      </div>
    </div>

    <!-- Error Banner -->
    <div v-if="error" class="error">{{ error }}</div>

    <!-- ============================================================
         SKELETON LOADER UNTUK SELURUH PANEL DASHBOARD
         ============================================================ -->
    <div v-if="loading" class="skel-wrap">
      <!-- 1. Skeleton Top KPI Bar (5 cards) -->
      <div class="dash-kpi-grid">
        <div v-for="i in 5" :key="i" class="kpi-card skel-card">
          <div class="skel skel-icon" />
          <div class="skel-content">
            <div class="skel skel-line sm" />
            <div class="skel skel-line lg" />
            <div class="skel skel-line xs" />
          </div>
        </div>
      </div>

      <!-- 2. Skeleton Charts Grid (2 panels) -->
      <div class="dash-charts-grid">
        <div class="panel skel-panel">
          <div class="skel skel-title" />
          <div class="skel-donut-body">
            <div class="skel skel-circle" />
            <div class="skel-legend-lines">
              <div v-for="i in 5" :key="i" class="skel skel-line md" />
            </div>
          </div>
        </div>

        <div class="panel skel-panel">
          <div class="skel skel-title" />
          <div class="skel-bars-body">
            <div v-for="i in 4" :key="i" class="skel-bar-item">
              <div class="skel skel-line sm" />
              <div class="skel skel-bar" />
            </div>
          </div>
        </div>
      </div>

      <!-- 3. Skeleton PIC Dual Hub 2-Column Grid -->
      <div class="pic-dual-grid">
        <div class="panel skel-panel">
          <div class="skel skel-title" />
          <div class="skel-pic-cards">
            <div v-for="i in 4" :key="i" class="skel skel-pic-card" />
          </div>
        </div>

        <div class="panel skel-panel">
          <div class="skel skel-title" />
          <div class="skel-table">
            <div class="skel skel-row head" />
            <div v-for="i in 5" :key="i" class="skel skel-row" />
          </div>
        </div>
      </div>

      <!-- 4. Skeleton Focus Items Table -->
      <div class="panel skel-panel">
        <div class="skel skel-title" />
        <div class="skel-table">
          <div class="skel skel-row head" />
          <div v-for="i in 4" :key="i" class="skel skel-row" />
        </div>
      </div>
    </div>

    <!-- MAIN DASHBOARD CONTENT -->
    <template v-else>
      <!-- KPI Top Metrics Bar -->
      <div class="dash-kpi-grid">
        <div class="kpi-card kpi-total">
          <div class="kpi-icon"><UiIcon name="dashboard" :size="22" color="#38bdf8" /></div>
          <div class="kpi-content">
            <span class="kpi-label">TOTAL TUGAS / ISU</span>
            <div class="kpi-value">{{ totalTasks }}</div>
            <span class="kpi-sub">Akumulasi seluruh sumber</span>
          </div>
        </div>

        <div class="kpi-card kpi-rate">
          <div class="kpi-icon"><UiIcon name="check" :size="22" color="#22c55e" /></div>
          <div class="kpi-content">
            <span class="kpi-label">TINGKAT PENYELESAIAN</span>
            <div class="kpi-value">{{ completionRate }}%</div>
            <div class="kpi-progress-bar">
              <span :style="{ width: completionRate + '%' }" />
            </div>
          </div>
        </div>

        <div class="kpi-card kpi-progress">
          <div class="kpi-icon"><UiIcon name="clock" :size="22" color="#38bdf8" /></div>
          <div class="kpi-content">
            <span class="kpi-label">DALAM PROSES (PROGRESS)</span>
            <div class="kpi-value">{{ statusCounts.progress }}</div>
            <span class="kpi-sub">Pekerjaan aktif berjalan</span>
          </div>
        </div>

        <div class="kpi-card kpi-hold">
          <div class="kpi-icon"><UiIcon name="filter" :size="22" color="#f87171" /></div>
          <div class="kpi-content">
            <span class="kpi-label">TERTAHAN (HOLD)</span>
            <div class="kpi-value">{{ statusCounts.hold }}</div>
            <span class="kpi-sub">Memerlukan perhatian</span>
          </div>
        </div>

        <div class="kpi-card kpi-priority">
          <div class="kpi-icon"><UiIcon name="monitoring" :size="22" color="#f59e0b" /></div>
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
            <h3><UiIcon name="dashboard" :size="18" /> Distribusi Status Pekerjaan</h3>
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

        <!-- Application Modules Breakdown -->
        <div class="panel app-panel">
          <div class="panel-head">
            <h3><UiIcon name="project_mgmt" :size="18" /> Distribusi Modul Aplikasi</h3>
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
      </div>

      <!-- ============================================================
           EXECUTIVE PIC MONITORING DUAL 2-COLUMN GRID (1 BARIS SEJAJAR)
           ============================================================ -->
      <div class="pic-dual-grid">
        <!-- Kolom 1: Monitoring Performa & Beban Kerja per PIC (Cards) -->
        <div class="panel pic-monitoring-panel">
          <div class="panel-head">
            <h3><UiIcon name="users" :size="18" color="#38bdf8" /> Monitoring Performa per PIC</h3>
            <span class="panel-sub">Ringkasan produktivitas &amp; tingkat penyelesaian</span>
          </div>

          <div class="pic-cards-column">
            <div v-for="p in picDetailedData" :key="p.pic" class="pic-exec-card">
              <div class="pic-card-top">
                <div class="pic-avatar-badge">{{ p.initials }}</div>
                <div class="pic-identity">
                  <h4>{{ p.pic }}</h4>
                  <span class="pic-task-count">{{ p.total }} Task Assigned</span>
                </div>
                <span class="pic-status-pill" :class="p.performanceClass">{{ p.performanceLabel }}</span>
              </div>

              <div class="pic-card-mid">
                <div class="pic-rate-row">
                  <span>Solvability</span>
                  <strong>{{ p.rate }}% Solved ({{ p.done }}/{{ p.total }})</strong>
                </div>
                <div class="pic-progress-bar">
                  <span class="bar-done" :style="{ width: p.rate + '%' }" />
                </div>
              </div>

              <div class="pic-mini-metrics">
                <div class="mini-m green"><span>Done</span><strong>{{ p.done }}</strong></div>
                <div class="mini-m cyan"><span>Prog</span><strong>{{ p.progress }}</strong></div>
                <div class="mini-m red" :class="{ alert: p.hold > 0 }"><span>Hold</span><strong>{{ p.hold }}</strong></div>
                <div class="mini-m slate"><span>ToDo</span><strong>{{ p.todo + p.backlog }}</strong></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Kolom 2: Matriks Performa Detail PIC (Table Matrix) -->
        <div class="panel pic-matrix-panel">
          <div class="row-between panel-head">
            <div class="panel-head-group">
              <h3><UiIcon name="sources" :size="18" color="#38bdf8" /> Matriks Performa Detail PIC</h3>
              <span class="panel-sub">Tabel detail perolehan status &amp; performa tim</span>
            </div>
            <div class="pic-search-box">
              <span class="search-ico"><UiIcon name="search" :size="14" /></span>
              <input v-model="picSearch" type="text" placeholder="Cari PIC..." />
            </div>
          </div>

          <div class="table-scroll pic-table-wrap">
            <table class="report pic-matrix-table">
              <thead>
                <tr>
                  <th>PIC</th>
                  <th>Total</th>
                  <th>Done</th>
                  <th>Prog</th>
                  <th>Hold</th>
                  <th>Penyelesaian</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in picDetailedData" :key="p.pic">
                  <td class="pic-name-cell">
                    <span class="mini-avatar">{{ p.initials }}</span>
                    <strong>{{ p.pic }}</strong>
                  </td>
                  <td class="num-cell"><strong>{{ p.total }}</strong></td>
                  <td><span class="badge s-Done">{{ p.done }}</span></td>
                  <td><span class="badge s-Progress">{{ p.progress }}</span></td>
                  <td><span class="badge s-Hold" :class="{ 'has-hold': p.hold > 0 }">{{ p.hold }}</span></td>
                  <td class="rate-cell">
                    <div class="rate-bar-wrap">
                      <div class="rate-bar"><span :style="{ width: p.rate + '%' }" /></div>
                      <span class="rate-num">{{ p.rate }}%</span>
                    </div>
                  </td>
                  <td>
                    <span class="perf-badge" :class="p.performanceClass">
                      {{ p.performanceLabel }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Focus Items Table (Progress & Hold) -->
      <div class="panel focus-panel">
        <div class="panel-head">
          <h3><UiIcon name="filter" :size="18" /> Fokus Perhatian Executive (Progress &amp; Hold)</h3>
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
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.14), rgba(99, 102, 241, 0.09));
  border: 1px solid var(--border-soft);
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
  color: var(--text);
  font-family: 'Outfit', sans-serif;
}
.dash-head-text p {
  margin: 0;
  color: var(--text-sub);
  font-size: 14px;
}
.dash-badge {
  display: inline-block;
  background: var(--cyan);
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
.dash-actions label {
  color: var(--cyan);
  font-weight: 700;
}
.btn-refresh {
  height: 40px;
  padding: 0 18px;
  background: var(--bg-3);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm, 9px);
  color: var(--cyan);
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all .18s;
}
.btn-refresh:hover:not(:disabled) {
  background: var(--cyan-glass);
  border-color: var(--cyan);
}
.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }

/* ============================================================
   SKELETON LOADER STYLES
   ============================================================ */
.skel-wrap {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.skel-panel {
  padding: 24px;
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius, 14px);
}
.skel {
  background: linear-gradient(90deg, var(--bg-2) 25%, var(--cyan-glass) 50%, var(--bg-2) 75%);
  background-size: 200% 100%;
  animation: skelPulse 1.5s infinite ease-in-out;
  border-radius: 6px;
}
@keyframes skelPulse {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skel-icon { width: 44px; height: 44px; border-radius: 12px; }
.skel-content { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.skel-line { height: 12px; }
.skel-line.xs { width: 40%; height: 10px; }
.skel-line.sm { width: 60%; }
.skel-line.md { width: 85%; height: 16px; }
.skel-line.lg { width: 70%; height: 24px; }
.skel-title { width: 40%; height: 20px; margin-bottom: 20px; }

.skel-donut-body { display: flex; align-items: center; gap: 28px; }
.skel-circle { width: 140px; height: 140px; border-radius: 50%; flex-shrink: 0; }
.skel-legend-lines { flex: 1; display: flex; flex-direction: column; gap: 10px; }

.skel-bars-body { display: flex; flex-direction: column; gap: 14px; }
.skel-bar-item { display: flex; flex-direction: column; gap: 6px; }
.skel-bar { height: 12px; border-radius: 999px; }

.skel-pic-cards { display: flex; flex-direction: column; gap: 12px; }
.skel-pic-card { height: 86px; border-radius: 12px; }

.skel-table { display: flex; flex-direction: column; gap: 8px; }
.skel-row { height: 36px; border-radius: 8px; }
.skel-row.head { height: 40px; background: var(--cyan-glass); }

/* Top KPI Grid */
.dash-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}
.kpi-card {
  background: var(--panel);
  border: 1px solid var(--border);
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
  border-color: var(--border-glow);
}
.kpi-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--cyan-glass);
  border: 1px solid var(--border-soft);
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
  color: var(--cyan);
  letter-spacing: 0.06em;
}
.kpi-value {
  font-size: 28px;
  font-weight: 800;
  color: var(--text);
  line-height: 1.1;
  margin: 4px 0;
  font-family: 'Outfit', sans-serif;
}
.kpi-sub {
  font-size: 11px;
  color: var(--text-dim);
  font-weight: 500;
}
.kpi-progress-bar {
  height: 4px;
  background: var(--bg-2);
  border-radius: 999px;
  overflow: hidden;
  margin-top: 6px;
}
.kpi-progress-bar span {
  display: block;
  height: 100%;
  background: var(--cyan);
  box-shadow: 0 0 8px var(--cyan);
  transition: width .6s ease;
}

/* Charts Grid */
.dash-charts-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
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
  color: var(--text);
  font-family: 'Outfit', sans-serif;
  display: flex;
  align-items: center;
  gap: 8px;
}
.panel-sub {
  font-size: 12px;
  color: var(--text-sub);
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
  color: var(--text);
  line-height: 1;
}
.center-label {
  font-size: 11px;
  color: var(--text-sub);
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
  background: var(--bg-2);
  border: 1px solid var(--border-soft);
  transition: all .18s;
  cursor: pointer;
}
.legend-row:hover, .legend-row.active {
  background: var(--cyan-glass);
  border-color: var(--cyan);
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
  color: var(--text);
  flex: 1;
}
.leg-val {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
}
.leg-pct {
  font-size: 11px;
  color: var(--cyan);
  font-weight: 700;
  min-width: 36px;
  text-align: right;
}

/* App Modules List */
.app-cards-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.app-card-item {
  background: var(--bg-2);
  border: 1px solid var(--border-soft);
  border-radius: 10px;
  padding: 12px 16px;
}
.app-card-head {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 8px;
}
.app-card-head strong { color: var(--text); }
.app-badge { font-size: 11px; color: var(--cyan); font-weight: 700; }
.app-progress {
  height: 6px;
  background: var(--bg-3);
  border-radius: 999px;
  overflow: hidden;
}
.app-progress span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--cyan), var(--indigo));
  box-shadow: 0 0 6px var(--cyan);
}

/* ============================================================
   EXECUTIVE PIC MONITORING DUAL 2-COLUMN GRID (1 BARIS SEJAJAR)
   ============================================================ */
.pic-dual-grid {
  display: grid;
  grid-template-columns: 1fr 1.25fr;
  gap: 20px;
}
@media (max-width: 1180px) {
  .pic-dual-grid {
    grid-template-columns: 1fr;
  }
}

.pic-monitoring-panel, .pic-matrix-panel {
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
}

.pic-cards-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 480px;
  overflow-y: auto;
  padding-right: 4px;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}
.pic-cards-column::-webkit-scrollbar { width: 4px; }
.pic-cards-column::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

.pic-exec-card {
  background: var(--bg-2);
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: all .2s ease;
}
.pic-exec-card:hover {
  border-color: var(--cyan);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.pic-card-top {
  display: flex;
  align-items: center;
  gap: 10px;
}
.pic-avatar-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--cyan), var(--indigo));
  color: #ffffff;
  font-weight: 800;
  font-size: 13.5px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
}
.pic-identity {
  flex: 1;
  min-width: 0;
}
.pic-identity h4 {
  margin: 0;
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pic-task-count {
  font-size: 11px;
  color: var(--text-dim);
}

.pic-status-pill {
  font-size: 9.5px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}
.perf-high { background: rgba(34, 197, 94, 0.18); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.35); }
.perf-ok { background: rgba(56, 189, 248, 0.18); color: var(--cyan); border: 1px solid rgba(56, 189, 248, 0.35); }
.perf-warning { background: rgba(248, 113, 113, 0.18); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.35); }

.pic-card-mid {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.pic-rate-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--text-sub);
}
.pic-rate-row strong {
  color: var(--cyan);
  font-weight: 700;
}
.pic-progress-bar {
  height: 5px;
  background: var(--bg-3);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid var(--border-soft);
}
.bar-done {
  display: block;
  height: 100%;
  background: #22c55e;
  box-shadow: 0 0 6px #22c55e;
  transition: width .5s ease;
}

.pic-mini-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
}
.mini-m {
  background: var(--bg-3);
  border: 1px solid var(--border-soft);
  border-radius: 6px;
  padding: 4px 4px;
  text-align: center;
  display: flex;
  flex-direction: column;
}
.mini-m span { font-size: 9px; color: var(--text-dim); text-transform: uppercase; font-weight: 600; line-height: 1; }
.mini-m strong { font-size: 12px; color: var(--text); font-weight: 800; line-height: 1.2; }
.mini-m.green strong { color: #22c55e; }
.mini-m.cyan strong { color: var(--cyan); }
.mini-m.red strong { color: #f87171; }
.mini-m.red.alert { background: rgba(248, 113, 113, 0.12); border-color: rgba(248, 113, 113, 0.3); }

/* Table Matrix */
.pic-search-box {
  display: flex;
  align-items: center;
  background: var(--bg-3);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm, 9px);
  padding: 0 10px;
  width: 180px;
}
.search-ico { color: var(--cyan); display: flex; align-items: center; }
.pic-search-box input {
  border: none; outline: none; background: transparent;
  padding: 6px 8px; font-size: 12px; color: var(--text); width: 100%;
}

.pic-table-wrap {
  border: 1px solid var(--border-soft);
  border-radius: 10px;
  overflow-y: auto;
  max-height: 480px;
  background: var(--bg-3);
}
.pic-matrix-table { margin: 0; width: 100%; }
.pic-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.mini-avatar {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: var(--cyan-glass);
  color: var(--cyan);
  font-size: 10px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}
.num-cell { font-size: 13px; font-weight: 800; color: var(--text); }
.badge.s-Hold.has-hold { background: rgba(248, 113, 113, 0.25); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.4); }

.rate-cell { min-width: 110px; }
.rate-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rate-bar {
  flex: 1;
  height: 5px;
  background: var(--bg-2);
  border-radius: 999px;
  overflow: hidden;
}
.rate-bar span {
  display: block;
  height: 100%;
  background: #22c55e;
}
.rate-num { font-size: 11.5px; font-weight: 700; color: var(--text); width: 32px; }

.perf-badge {
  font-size: 9.5px;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 999px;
}
</style>
