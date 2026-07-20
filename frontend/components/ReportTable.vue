<script setup lang="ts">
import { ref } from "vue";
import type { ReportRow } from "~/composables/useReport";
defineProps<{ rows: ReportRow[] }>();

function fmt(dt: string | null): string {
  if (!dt) return "";
  const tgl = dt.slice(0, 10).split("-").reverse().join("/");
  const jam = dt.slice(11, 16);            // "HH:MM" dari ISO datetime
  return jam && jam !== "00:00" ? `${tgl} ${jam}` : tgl;
}
function badge(status: string) {
  return "badge s-" + status.replace(/\s/g, "");
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
          <th>No</th><th>Aplikasi</th><th>Issue</th><th>Kategori</th>
          <th>Tgl Request</th><th>Tgl Mulai</th><th>Tgl Estimasi Selesai</th><th>Tgl Selesai</th><th>PIC</th><th>Request By</th>
          <th>Status</th><th>Priority</th><th>Status Deploy</th><th>Keterangan</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in rows" :key="i">
          <td>{{ r.no }}</td>
          <td>{{ r.aplikasi }}</td>
          <td class="long-cell" @click="openCell('Issue #' + (r.no ?? '-'), r.issue)">
            <div class="clip">{{ r.issue }}</div>
          </td>
          <td>{{ r.kategori }}</td>
          <td>{{ fmt(r.tgl_request) }}</td>
          <td>{{ fmt(r.tgl_mulai) }}</td>
          <td>{{ fmt(r.tgl_estimasi) }}</td>
          <td>{{ fmt(r.tgl_selesai) }}</td>
          <td>{{ r.pic }}</td>
          <td>{{ r.request_by }}</td>
          <td><span :class="badge(r.status)">{{ r.status }}</span></td>
          <td>{{ r.priority }}</td>
          <td>{{ r.status_deploy }}</td>
          <td class="long-cell ket-cell" @click="openCell('Keterangan #' + (r.no ?? '-'), r.keterangan)">
            <div class="clip">{{ r.keterangan }}</div>
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
