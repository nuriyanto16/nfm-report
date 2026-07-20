<script setup lang="ts">
import { onMounted, ref } from "vue";

interface DataSource {
  id: string;
  name: string;
  type: string;
  link: string;
}

const sources = ref<DataSource[]>([]);
const loading = ref(true);
const error = ref("");

const TYPE_LABEL: Record<string, string> = {
  google_sheet: "Google Sheet",
};

onMounted(async () => {
  try {
    const res = await apiGet<{ sources: DataSource[] }>("/api/data-sources");
    sources.value = res.sources;
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || "Gagal memuat sumber data";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page-grid">
    <div class="page-body">
      <div class="panel">
        <div class="report-title" style="margin-bottom: 16px">
          <h2>Sumber Data</h2>
          <span class="period-pill">Daftar sumber laporan</span>
        </div>

        <div v-if="error" class="error">{{ error }}</div>
        <SkeletonReport v-else-if="loading" />

        <div v-else class="table-scroll">
          <table class="report">
            <thead>
              <tr><th style="width:48px">#</th><th>Nama Sumber</th><th>Jenis</th><th>Link Sumber</th></tr>
            </thead>
            <tbody>
              <tr v-for="(s, i) in sources" :key="s.id">
                <td>{{ i + 1 }}</td>
                <td><strong>{{ s.name }}</strong></td>
                <td><span class="badge s-ToDo">{{ TYPE_LABEL[s.type] || s.type }}</span></td>
                <td>
                  <a v-if="s.link" :href="s.link" target="_blank" rel="noopener" class="src-link">
                    🔗 Buka Sheet
                  </a>
                  <span v-else class="muted">—</span>
                </td>
              </tr>
              <tr v-if="!sources.length">
                <td colspan="4" class="muted" style="text-align:center;padding:24px">Belum ada sumber data.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <aside class="page-rail">
      <InfoRail page="sumber" />
    </aside>
  </div>
</template>
