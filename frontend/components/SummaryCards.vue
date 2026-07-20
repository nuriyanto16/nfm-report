<script setup lang="ts">
import { computed } from "vue";

interface Daily {
  total: number; isu: number; solved: number; pr: number;
  pr_solved: number; carry_over: number;
  window_start?: string; window_end?: string;
}
const props = defineProps<{
  summary: { total: number; by_status: Record<string, number>; daily?: Daily };
}>();

// Ikon + kelas warna per status kanonik.
const STATUS_META: Record<string, { icon: string; cls: string }> = {
  Done: { icon: "✅", cls: "m-green" },
  Progress: { icon: "🔄", cls: "m-blue" },
  Hold: { icon: "⏸️", cls: "m-red" },
  "Back Log": { icon: "📋", cls: "m-slate" },
  "To Do": { icon: "📝", cls: "m-amber" },
  "Tanpa Status": { icon: "❔", cls: "m-slate" },
};
function meta(s: string) {
  return STATUS_META[s] || { icon: "▫️", cls: "m-slate" };
}

const daily = computed(() => props.summary.daily);
// Persentase solved (dari total Isu hari ini) untuk mini progress bar di
// kartu hero. Dulu dibagi `total` (jumlah baris periode harian), tapi itu
// bisa bikin persentase > 100%. Basisnya sekarang Isu.
const solvedPct = computed(() => {
  const d = daily.value;
  if (!d || !d.isu) return 0;
  return Math.round((d.solved / d.isu) * 100);
});
</script>

<template>
  <div class="cards" :class="{ 'cards-row': daily }">
    <!-- Kartu hero: Total -->
    <div class="metric metric-hero">
      <div class="metric-top">
        <div class="metric-ico">📊</div>
        <span v-if="daily" class="metric-tag">{{ solvedPct }}% selesai</span>
      </div>
      <div class="metric-num">{{ summary.total }}</div>
      <div class="metric-lbl">Total Task</div>
      <div v-if="daily" class="metric-bar">
        <span :style="{ width: solvedPct + '%' }" />
      </div>
    </div>

    <!-- Mode harian: kartu Isu / Solved / PR / PR Solved / Carry Over -->
    <template v-if="daily">
      <div class="metric m-blue">
        <div class="metric-top"><div class="metric-ico">🆕</div></div>
        <div class="metric-num">{{ daily.isu }}</div>
        <div class="metric-lbl">Isu</div>
      </div>
      <div class="metric m-green">
        <div class="metric-top"><div class="metric-ico">✅</div></div>
        <div class="metric-num">{{ daily.solved }}</div>
        <div class="metric-lbl">Solved</div>
      </div>
      <div class="metric m-amber">
        <div class="metric-top"><div class="metric-ico">📝</div></div>
        <div class="metric-num">{{ daily.pr }}</div>
        <div class="metric-lbl">PR</div>
      </div>
      <div class="metric m-slate" v-if="daily.pr_solved > 0">
        <div class="metric-top"><div class="metric-ico">✔️</div></div>
        <div class="metric-num">{{ daily.pr_solved }}</div>
        <div class="metric-lbl">PR Solved</div>
      </div>
      <div class="metric m-purple" v-if="daily.carry_over > 0">
        <div class="metric-top"><div class="metric-ico">⏳</div></div>
        <div class="metric-num">{{ daily.carry_over }}</div>
        <div class="metric-lbl">Carry Over <span class="metric-sub">of PR</span></div>
      </div>
    </template>

    <!-- Mode lain: rincian per status -->
    <template v-else>
      <div
        class="metric" :class="meta(status).cls"
        v-for="(count, status) in summary.by_status" :key="status"
      >
        <div class="metric-top"><div class="metric-ico">{{ meta(status).icon }}</div></div>
        <div class="metric-num">{{ count }}</div>
        <div class="metric-lbl">{{ status }}</div>
      </div>
    </template>
  </div>
</template>
