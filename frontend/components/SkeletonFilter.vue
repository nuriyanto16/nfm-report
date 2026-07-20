<script setup lang="ts">
defineProps<{ groups?: number }>();
</script>

<template>
  <div class="panel">
    <div class="row-between filter-head">
      <div class="skel" style="height: 16px; width: 150px" />
      <div class="skel" style="height: 32px; width: 100px; border-radius: 8px" />
    </div>
    <div class="filter-grid">
      <div class="filter-group" v-for="g in (groups || 6)" :key="g">
        <div class="skel" style="height: 12px; width: 90px; margin-bottom: 11px" />
        <div class="chips">
          <div class="skel" v-for="n in 4" :key="n"
               :style="{ height: '24px', width: (40 + (n * 17) % 50) + 'px', borderRadius: '999px' }" />
        </div>
      </div>
    </div>
  </div>
</template>
