<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useTheme } from "~/composables/useTheme";

definePageMeta({ layout: false });

const { login } = useAuth();
const { theme, toggleTheme, initTheme } = useTheme();

onMounted(() => {
  initTheme();
});

const username = ref("");
const password = ref("");
const showPass = ref(false);
const loading = ref(false);
const error = ref("");

async function onSubmit() {
  if (!username.value || !password.value) {
    error.value = "Username dan password wajib diisi.";
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    await login(username.value, password.value);
    await navigateTo("/");
  } catch (e: any) {
    error.value = e?.data?.detail || "Login gagal. Periksa kembali kredensial Anda.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login2">
    <!-- Panel branding kiri -->
    <section class="login2-left">
      <div class="login2-orbs">
        <span />
        <span />
        <span />
      </div>

      <div class="login2-brand">
        <div class="brand-badge">
          <span class="badge-dot" />
          <span>PORTAL MONITORING &amp; LAPORAN EXECUTIVE</span>
        </div>

        <div class="brand-logo-wrap">
          <div class="login2-logo">
            <UiIcon name="logo" :size="34" color="#ffffff" />
          </div>
          <div class="logo-text">
            <h1>FAST REPORT</h1>
            <span class="logo-sub">Multi-Source Reporting Platform</span>
          </div>
        </div>

        <p class="login2-tag">
          Sistem rekapitulasi data terpadu, pemantauan progress pekerjaan, dan analisis performa tim secara real-time.
        </p>

        <div class="login2-feats-grid">
          <div class="feat-card">
            <div class="feat-ico"><UiIcon name="dashboard" :size="20" color="#38bdf8" /></div>
            <div class="feat-text">
              <strong>Executive Dashboard</strong>
              <span>Visualisasi KPI &amp; grafik analitik real-time</span>
            </div>
          </div>

          <div class="feat-card">
            <div class="feat-ico"><UiIcon name="harian" :size="20" color="#38bdf8" /></div>
            <div class="feat-text">
              <strong>Laporan Harian, Mingguan &amp; Bulanan</strong>
              <span>Rekapitulasi otomatis dari spreadsheet active</span>
            </div>
          </div>

          <div class="feat-card">
            <div class="feat-ico"><UiIcon name="filter" :size="20" color="#38bdf8" /></div>
            <div class="feat-text">
              <strong>Filter Dinamis Presisi</strong>
              <span>Penyaringan per status, PIC, aplikasi &amp; prioritas</span>
            </div>
          </div>

          <div class="feat-card">
            <div class="feat-ico"><UiIcon name="sources" :size="20" color="#38bdf8" /></div>
            <div class="feat-text">
              <strong>Ekspor Multi-Format</strong>
              <span>Siap unduh ke Excel, Word, PDF &amp; WhatsApp</span>
            </div>
          </div>
        </div>
      </div>

      <div class="login2-instansi">
        <span class="status-indicator">🟢 Server Active &amp; Live Sync</span>
        <span>FAST REPORT v1.1.0 · BBPPT 2026</span>
      </div>
    </section>

    <!-- Panel form kanan -->
    <section class="login2-right">
      <!-- Theme Switcher Top Right -->
      <div class="login-theme-bar">
        <button class="theme-toggle-btn" @click="toggleTheme" :title="theme === 'dark' ? 'Ganti ke Mode Terang' : 'Ganti ke Mode Gelap'">
          <UiIcon v-if="theme === 'dark'" name="sun" :size="16" color="#f59e0b" />
          <UiIcon v-else name="moon" :size="16" color="#0284c7" />
          <span class="theme-toggle-label">{{ theme === 'dark' ? 'Mode Terang' : 'Mode Gelap' }}</span>
        </button>
      </div>

      <div class="login2-card">
        <div class="login2-card-head">
          <div class="login2-logo sm">
            <UiIcon name="logo" :size="26" color="#ffffff" />
          </div>
          <h2>Selamat Datang 👋</h2>
          <p>Masuk dengan akun Anda untuk mengakses portal laporan.</p>
        </div>

        <form class="login-form" @submit.prevent="onSubmit">
          <label class="login-field">
            <span>Username</span>
            <div class="login-input">
              <span class="login-icon"><UiIcon name="users" :size="16" color="#38bdf8" /></span>
              <input v-model="username" type="text" placeholder="Masukkan username Anda" autocomplete="username" />
            </div>
          </label>

          <label class="login-field">
            <span>Password</span>
            <div class="login-input">
              <span class="login-icon"><UiIcon name="profil" :size="16" color="#38bdf8" /></span>
              <input
                v-model="password"
                :type="showPass ? 'text' : 'password'"
                placeholder="Masukkan password Anda"
                autocomplete="current-password"
              />
              <button type="button" class="login-eye" @click="showPass = !showPass">
                {{ showPass ? "🙈" : "👁" }}
              </button>
            </div>
          </label>

          <p v-if="error" class="login-error">{{ error }}</p>

          <button class="login-btn" type="submit" :disabled="loading">
            <span v-if="loading" class="btn-spinner">⏳ Memproses…</span>
            <span v-else class="btn-text">Masuk ke Portal <UiIcon name="check" :size="16" /></span>
          </button>
        </form>

        <div class="login2-foot">
          <span>Sistem Pelaporan Multi-Sumber · BBPPT 2026</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.login-theme-bar {
  position: absolute;
  top: 24px;
  right: 24px;
  z-index: 10;
}
.theme-toggle-btn {
  background: var(--cyan-glass, rgba(56, 189, 248, 0.12));
  border: 1px solid var(--border-soft, rgba(56, 189, 248, 0.3));
  color: var(--text);
  font-size: 12px;
  font-weight: 700;
  padding: 6px 14px;
  border-radius: 999px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all .2s ease;
}
.theme-toggle-btn:hover {
  background: var(--border-glow, rgba(56, 189, 248, 0.25));
  transform: translateY(-1px);
}
.login2-right {
  position: relative;
}
</style>
