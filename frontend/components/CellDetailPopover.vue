<script setup lang="ts">
// Panel detail (modal, di-tengah layar) yang muncul saat angka pada tabel
// Monitoring per PIC diklik, menampilkan Bulan (sheet), No issue, Request By
// & tanggal lengkap (Request/Mulai/Estimasi/Selesai) supaya mudah menyisir
// mana saja yang Hold, Back Log, To Do, dst tanpa buka laporan lain.
import { onMounted, onBeforeUnmount } from "vue";

interface Row {
  no: number | null;
  issue: string;
  source_month: string;
  request_by: string | null;
  tgl_request: string | null;
  tgl_mulai: string | null;
  tgl_estimasi: string | null;
  tgl_selesai: string | null;
}

defineProps<{
  title: string;
  rows: Row[];
}>();
const emit = defineEmits<{ (e: "close"): void }>();

function onKey(e: KeyboardEvent) {
  if (e.key === "Escape") emit("close");
}
onMounted(() => document.addEventListener("keydown", onKey));
onBeforeUnmount(() => document.removeEventListener("keydown", onKey));

const MONTH_ID = [
  "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
  "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
];

// Format tanggal+jam ISO -> "10 Jul 2026 14.30"; jam disertakan hanya bila
// datanya punya komponen waktu (bukan 00.00). Kosong/null -> "-".
function fmt(iso: string | null): string {
  if (!iso) return "-";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "-";
  const day = `${d.getDate()} ${MONTH_ID[d.getMonth()]} ${d.getFullYear()}`;
  if (d.getHours() || d.getMinutes()) {
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    return `${day} ${hh}.${mm}`;
  }
  return day;
}
</script>

<template>
  <div class="cdp-overlay" @click="emit('close')">
    <div class="cdp-panel" @click.stop>
      <div class="cdp-head">
        <strong>{{ title }}</strong>
        <button class="cdp-close" @click="emit('close')">✕</button>
      </div>
      <div class="cdp-body">
        <div v-if="!rows.length" class="cdp-empty">Tidak ada data.</div>
        <div v-for="(row, i) in rows" :key="i" class="cdp-row">
          <div class="cdp-row-head">
            <span class="cdp-no">#{{ row.no ?? '-' }}</span>
            <span class="cdp-issue">{{ row.issue }}</span>
          </div>
          <div class="cdp-row-meta">
            <span>👤 {{ row.request_by || '-' }}</span>
            <span>📄 Sheet: {{ row.source_month || '-' }}</span>
          </div>
          <div class="cdp-row-dates">
            <span><em>Req</em> {{ fmt(row.tgl_request) }}</span>
            <span><em>Mulai</em> {{ fmt(row.tgl_mulai) }}</span>
            <span><em>Estimasi</em> {{ fmt(row.tgl_estimasi) }}</span>
            <span><em>Selesai</em> {{ fmt(row.tgl_selesai) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cdp-overlay {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.cdp-panel {
  position: relative; z-index: 201; width: min(720px, 100%);
  max-height: min(680px, 85vh);
  display: flex; flex-direction: column;
  overflow: hidden;
  background: #1e293b;
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6);
  color: #f1f5f9;
}
.cdp-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(56, 189, 248, 0.2);
  font-size: 16px; flex-shrink: 0;
  background: #0f172a;
  color: #f1f5f9;
}
.cdp-close {
  border: 1px solid rgba(56, 189, 248, 0.3);
  background: #1e293b;
  cursor: pointer; font-size: 14px;
  color: #cbd5e1; line-height: 1; padding: 6px 12px;
  border-radius: 6px;
  transition: all .15s ease;
}
.cdp-close:hover { color: #38bdf8; border-color: #38bdf8; background: rgba(56, 189, 248, 0.15); }
.cdp-body { padding: 8px 0; overflow-y: auto; background: #1e293b; }
.cdp-empty { padding: 20px; color: #cbd5e1; font-size: 14px; }
.cdp-row {
  padding: 14px 20px; border-bottom: 1px solid rgba(56, 189, 248, 0.12);
}
.cdp-row:last-child { border-bottom: none; }
.cdp-row:hover { background: rgba(56, 189, 248, 0.06); }
.cdp-row-head {
  display: flex; align-items: baseline; gap: 8px; font-size: 14px;
}
.cdp-no { font-weight: 700; color: #38bdf8; flex-shrink: 0; }
.cdp-issue { color: #f8fafc; font-weight: 500; }
.cdp-row-meta {
  display: flex; flex-wrap: wrap; gap: 6px 16px; margin-top: 6px;
  font-size: 12px; color: #cbd5e1;
}
.cdp-row-dates {
  display: flex; flex-wrap: wrap; gap: 6px 16px; margin-top: 6px;
  font-size: 12px; color: #e2e8f0;
}
.cdp-row-dates em, .cdp-row-meta em { font-style: normal; }
.cdp-row-dates em {
  color: #94a3b8; margin-right: 3px;
}
</style>
