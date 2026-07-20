<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useProjects } from "~/composables/useProjects";

const p = useProjects();

const TABS = [
  { key: "overview", label: "📊 Overview" },
  { key: "mapping", label: "🧑‍🤝‍🧑 Load Mapping" },
  { key: "target", label: "🎯 Target Bulanan" },
  { key: "tw", label: "🗓️ TW per Divisi" },
] as const;
const tab = ref<(typeof TABS)[number]["key"]>("overview");
const targetMonth = ref<string>("");

watch(() => p.targets.value, (t) => {
  if (t && !targetMonth.value && t.months.length) targetMonth.value = t.months[t.months.length - 1].month;
});
const currentMonth = computed(() =>
  p.targets.value?.months.find((m) => m.month === targetMonth.value) || null,
);

onMounted(() => p.init());

// Auto-tarik ulang daftar saat filter berubah (ringkasan tetap global).
watch(
  () => ({ ...p.f.value }),
  () => { if (!p.initializing.value) p.loadList(); },
  { deep: true },
);

// --- Formatters ---
function rupiah(v: number): string {
  if (!v) return "Rp 0";
  const abs = Math.abs(v);
  if (abs >= 1e9) return `Rp ${(v / 1e9).toFixed(2)} M`;
  if (abs >= 1e6) return `Rp ${(v / 1e6).toFixed(1)} Jt`;
  if (abs >= 1e3) return `Rp ${(v / 1e3).toFixed(0)} rb`;
  return `Rp ${v.toFixed(0)}`;
}
function pct(v: number): string {
  return `${Math.round((v || 0) * 100)}%`;
}
function tanggal(v: string | null): string {
  if (!v) return "–";
  const d = new Date(v + "T00:00:00");
  return d.toLocaleDateString("id-ID", { day: "2-digit", month: "short", year: "numeric" });
}

const STATUS_META: Record<string, { cls: string; icon: string }> = {
  Done: { cls: "s-Done", icon: "✅" },
  Progress: { cls: "s-Progress", icon: "🔄" },
  "In Progress": { cls: "s-Progress", icon: "🔄" },
  Upcoming: { cls: "s-Upcoming", icon: "🕒" },
  Maintenance: { cls: "s-Maintenance", icon: "🛠️" },
  "Not Achieve": { cls: "s-Maintenance", icon: "❌" },
  Adjustment: { cls: "s-Upcoming", icon: "⚙️" },
  "To Do": { cls: "s-None", icon: "📝" },
  "Tanpa Status": { cls: "s-None", icon: "❔" },
};
function stMeta(s: string) {
  return STATUS_META[s] || { cls: "s-None", icon: "▫️" };
}

const maxLoad = computed(() =>
  Math.max(1, ...(p.loadMapping.value?.member_totals.map((m) => m.total_load) || [1])),
);
function statusEntries(obj: Record<string, number>) {
  return Object.entries(obj).sort((a, b) => b[1] - a[1]);
}

