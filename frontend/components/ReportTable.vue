<script setup lang="ts">
import { ref } from "vue";
import type { ReportRow } from "~/composables/useReport";

defineProps<{ rows: ReportRow[] }>();

function parseDt(dt: string | null) {
  if (!dt) return null;
  const tgl = dt.slice(0, 10).split("-").reverse().join("/");
  const jam = dt.slice(11, 16);
  return { tgl, jam: jam && jam !== "00:00" ? jam : "" };
}

function badge(status: string) {
  return "badge s-" + (status || "default").replace(/\s/g, "");
}

function prioBadge(prio: string | null) {
  if (!prio) return "prio-normal";
  const p = prio.toLowerCase();
  if (p.includes("high") || p.includes("tinggi")) return "prio-high";
  if (p.includes("mid") || p.includes("sedang")) return "prio-mid";
  if (p.includes("low") || p.includes("rendah")) return "prio-low";
  return "prio-normal";
}

// Popup untuk melihat isi kolom panjang (Issue / Keterangan) secara penuh.
const popup = ref<{ title: string; text: string } | null>(null);
function openCell(title: string, text: string | null) {
  if (text && text.trim()) popup.value = { title, text };
}

// Ubah URL di dalam teks menjadi tautan yang bisa diklik pada popup.
const URL_RE = /(https?:\/\/[^\s]+)/g;
function parts(text: string) {
  return text.split(URL_RE).map((seg) => ({ seg, isUrl: URL_RE.test(seg) }));
}
</script>

<template>
  <div class="table-scroll">
    <table class="report">
      <thead>
        <tr>
          <th class="th-no">#</th>
          <th>📱 Aplikasi</th>
          <th>📋 Issue / Pekerjaan</th>
          <th>🏷️ Kategori</th>
          <th>📅 Tgl Request</th>
          <th>🚀 Tgl Mulai</th>
          <th>⏳ Tgl Estimasi Selesai</th>
          <th>✅ Tgl Selesai</th>
          <th>👤 PIC</th>
          <th>📩 Request By</th>
          <th>⚡ Status</th>
          <th>🔥 Priority</th>
          <th>🌐 Status Deploy</th>
          <th>💬 Keterangan</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in rows" :key="i">
          <td class="td-no">
            <span class="no-pill">{{ r.no ?? (i + 1) }}</span>
          </td>
          <td>
            <span class="app-chip">{{ r.aplikasi || '-' }}</span>
          </td>
          <td class="long-cell" @click="openCell('Issue #' + (r.no ?? '-'), r.issue)">
            <div class="clip">
              {{ r.issue }}
              <span class="zoom-hint" title="Klik untuk lihat detail">🔍</span>
            </div>
          </td>
          <td>
            <span v-if="r.kategori" class="cat-pill">{{ r.kategori }}</span>
            <span v-else class="muted">-</span>
          </td>

          <!-- Tgl Request -->
          <td>
            <div v-if="parseDt(r.tgl_request)" class="dt-cell">
              <span class="dt-tgl">{{ parseDt(r.tgl_request)!.tgl }}</span>
              <span v-if="parseDt(r.tgl_request)!.jam" class="dt-jam">{{ parseDt(r.tgl_request)!.jam }}</span>
            </div>
            <span v-else class="muted">-</span>
          </td>

          <!-- Tgl Mulai -->
          <td>
            <div v-if="parseDt(r.tgl_mulai)" class="dt-cell">
              <span class="dt-tgl">{{ parseDt(r.tgl_mulai)!.tgl }}</span>
              <span v-if="parseDt(r.tgl_mulai)!.jam" class="dt-jam">{{ parseDt(r.tgl_mulai)!.jam }}</span>
            </div>
            <span v-else class="muted">-</span>
          </td>

          <!-- Tgl Estimasi -->
          <td>
            <div v-if="parseDt(r.tgl_estimasi)" class="dt-cell">
              <span class="dt-tgl">{{ parseDt(r.tgl_estimasi)!.tgl }}</span>
              <span v-if="parseDt(r.tgl_estimasi)!.jam" class="dt-jam">{{ parseDt(r.tgl_estimasi)!.jam }}</span>
            </div>
            <span v-else class="muted">-</span>
          </td>

          <!-- Tgl Selesai -->
          <td>
            <div v-if="parseDt(r.tgl_selesai)" class="dt-cell done">
              <span class="dt-tgl">{{ parseDt(r.tgl_selesai)!.tgl }}</span>
              <span v-if="parseDt(r.tgl_selesai)!.jam" class="dt-jam">{{ parseDt(r.tgl_selesai)!.jam }}</span>
            </div>
            <span v-else class="muted">-</span>
          </td>

          <td>
            <div v-if="r.pic" class="user-pill">
              <span class="u-icon">👤</span>
              <span class="u-name">{{ r.pic }}</span>
            </div>
            <span v-else class="muted">-</span>
          </td>

          <td>
            <div v-if="r.request_by" class="user-pill req">
              <span class="u-icon">📩</span>
              <span class="u-name">{{ r.request_by }}</span>
            </div>
            <span v-else class="muted">-</span>
          </td>

          <td>
            <span :class="badge(r.status)">{{ r.status }}</span>
          </td>

          <td>
            <span class="prio-tag" :class="prioBadge(r.priority)">
              {{ r.priority || 'Normal' }}
            </span>
          </td>

          <td>
            <span v-if="r.status_deploy" class="deploy-pill">{{ r.status_deploy }}</span>
            <span v-else class="muted">-</span>
          </td>

          <td class="long-cell ket-cell" @click="openCell('Keterangan #' + (r.no ?? '-'), r.keterangan)">
            <div class="clip">
              {{ r.keterangan }}
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- Popup isi penuh kolom -->
  <div v-if="popup" class="modal-backdrop" @click.self="popup = null">
    <div class="modal">
      <h3>{{ popup.title }}</h3>
      <div class="cell-full">
        <template v-for="(p, idx) in parts(popup.text)" :key="idx">
          <a v-if="p.isUrl" :href="p.seg" target="_blank" rel="noopener">{{ p.seg }}</a>
          <span v-else>{{ p.seg }}</span>
        </template>
      </div>
      <div class="modal-foot">
        <button class="btn secondary" @click="popup = null">Tutup</button>
      </div>
    </div>
  </div>
</template>
