<script setup lang="ts">
import { ref } from "vue";

definePageMeta({ layout: false });

const { login } = useAuth();
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
      <div class="login2-orbs"><span /><span /><span /></div>
      <div class="login2-brand">
        <div class="login2-logo">📊</div>
        <h1>FAST REPORT</h1>
        <p class="login2-tag">Penarikan Laporan dari Berbagai Sumber Data</p>
        <ul class="login2-feats">
          <li>🔌 Tarik data dari banyak sumber (multi-source)</li>
          <li>📅 Laporan harian, mingguan & bulanan</li>
          <li>🎯 Filter dinamis berdasarkan status & PIC</li>
          <li>📥 Ekspor ke Excel, Word, dan PDF</li>
        </ul>
      </div>
      <div class="login2-instansi">FAST REPORT · Multi-Source Reporting Tool</div>
    </section>

    <!-- Panel form kanan -->
    <section class="login2-right">
      <div class="login2-card">
        <div class="login2-card-head">
          <div class="login2-logo sm">📊</div>
          <h2>Selamat Datang 👋</h2>
          <p>Silakan masuk untuk mengakses dashboard laporan.</p>
        </div>

        <form class="login-form" @submit.prevent="onSubmit">
          <label class="login-field">
            <span>Username</span>
            <div class="login-input">
              <span class="login-icon">👤</span>
              <input v-model="username" type="text" placeholder="Masukkan username" autocomplete="username" />
            </div>
          </label>

          <label class="login-field">
            <span>Password</span>
            <div class="login-input">
              <span class="login-icon">🔒</span>
              <input
                v-model="password"
                :type="showPass ? 'text' : 'password'"
                placeholder="Masukkan password"
                autocomplete="current-password"
              />
              <button type="button" class="login-eye" @click="showPass = !showPass">
                {{ showPass ? "🙈" : "👁" }}
              </button>
            </div>
          </label>

          <p v-if="error" class="login-error">{{ error }}</p>

          <button class="login-btn" type="submit" :disabled="loading">
            <span v-if="loading">Memproses…</span>
            <span v-else>Masuk →</span>
          </button>
        </form>

        <p class="login2-foot">© 2026 FAST REPORT</p>
      </div>
    </section>
  </div>
</template>