const totals = computed(() => p.summary.value?.totals);
// Bendera bar: proporsi jumlah proyek.
const benderaRows = computed(() => {
  const b = p.summary.value?.by_bendera || {};
  const max = Math.max(1, ...Object.values(b));
  return Object.entries(b).map(([name, count]) => ({ name, count, w: (count / max) * 100 }));
});
function achClass(rate: number): string {
  if (rate >= 90) return "ach-good";
  if (rate >= 70) return "ach-mid";
  return "ach-low";
}
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h2 class="pg-title">🗂️ Project Management</h2>
        <p class="pg-sub">
          Monitoring proyek & evaluasi pencapaian per triwulan —
          <em>{{ p.summary.value?.source || "Project List MST 2026" }}</em>
        </p>
      </div>
      <div class="head-actions">
        <button class="btn-ghost" :disabled="p.refreshing.value || p.initializing.value" @click="p.refreshData()">
          {{ p.refreshing.value ? "⏳ Memuat…" : "🔄 Refresh Data" }}
        </button>
        <button class="btn-primary" :disabled="p.initializing.value" @click="p.exportXlsx()">
          ⬇️ Export XLSX
        </button>
      </div>
    </div>

    <!-- Tab bar -->
    <div class="tabbar">
      <button v-for="t in TABS" :key="t.key" class="tab" :class="{ active: tab === t.key }" @click="tab = t.key">
        {{ t.label }}
      </button>
    </div>

    <div v-if="p.error.value" class="error">{{ p.error.value }}</div>

    <template v-if="p.initializing.value">
      <div class="panel"><p class="muted">Memuat data project management…</p></div>
    </template>

    <template v-else>
      <div class="page-grid">
        <div class="page-body">
          <!-- ============================================================= -->
          <!-- TAB: OVERVIEW                                                  -->
          <!-- ============================================================= -->
          <template v-if="tab === 'overview' && totals">
      <!-- ===================== KPI ===================== -->
      <div class="cards">
        <div class="metric metric-hero">
          <div class="metric-top"><div class="metric-ico">📊</div>
            <span class="metric-tag">{{ totals.done }} selesai</span>
          </div>
          <div class="metric-num">{{ totals.projects }}</div>
          <div class="metric-lbl">Total Proyek</div>
        </div>
        <div class="metric m-blue">
          <div class="metric-top"><div class="metric-ico">💰</div></div>
          <div class="metric-num sm">{{ rupiah(totals.nilai_project) }}</div>
          <div class="metric-lbl">Total Nilai Project</div>
        </div>
        <div class="metric m-green">
          <div class="metric-top"><div class="metric-ico">🎯</div>
            <span class="metric-tag">{{ totals.achievement_rate }}%</span>
          </div>
          <div class="metric-num sm">{{ rupiah(totals.nilai_pencapaian) }}</div>
          <div class="metric-lbl">Nilai Pencapaian</div>
        </div>
        <div class="metric m-purple">
          <div class="metric-top"><div class="metric-ico">🏦</div>
            <span class="metric-tag">{{ totals.pencairan_rate }}%</span>
          </div>
          <div class="metric-num sm">{{ rupiah(totals.nilai_pencairan) }}</div>
          <div class="metric-lbl">Nilai Pencairan</div>
        </div>
        <div class="metric m-amber">
          <div class="metric-top"><div class="metric-ico">📈</div></div>
          <div class="metric-num">{{ totals.avg_progress }}%</div>
          <div class="metric-lbl">Rata-rata Progress</div>
        </div>
        <div class="metric" :class="totals.overdue ? 'm-red' : 'm-slate'">
          <div class="metric-top"><div class="metric-ico">⚠️</div></div>
          <div class="metric-num">{{ totals.overdue }}</div>
          <div class="metric-lbl">Proyek Overdue</div>
        </div>
      </div>

      <!-- ===================== EVALUASI TRIWULAN ===================== -->
      <div class="panel">
        <div class="panel-title"><span class="dot" />Pencapaian & Evaluasi per Triwulan</div>
        <div class="tw-grid">
          <div v-for="t in p.summary.value!.triwulan" :key="t.triwulan" class="tw-card">
            <div class="tw-head">
              <strong>{{ t.triwulan }}</strong>
              <span class="tw-count">{{ t.count }} proyek</span>
            </div>
            <div class="tw-stats">
              <span class="chip s-Done">✅ {{ t.done }}</span>
              <span class="chip s-Progress">🔄 {{ t.progress }}</span>
              <span v-if="t.overdue" class="chip s-Maintenance">⚠️ {{ t.overdue }}</span>
            </div>

            <div class="bar-row">
              <div class="bar-label"><span>Pencapaian</span><span>{{ t.achievement_rate }}%</span></div>
              <div class="bar"><span :class="achClass(t.achievement_rate)"
                :style="{ width: Math.min(100, t.achievement_rate) + '%' }" /></div>
            </div>
            <div class="bar-row">
              <div class="bar-label"><span>Avg Progress</span><span>{{ t.avg_progress }}%</span></div>
              <div class="bar"><span class="ach-mid" :style="{ width: Math.min(100, t.avg_progress) + '%' }" /></div>
            </div>

            <div class="tw-money">
              <div><small>Nilai</small><b>{{ rupiah(t.nilai_project) }}</b></div>
              <div><small>Pencapaian</small><b>{{ rupiah(t.nilai_pencapaian) }}</b></div>
            </div>
            <p class="tw-eval">{{ t.evaluasi }}</p>
          </div>
        </div>
      </div>

      <!-- ===================== BREAKDOWN ===================== -->
      <div class="grid-2">
        <div class="panel">
          <div class="panel-title"><span class="dot" />Distribusi Status & Section</div>
          <div class="pill-wrap">
            <span v-for="(c, s) in p.summary.value!.by_status" :key="s" class="badge" :class="stMeta(String(s)).cls">
              {{ stMeta(String(s)).icon }} {{ s }} · {{ c }}
            </span>
          </div>
          <div class="pill-wrap mt">
            <span v-for="(c, s) in p.summary.value!.by_section" :key="s" class="badge s-None">
              📁 {{ s }} · {{ c }}
            </span>
          </div>
        </div>

        <div class="panel">
          <div class="panel-title"><span class="dot" />Proyek per Bendera</div>
          <div class="bendera-list">
            <div v-for="b in benderaRows" :key="b.name" class="bendera-row">
              <span class="bendera-name">{{ b.name }}</span>
              <div class="bar"><span class="ach-good" :style="{ width: b.w + '%' }" /></div>
              <span class="bendera-count">{{ b.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ===================== PIC ===================== -->
      <div class="panel">
        <div class="panel-title"><span class="dot" />Kinerja per PIC</div>
        <div class="table-scroll">
          <table class="report">
            <thead>
              <tr><th>PIC</th><th>Total</th><th>Done</th><th>Done Rate</th><th>Nilai Pencapaian</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in p.summary.value!.by_pic" :key="row.pic">
                <td>{{ row.pic }}</td>
                <td><strong>{{ row.total }}</strong></td>
                <td>{{ row.done }}</td>
                <td>
                  <div class="mini-bar"><span class="ach-good" :style="{ width: row.done_rate + '%' }" /></div>
                  <small>{{ row.done_rate }}%</small>
                </td>
                <td>{{ rupiah(row.nilai_pencapaian) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ===================== ALERTS ===================== -->
      <div class="panel" v-if="p.summary.value!.alerts.overdue.length || p.summary.value!.alerts.due_soon.length">
        <div class="panel-title"><span class="dot red" />Peringatan Monitoring</div>
        <div v-if="p.summary.value!.alerts.overdue.length">
          <h4 class="alert-h red">⚠️ Overdue (kontrak lewat, progres &lt; 100%)</h4>
          <div class="table-scroll">
            <table class="report">
              <thead><tr><th>Instansi</th><th>Pekerjaan</th><th>PIC</th><th>Akhir Kontrak</th><th>Progress</th><th>Terlambat</th></tr></thead>
              <tbody>
                <tr v-for="(r, i) in p.summary.value!.alerts.overdue" :key="'o'+i">
                  <td>{{ r.instansi }}</td><td>{{ r.nama_pekerjaan }}</td><td>{{ r.pic }}</td>
                  <td>{{ tanggal(r.akhir_kontrak) }}</td><td>{{ pct(r.progress) }}</td>
                  <td><span class="badge s-Maintenance">{{ r.days }} hari</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-if="p.summary.value!.alerts.due_soon.length" class="mt">
          <h4 class="alert-h amber">🕒 Jatuh tempo ≤ 30 hari</h4>
          <div class="table-scroll">
            <table class="report">
              <thead><tr><th>Instansi</th><th>Pekerjaan</th><th>PIC</th><th>Akhir Kontrak</th><th>Progress</th><th>Sisa</th></tr></thead>
              <tbody>
                <tr v-for="(r, i) in p.summary.value!.alerts.due_soon" :key="'d'+i">
                  <td>{{ r.instansi }}</td><td>{{ r.nama_pekerjaan }}</td><td>{{ r.pic }}</td>
                  <td>{{ tanggal(r.akhir_kontrak) }}</td><td>{{ pct(r.progress) }}</td>
                  <td><span class="badge s-Upcoming">{{ Math.abs(r.days) }} hari</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ===================== DAFTAR PROYEK + FILTER ===================== -->
      <div class="panel">
        <div class="panel-title"><span class="dot" />Daftar Proyek</div>
        <div class="controls">
          <div class="field">
            <label>🔎 Cari</label>
            <input v-model="p.f.value.q" type="text" placeholder="Instansi / pekerjaan…" />
          </div>
          <div class="field">
            <label>Section</label>
            <select v-model="p.f.value.section">
              <option value="">Semua</option>
              <option v-for="s in p.filters.value.sections" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="field">
            <label>Status</label>
            <select v-model="p.f.value.status">
              <option value="">Semua</option>
              <option v-for="s in p.filters.value.statuses" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="field">
            <label>Triwulan</label>
            <select v-model="p.f.value.triwulan">
              <option value="">Semua</option>
              <option v-for="s in p.filters.value.triwulan" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="field">
            <label>PIC</label>
            <select v-model="p.f.value.pic">
              <option value="">Semua</option>
              <option v-for="s in p.filters.value.pics" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="field">
            <label>Bendera</label>
            <select v-model="p.f.value.bendera">
              <option value="">Semua</option>
              <option v-for="s in p.filters.value.benderas" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="field field-btn">
            <label>&nbsp;</label>
            <button class="btn-ghost" :disabled="!p.hasFilter.value" @click="p.resetFilters()">Reset</button>
          </div>
        </div>

        <div v-if="!p.projects.value.length" class="empty-state">
          <div class="empty-ico">🗂️</div><p>Tidak ada proyek untuk filter ini.</p>
        </div>
        <div v-else class="table-scroll">
          <table class="report">
            <thead>
              <tr>
                <th>#</th><th>Instansi</th><th>Pekerjaan</th><th>Bendera</th><th>PIC</th>
                <th>Status</th><th>Progress</th><th>Triwulan</th><th>Akhir Kontrak</th>
                <th>Nilai</th><th>Pencapaian</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in p.projects.value" :key="i">
                <td>{{ i + 1 }}</td>
                <td>{{ row.instansi }}</td>
                <td class="wrap">{{ row.nama_pekerjaan || "–" }}</td>
                <td>{{ row.bendera }}</td>
                <td>{{ row.pic_names.join(", ") || "–" }}</td>
                <td><span class="badge" :class="stMeta(row.status).cls">{{ stMeta(row.status).icon }} {{ row.status }}</span></td>
                <td>
                  <div class="mini-bar"><span :class="row.progress >= 0.999 ? 'ach-good' : 'ach-mid'" :style="{ width: (row.progress * 100) + '%' }" /></div>
                  <small>{{ pct(row.progress) }}</small>
                </td>
                <td>{{ row.triwulan }}</td>
                <td>{{ tanggal(row.akhir_kontrak) }}</td>
                <td>{{ rupiah(row.nilai_project) }}</td>
                <td>{{ rupiah(row.nilai_pencapaian) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- ============================================================= -->
    <!-- TAB: LOAD MAPPING                                              -->
    <!-- ============================================================= -->
    <template v-else-if="tab === 'mapping' && p.loadMapping.value">
      <div class="cards">
        <div class="metric metric-hero">
          <div class="metric-top"><div class="metric-ico">🧑‍🤝‍🧑</div></div>
          <div class="metric-num">{{ p.loadMapping.value.counts.total }}</div>
          <div class="metric-lbl">Proyek Ter-mapping</div>
        </div>
        <div class="metric m-green">
          <div class="metric-top"><div class="metric-ico">✅</div></div>
          <div class="metric-num">{{ p.loadMapping.value.counts.done }}</div>
          <div class="metric-lbl">Selesai</div>
        </div>
        <div class="metric m-blue">
          <div class="metric-top"><div class="metric-ico">👥</div></div>
          <div class="metric-num">{{ p.loadMapping.value.members.length }}</div>
          <div class="metric-lbl">Anggota Tim</div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title"><span class="dot" />Beban Kerja per Anggota (jumlah porsi lintas proyek)</div>
        <div class="bendera-list">
          <div v-for="mrow in p.loadMapping.value.member_totals" :key="mrow.member" class="bendera-row load">
            <span class="bendera-name">{{ mrow.member }}</span>
            <div class="bar"><span class="ach-mid" :style="{ width: (mrow.total_load / maxLoad * 100) + '%' }" /></div>
            <span class="bendera-count">{{ mrow.total_load.toFixed(2) }}</span>
            <span class="load-proj">{{ mrow.projects }} proyek</span>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title"><span class="dot" />Matriks Mapping Proyek × Anggota</div>
        <div class="table-scroll">
          <table class="report matrix">
            <thead>
              <tr>
                <th class="sticky-col">Proyek</th>
                <th>PIC</th><th>Prog</th>
                <th v-for="mem in p.loadMapping.value.members" :key="mem">{{ mem }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in p.loadMapping.value.projects" :key="i">
                <td class="sticky-col wrap"><strong>{{ row.instansi }}</strong><br /><small class="muted">{{ row.nama }}</small></td>
                <td>{{ row.pic_utama }}</td>
                <td>{{ pct(row.progress) }}</td>
                <td v-for="mem in p.loadMapping.value.members" :key="mem" :class="{ 'cell-on': row.alloc[mem] }">
                  <span v-if="row.alloc[mem]">{{ Math.round(row.alloc[mem] * 100) }}%</span>
                  <span v-else class="muted">·</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- ============================================================= -->
    <!-- TAB: TARGET BULANAN                                            -->
    <!-- ============================================================= -->
    <template v-else-if="tab === 'target' && p.targets.value">
      <div class="panel">
        <div class="panel-title"><span class="dot" />Rekap Status Target per Bulan (2026)</div>
        <div class="table-scroll">
          <table class="report">
            <thead>
              <tr><th>Bulan</th><th>Total</th>
                <th v-for="(_c, s) in p.targets.value.by_status" :key="s">{{ s }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="mo in p.targets.value.months" :key="mo.month"
                  :class="{ 'row-active': mo.month === targetMonth }" @click="targetMonth = mo.month" style="cursor:pointer">
                <td><strong>{{ mo.month }}</strong></td>
                <td>{{ mo.total }}</td>
                <td v-for="(_c, s) in p.targets.value.by_status" :key="s">
                  <span v-if="mo.by_status[s]" class="badge" :class="stMeta(String(s)).cls">{{ mo.by_status[s] }}</span>
                  <span v-else class="muted">–</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel" v-if="currentMonth">
        <div class="row-between report-head">
          <div class="report-title"><h2>Detail Target — {{ currentMonth.month }}</h2>
            <span class="period-pill">{{ currentMonth.total }} item</span>
          </div>
          <div class="field" style="min-width:160px">
            <select v-model="targetMonth">
              <option v-for="mo in p.targets.value.months" :key="mo.month" :value="mo.month">{{ mo.month }}</option>
            </select>
          </div>
        </div>
        <div class="table-scroll">
          <table class="report">
            <thead><tr><th>Grup</th><th>Instansi</th><th>Target / Kegiatan</th><th>Status</th><th>Keterangan</th></tr></thead>
            <tbody>
              <tr v-for="(it, i) in currentMonth.items" :key="i">
                <td class="muted">{{ it.group }}</td>
                <td>{{ it.instansi }}</td>
                <td class="wrap">{{ it.kegiatan || it.target || "–" }}</td>
                <td><span class="badge" :class="stMeta(it.status).cls">{{ stMeta(it.status).icon }} {{ it.status }}</span></td>
                <td class="wrap muted">{{ it.keterangan || "–" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- ============================================================= -->
    <!-- TAB: TW PER DIVISI                                             -->
    <!-- ============================================================= -->
    <template v-else-if="tab === 'tw' && p.tw.value">
      <div v-for="d in p.tw.value.divisions" :key="d.division" class="panel">
        <div class="row-between report-head">
          <div class="report-title"><h2>{{ d.division }}</h2>
            <span class="period-pill">{{ d.total }} kegiatan · {{ d.done }} selesai</span>
          </div>
          <div class="pill-wrap">
            <span v-for="[s, c] in statusEntries(d.by_status)" :key="s" class="badge" :class="stMeta(s).cls">
              {{ stMeta(s).icon }} {{ s }} · {{ c }}
            </span>
          </div>
        </div>
        <div class="table-scroll">
          <table class="report">
            <thead>
              <tr><th>Grup</th><th>Instansi / Kegiatan</th><th v-if="d.items.some(x => x.pic)">PIC</th><th>Status</th><th>Progress</th><th>Keterangan</th></tr>
            </thead>
            <tbody>
              <tr v-for="(it, i) in d.items" :key="i">
                <td class="muted">{{ it.group }}</td>
                <td class="wrap"><strong v-if="it.instansi">{{ it.instansi }}</strong><span v-if="it.instansi && it.kegiatan"> — </span>{{ it.kegiatan }}</td>
                <td v-if="d.items.some(x => x.pic)">{{ it.pic || "–" }}</td>
                <td><span class="badge" :class="stMeta(it.status).cls">{{ stMeta(it.status).icon }} {{ it.status }}</span></td>
                <td>
                  <template v-if="it.progress !== null">
                    <div class="mini-bar"><span :class="it.progress >= 0.999 ? 'ach-good' : 'ach-mid'" :style="{ width: (it.progress * 100) + '%' }" /></div>
                    <small>{{ pct(it.progress) }}</small>
                  </template>
                  <span v-else class="muted">–</span>
                </td>
                <td class="wrap muted">{{ it.keterangan || "–" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
          </template>
        </div>
        <aside class="page-rail">
          <InfoRail page="project" />
        </aside>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 1rem; }
.pg-title { margin: 0; font-size: 1.4rem; }
.pg-sub { margin: .25rem 0 0; color: #64748b; font-size: .85rem; }
.btn-primary { background: linear-gradient(135deg, #1e3a8a, #2563eb); color: #fff; border: 0; padding: .6rem 1rem; border-radius: 10px; font-weight: 600; cursor: pointer; white-space: nowrap; }
.btn-primary:disabled { opacity: .5; cursor: default; }
.btn-ghost { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: .5rem .8rem; cursor: pointer; }
.btn-ghost:disabled { opacity: .5; cursor: default; }
.metric-num.sm { font-size: 1.25rem; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 900px) { .grid-2 { grid-template-columns: 1fr; } }

.tw-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
.tw-card { border: 1px solid var(--border, rgba(48, 66, 100, 0.55)); border-radius: 14px; padding: 1rem; background: var(--panel, #161b22); box-shadow: var(--shadow-sm); color: var(--text, #f1f5f9); }
.tw-head { display: flex; justify-content: space-between; align-items: center; }
.tw-head strong { font-size: 1.05rem; color: var(--text, #f1f5f9); }
.tw-count { font-size: .78rem; color: var(--text-sub, #cbd5e1); }
.tw-stats { display: flex; gap: .4rem; margin: .5rem 0; flex-wrap: wrap; }
.chip { font-size: .75rem; padding: .15rem .5rem; border-radius: 999px; font-weight: 600; }
.bar-row { margin: .5rem 0; }
.bar-label { display: flex; justify-content: space-between; font-size: .75rem; color: var(--text-sub, #cbd5e1); margin-bottom: .2rem; }
.bar { height: 8px; background: var(--bg-3, #1c2333); border-radius: 999px; overflow: hidden; }
.bar span { display: block; height: 100%; border-radius: 999px; }
.mini-bar { height: 6px; width: 70px; background: var(--bg-3, #1c2333); border-radius: 999px; overflow: hidden; display: inline-block; vertical-align: middle; margin-right: .35rem; }
.mini-bar span { display: block; height: 100%; }
.ach-good { background: linear-gradient(90deg, #16a34a, #22c55e); }
.ach-mid { background: linear-gradient(90deg, #d97706, #f59e0b); }
.ach-low { background: linear-gradient(90deg, #dc2626, #ef4444); }
.tw-money { display: flex; gap: 1rem; margin: .6rem 0; }
.tw-money div { display: flex; flex-direction: column; }
.tw-money small { color: var(--text-dim, #94a3b8); font-size: .68rem; text-transform: uppercase; font-weight: 700; }
.tw-money b { font-size: .9rem; color: var(--text, #f1f5f9); }
.tw-eval { font-size: .8rem; color: var(--text-sub, #cbd5e1); background: var(--bg-2, #161b22); border-left: 3px solid var(--cyan, #38bdf8); padding: .5rem .6rem; border-radius: 0 8px 8px 0; margin: .4rem 0 0; line-height: 1.4; }

.pill-wrap { display: flex; flex-wrap: wrap; gap: .4rem; }
.pill-wrap.mt, .mt { margin-top: .75rem; }
.badge.s-Done { background: rgba(34, 197, 94, 0.15); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.3); }
.badge.s-Progress { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
.badge.s-Upcoming { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
.badge.s-Maintenance { background: rgba(248, 113, 113, 0.15); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.3); }
.badge.s-None { background: rgba(100, 116, 139, 0.15); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.3); }
.chip.s-Done { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.chip.s-Progress { background: rgba(56, 189, 248, 0.15); color: #38bdf8; }
.chip.s-Maintenance { background: rgba(248, 113, 113, 0.15); color: #f87171; }

.bendera-list { display: flex; flex-direction: column; gap: .55rem; }
.bendera-row { display: grid; grid-template-columns: 120px 1fr 32px; align-items: center; gap: .6rem; }
.bendera-name { font-size: .8rem; color: var(--text-sub, #cbd5e1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bendera-count { font-size: .8rem; font-weight: 700; text-align: right; color: var(--text, #f1f5f9); }

.alert-h { margin: .3rem 0 .5rem; font-size: 1rem; }
.alert-h.red { color: #f87171; }
.alert-h.amber { color: #f59e0b; }
.dot.red { background: #ef4444; }
.field-btn { display: flex; flex-direction: column; justify-content: flex-end; }
td.wrap { max-width: 280px; white-space: normal; }
.head-actions { display: flex; gap: .5rem; }

/* Tabs */
.tabbar { display: flex; gap: .3rem; border-bottom: 2px solid var(--border, rgba(48, 66, 100, 0.55)); margin-bottom: 1rem; flex-wrap: wrap; }
.tab { background: transparent; border: 0; padding: .6rem .9rem; cursor: pointer; font-weight: 600; color: var(--text-sub, #cbd5e1); border-bottom: 3px solid transparent; margin-bottom: -2px; border-radius: 8px 8px 0 0; }
.tab:hover { background: var(--bg-3, #1c2333); color: var(--text, #f1f5f9); }
.tab.active { color: var(--cyan, #38bdf8); border-bottom-color: var(--cyan, #38bdf8); }

/* Load mapping */
.bendera-row.load { grid-template-columns: 150px 1fr 52px 90px; }
.load-proj { font-size: .85rem; color: var(--text-dim, #94a3b8); text-align: right; font-weight: 500; }
.matrix th, .matrix td { font-size: 1rem; text-align: center; padding: .55rem .6rem; line-height: 1.5; }
.matrix th:first-child, .matrix td:first-child { text-align: left; }
.matrix .cell-on { background: rgba(56, 189, 248, 0.15); font-weight: 600; color: #38bdf8; }
.sticky-col { position: sticky; left: 0; background: var(--bg-2, #161b22); color: var(--text, #f1f5f9); z-index: 1; min-width: 220px; max-width: 280px; }
.matrix thead .sticky-col { z-index: 2; }
.row-active { background: rgba(56, 189, 248, 0.08); }
</style>
