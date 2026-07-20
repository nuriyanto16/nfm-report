<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  dims: readonly string[];
  values: Record<string, string[]>;
  selected: Record<string, string[]>;
}>();
const emit = defineEmits<{ (e: "toggle", dim: string, value: string): void; (e: "reset"): void }>();

const LABELS: Record<string, string> = {
  status: "⚡ Status",
  aplikasi: "📱 Aplikasi",
  pic: "👤 PIC",
  kategori: "🏷️ Kategori",
  priority: "🔥 Priority",
  status_deploy: "🌐 Status Deploy",
};

function isOn(dim: string, v: string) {
  return props.selected[dim]?.includes(v);
}

const totalSelected = computed(() =>
  props.dims.reduce((n, d) => n + (props.selected[d]?.length || 0), 0)
);
</script>

<template>
  <div class="panel filter-panel">
    <div class="row-between filter-head">
      <h2>
        ⚙️ Filter Dinamis Laporan
        <span v-if="totalSelected" class="filter-count">{{ totalSelected }} aktif</span>
      </h2>
      <button class="btn secondary" :disabled="!totalSelected" @click="emit('reset')">
        ↺ Reset Filter
      </button>
    </div>

    <div class="filter-grid">
      <div class="filter-group" v-for="dim in dims" :key="dim">
        <div class="filter-group-label">
          <span>{{ LABELS[dim] || dim }}</span>
          <span v-if="selected[dim]?.length" class="filter-badge">{{ selected[dim].length }}</span>
        </div>
        <div class="chips">
          <span v-if="!(values[dim] && values[dim].length)" class="muted">— tidak ada data —</span>
          <span
            v-for="v in values[dim]"
            :key="v"
            class="chip"
            :class="{ on: isOn(dim, v) }"
            @click="emit('toggle', dim, v)"
          >{{ v }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
