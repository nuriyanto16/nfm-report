<script setup lang="ts">
// Placeholder shimmer saat data laporan dimuat.
</script>

<template>
  <div>
    <div class="skel-cards" style="margin-bottom: 16px">
      <div class="skel skel-card" v-for="n in 6" :key="n" />
    </div>
    <div class="skel-table">
      <div class="skel skel-row head" />
      <div class="skel skel-row" v-for="n in 8" :key="n" :style="{ opacity: 1 - n * 0.07 }" />
    </div>
  </div>
</template>
