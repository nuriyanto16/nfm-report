<script setup lang="ts">
import { onMounted, watch } from "vue";
import { useEvaluasi } from "~/composables/useEvaluasi";

const e = useEvaluasi();

onMounted(() => e.init());

// Ganti PIC -> muat ulang dokumen.
watch(e.selected, () => { if (!e.initializing.value) e.loadContent(); });

function openInNewTab() {
  if (!e.html.value) return;
  const blob = new Blob([e.html.value], { type: "text/html" });
  window.open(URL.createObjectURL(blob), "_blank");
}
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h2 class="pg-title">📝 Evaluasi Triwulan</h2>
        <p class="pg-sub">Reviu triwulan berjalan &amp; rencana triwulan berikutnya, per PIC.</p>
      </div>
    </div>

    <div v-if="e.error.value" class="error">{{ e.error.value }}</div>

    <div class="page-grid">
      <div class="page-body">
        <div class="panel">
          <div class="controls">
            <div class="field">
              <label>👤 PIC</label>
              <select v-model="e.selected.value" :disabled="e.initializing.value">
                <option v-for="it in e.items.value" :key="it.pic" :value="it.pic">{{ it.pic }}</option>
              </select>
            </div>
            <div class="field field-btn">
              <label>&nbsp;</label>
              <button class="btn-ghost" :disabled="!e.html.value" @click="openInNewTab">↗️ Buka di tab baru</button>
            </div>
            <div v-if="e.title.value" class="doc-title">{{ e.title.value }}</div>
          </div>
        </div>

        <div class="panel">
          <div v-if="e.initializing.value || e.loading.value" class="doc-loading">Memuat dokumen…</div>
          <div v-else-if="!e.items.value.length" class="empty-state">
            <div class="empty-ico">📭</div>
            <p>Belum ada dokumen evaluasi. Tambahkan file <code>*_Tim_&lt;PIC&gt;.html</code> di folder LAPORAN.</p>
          </div>
          <iframe
            v-else
            class="doc-frame"
            :srcdoc="e.html.value"
            title="Dokumen Evaluasi Triwulan"
            sandbox="allow-same-origin allow-popups"
          />
        </div>
      </div>

      <aside class="page-rail">
        <InfoRail page="evaluasi" />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.page-head { margin-bottom: 1rem; }
.pg-title { margin: 0; font-size: 1.4rem; }
.pg-sub { margin: .25rem 0 0; color: #64748b; font-size: .85rem; }
.btn-ghost { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: .5rem .8rem; cursor: pointer; }
.btn-ghost:disabled { opacity: .5; cursor: default; }
.field-btn { display: flex; flex-direction: column; justify-content: flex-end; }
.doc-title { align-self: flex-end; color: #334155; font-weight: 600; font-size: .85rem; margin-left: auto; max-width: 45ch; }
.doc-loading { padding: 2rem; text-align: center; color: #64748b; }
.doc-frame { width: 100%; height: calc(100vh - 230px); min-height: 520px; border: 1px solid #e2e8f0; border-radius: 12px; background: #fff; }
</style>
