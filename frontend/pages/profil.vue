<script setup lang="ts">
import { ref } from "vue";

const { username, role, token } = useAuth();
const oldPass = ref("");
const newPass = ref("");
const confirmPass = ref("");
const loading = ref(false);
const error = ref("");
const ok = ref("");

async function submit() {
  error.value = "";
  ok.value = "";
  if (!oldPass.value || !newPass.value) {
    error.value = "Password lama & baru wajib diisi.";
    return;
  }
  if (newPass.value !== confirmPass.value) {
    error.value = "Konfirmasi password tidak cocok.";
    return;
  }
  loading.value = true;
  try {
    const res = await apiSend<{ token: string }>("/api/me/password", "POST", {
      old_password: oldPass.value,
      new_password: newPass.value,
    });
    // ver di-bump di server -> token lama invalid; pakai token baru.
    if (res?.token) token.value = res.token;
    oldPass.value = newPass.value = confirmPass.value = "";
    ok.value = "Password berhasil diganti.";
  } catch (e: any) {
    error.value = e?.message || "Gagal mengganti password.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page-grid">
    <div class="page-body">
      <div class="profile-wrap">
        <div class="panel">
          <div class="report-title" style="margin-bottom:16px">
            <h2>Profil Saya</h2>
          </div>
          <div class="profile-id">
            <div class="sb-avatar lg">{{ (username || "A").charAt(0).toUpperCase() }}</div>
            <div>
              <div class="pi-name">{{ username }}</div>
              <div class="pi-role">{{ role }}</div>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-title"><span class="dot" />Ganti Password</div>
          <form class="pw-form" @submit.prevent="submit">
            <label class="field full">
              <span>Password Lama</span>
              <input v-model="oldPass" type="password" autocomplete="current-password" />
            </label>
            <label class="field full">
              <span>Password Baru</span>
              <input v-model="newPass" type="password" autocomplete="new-password" />
            </label>
            <label class="field full">
              <span>Konfirmasi Password Baru</span>
              <input v-model="confirmPass" type="password" autocomplete="new-password" />
            </label>
            <p v-if="error" class="error">{{ error }}</p>
            <p v-if="ok" class="notice">{{ ok }}</p>
            <button class="btn btn-run" type="submit" :disabled="loading">
              {{ loading ? "Menyimpan…" : "Simpan Password" }}
            </button>
          </form>
        </div>
      </div>
    </div>

    <aside class="page-rail">
      <InfoRail page="profil" />
    </aside>
  </div>
</template>
