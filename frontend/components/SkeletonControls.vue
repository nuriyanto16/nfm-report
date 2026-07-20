<script setup lang="ts">
defineProps<{ fields?: number }>();
</script>

<template>
  <div class="panel">
    <div class="controls">
      <div class="skel-field" v-for="n in (fields || 4)" :key="n">
        <div class="skel" style="height: 11px; width: 80px; margin-bottom: 7px" />
        <div class="skel" style="height: 38px; width: 160px; border-radius: 8px" />
      </div>
    </div>
  </div>
</template>
