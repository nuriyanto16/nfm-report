<script setup lang="ts">
import { computed, ref } from "vue";
const route = useRoute();
const { username, role, isLoggedIn, hasMenu, logout } = useAuth();
const showChrome = computed(() => route.path !== "/login");
const collapsed = ref(false);

// Menu dikelompokkan; tiap item difilter berdasarkan hak akses (menu key).
const groups = [
  {
    section: "DASHBOARD",
    items: [
      { to: "/", label: "Dashboard Executive", iconName: "dashboard", key: "dashboard" },
    ],
  },
  {
    section: "LAPORAN",
    items: [
      { to: "/harian", label: "Laporan Harian", iconName: "harian", key: "harian" },
      { to: "/mingguan", label: "Laporan Mingguan", iconName: "mingguan", key: "mingguan" },
      { to: "/bulanan", label: "Laporan Bulanan", iconName: "bulanan", key: "bulanan" },
    ],
  },
  {
    section: "ANALITIK",
    items: [
      { to: "/monitoring", label: "Monitoring Progress", iconName: "monitoring", key: "monitoring" },
      { to: "/project", label: "Project Management", iconName: "project_mgmt", key: "project_mgmt" },
      { to: "/evaluasi", label: "Evaluasi Triwulan", iconName: "evaluasi_tw", key: "evaluasi_tw" },
    ],
  },
  {
    section: "DATA",
    items: [
      { to: "/sumber", label: "Sumber Data", iconName: "sources", key: "sources" },
    ],
  },
  {
    section: "ADMINISTRASI",
    items: [
      { to: "/users", label: "Manajemen User", iconName: "users", key: "users" },
    ],
  },
];

const visibleGroups = computed(() =>
  groups
    .map((g) => ({ ...g, items: g.items.filter((i) => hasMenu(i.key)) }))
    .filter((g) => g.items.length > 0),
);
</script>

<template>
  <div v-if="showChrome" class="layout" :class="{ collapsed }">
    <aside class="sidebar">
      <div class="sb-brand">
        <div class="sb-logo">
          <UiIcon name="logo" :size="24" color="#ffffff" />
        </div>
        <div class="sb-brand-text">
          <strong>FAST REPORT</strong>
          <span>Multi-Source Report</span>
        </div>
      </div>

      <nav class="sb-nav">
        <template v-for="g in visibleGroups" :key="g.section">
          <p class="sb-section">{{ g.section }}</p>
          <NuxtLink v-for="m in g.items" :key="m.to" :to="m.to" class="sb-link">
            <span class="sb-icon"><UiIcon :name="m.iconName" :size="18" /></span>
            <span class="sb-label">{{ m.label }}</span>
          </NuxtLink>
        </template>
      </nav>

      <div class="sb-foot">
        <NuxtLink to="/profil" class="sb-link sb-profile">
          <span class="sb-icon"><UiIcon name="profil" :size="18" /></span>
          <span class="sb-label">Profil &amp; Password</span>
        </NuxtLink>
        <div class="sb-user" v-if="isLoggedIn">
          <div class="sb-avatar">{{ (username || "A").charAt(0).toUpperCase() }}</div>
          <div class="sb-user-text">
            <strong>{{ username || "admin" }}</strong>
            <span>{{ role || "user" }}</span>
          </div>
        </div>
        <button class="sb-logout" @click="logout">
          <span class="sb-icon"><UiIcon name="logout" :size="18" /></span>
          <span class="sb-label">Keluar</span>
        </button>
      </div>
    </aside>

    <div class="main-area">
      <header class="topbar">
        <button class="collapse-btn" @click="collapsed = !collapsed" title="Sembunyikan menu">
          <UiIcon name="filter" :size="16" />
        </button>
        <h1 class="topbar-title">FAST REPORT — Penarikan Laporan</h1>
      </header>
      <main class="content">
        <NuxtPage />
      </main>
    </div>
  </div>

  <NuxtPage v-else />
</template>
