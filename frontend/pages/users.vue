<script setup lang="ts">
import { onMounted, reactive, ref, computed } from "vue";
import { useUsers, type UserRow, type RoleRow } from "~/composables/useUsers";

const u = useUsers();
const tab = ref<"users" | "roles">("users");
const notice = ref("");
const noticeErr = ref(false);

function flash(msg: string, err = false) {
  notice.value = msg;
  noticeErr.value = err;
  setTimeout(() => (notice.value = ""), 3500);
}

onMounted(() => u.loadAll());

// ---------- Modal user ----------
const userModal = reactive({
  open: false, mode: "create" as "create" | "edit",
  username: "", full_name: "", description: "", role: "", active: true, password: "",
  saving: false, error: "",
});
function openCreateUser() {
  Object.assign(userModal, {
    open: true, mode: "create", username: "", full_name: "", description: "",
    role: u.roles.value[0]?.name || "", active: true, password: "", error: "",
  });
}
function openEditUser(row: UserRow) {
  Object.assign(userModal, {
    open: true, mode: "edit", username: row.username, full_name: row.full_name,
    description: row.description, role: row.role, active: row.active, password: "",
    error: "",
  });
}
async function saveUser() {
  userModal.saving = true;
  userModal.error = "";
  try {
    if (userModal.mode === "create") {
      await u.createUser({
        username: userModal.username, password: userModal.password,
        role: userModal.role, full_name: userModal.full_name,
        description: userModal.description, active: userModal.active,
      });
      flash("User dibuat.");
    } else {
      await u.updateUser(userModal.username, {
        role: userModal.role, full_name: userModal.full_name,
        description: userModal.description, active: userModal.active,
      });
      flash("User diperbarui.");
    }
    userModal.open = false;
    await u.loadAll();
  } catch (e: any) {
    userModal.error = e?.message || "Gagal menyimpan";
  } finally {
    userModal.saving = false;
  }
}
async function toggleActive(row: UserRow) {
  try {
    await u.updateUser(row.username, { active: !row.active });
    await u.loadAll();
  } catch (e: any) {
    flash(e?.message || "Gagal mengubah status", true);
  }
}
async function removeUser(row: UserRow) {
  if (!confirm(`Hapus user "${row.username}"?`)) return;
  try {
    await u.deleteUser(row.username);
    flash("User dihapus.");
    await u.loadAll();
  } catch (e: any) {
    flash(e?.message || "Gagal menghapus", true);
  }
}

// ---------- Modal reset password ----------
const pwModal = reactive({ open: false, username: "", password: "", saving: false, error: "" });
function openResetPw(row: UserRow) {
  Object.assign(pwModal, { open: true, username: row.username, password: "", error: "" });
}
async function saveResetPw() {
  if (!pwModal.password) { pwModal.error = "Password baru wajib diisi"; return; }
  pwModal.saving = true;
  pwModal.error = "";
  try {
    await u.resetPassword(pwModal.username, pwModal.password);
    pwModal.open = false;
    flash(`Password ${pwModal.username} direset.`);
  } catch (e: any) {
    pwModal.error = e?.message || "Gagal reset password";
  } finally {
    pwModal.saving = false;
  }
}

// ---------- Modal role ----------
const roleModal = reactive({
  open: false, mode: "create" as "create" | "edit",
  name: "", label: "", menus: [] as string[], saving: false, error: "",
});
function openCreateRole() {
  Object.assign(roleModal, { open: true, mode: "create", name: "", label: "", menus: [], error: "" });
}
function openEditRole(row: RoleRow) {
  Object.assign(roleModal, {
    open: true, mode: "edit", name: row.name, label: row.label,
    menus: [...row.menus], error: "",
  });
}
function toggleMenu(key: string) {
  const i = roleModal.menus.indexOf(key);
  if (i >= 0) roleModal.menus.splice(i, 1);
  else roleModal.menus.push(key);
}
async function saveRole() {
  roleModal.saving = true;
  roleModal.error = "";
  try {
    if (roleModal.mode === "create") {
      await u.createRole({ name: roleModal.name, label: roleModal.label, menus: roleModal.menus });
      flash("Role dibuat.");
    } else {
      await u.updateRole(roleModal.name, { label: roleModal.label, menus: roleModal.menus });
      flash("Role diperbarui.");
    }
    roleModal.open = false;
    await u.loadAll();
  } catch (e: any) {
    roleModal.error = e?.message || "Gagal menyimpan role";
  } finally {
    roleModal.saving = false;
  }
}
async function removeRole(row: RoleRow) {
  if (!confirm(`Hapus role "${row.name}"?`)) return;
  try {
    await u.deleteRole(row.name);
    flash("Role dihapus.");
    await u.loadAll();
  } catch (e: any) {
    flash(e?.message || "Gagal menghapus role", true);
  }
}

const menuLabel = (key: string) =>
  u.menus.value.find((m) => m.key === key)?.label || key;
const roleLabel = (name: string) =>
  u.roles.value.find((r) => r.name === name)?.label || name;
</script>

<template>
  <div class="page-grid">
    <div class="page-body">
      <div class="panel">
        <div class="row-between report-head">
        <div class="report-title">
          <h2>Manajemen User</h2>
          <span class="period-pill">Kelola akun &amp; hak akses</span>
        </div>
        <div class="tabs">
          <button class="tab" :class="{ on: tab === 'users' }" @click="tab = 'users'">👥 Users</button>
          <button class="tab" :class="{ on: tab === 'roles' }" @click="tab = 'roles'">🛡️ Roles</button>
        </div>
      </div>

      <div v-if="notice" class="notice" :class="{ err: noticeErr }">{{ notice }}</div>
      <div v-if="u.error.value" class="error">{{ u.error.value }}</div>

      <!-- ============ TAB USERS ============ -->
      <template v-if="tab === 'users'">
        <div class="toolbar">
          <button class="btn btn-run" @click="openCreateUser">＋ Tambah User</button>
        </div>
        <div class="table-scroll">
          <table class="report">
            <thead>
              <tr><th>Username</th><th>Nama Lengkap</th><th>Role</th><th>Status</th><th>Keterangan</th><th>Aksi</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in u.users.value" :key="row.username">
                <td><strong>{{ row.username }}</strong></td>
                <td>{{ row.full_name || "—" }}</td>
                <td><span class="badge s-ToDo">{{ roleLabel(row.role) }}</span></td>
                <td>
                  <button class="switch" :class="{ on: row.active }" @click="toggleActive(row)"
                    :title="row.active ? 'Aktif — klik untuk nonaktifkan' : 'Nonaktif — klik untuk aktifkan'">
                    <span class="knob" />
                  </button>
                </td>
                <td class="ket-cell">{{ row.description || "—" }}</td>
                <td class="act">
                  <button class="mini" @click="openEditUser(row)" title="Edit">✏️</button>
                  <button class="mini" @click="openResetPw(row)" title="Reset password">🔑</button>
                  <button class="mini danger" @click="removeUser(row)" title="Hapus">🗑️</button>
                </td>
              </tr>
              <tr v-if="!u.users.value.length"><td colspan="6" class="muted" style="text-align:center;padding:24px">Belum ada user.</td></tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- ============ TAB ROLES ============ -->
      <template v-else>
        <div class="toolbar">
          <button class="btn btn-run" @click="openCreateRole">＋ Tambah Role</button>
        </div>
        <div class="table-scroll">
          <table class="report">
            <thead>
              <tr><th>Nama Role</th><th>Label</th><th>Menu Diizinkan</th><th>Aksi</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in u.roles.value" :key="row.name">
                <td><strong>{{ row.name }}</strong></td>
                <td>{{ row.label }}</td>
                <td>
                  <span v-if="!row.menus.length" class="muted">— tidak ada —</span>
                  <span v-for="k in row.menus" :key="k" class="chip on" style="margin:2px">{{ menuLabel(k) }}</span>
                </td>
                <td class="act">
                  <button class="mini" @click="openEditRole(row)" title="Edit">✏️</button>
                  <button class="mini danger" @click="removeRole(row)" title="Hapus">🗑️</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
      </div>
    </div>

    <aside class="page-rail">
      <InfoRail page="users" />
    </aside>
  </div>

  <!-- ============ MODAL USER ============ -->
    <div v-if="userModal.open" class="modal-backdrop" @click.self="userModal.open = false">
      <div class="modal">
        <h3>{{ userModal.mode === "create" ? "Tambah User" : `Edit ${userModal.username}` }}</h3>
        <div class="modal-grid">
          <label class="field">
            <span>Username</span>
            <input v-model="userModal.username" :disabled="userModal.mode === 'edit'" placeholder="mis. budi" />
          </label>
          <label class="field">
            <span>Nama Lengkap</span>
            <input v-model="userModal.full_name" placeholder="Budi Santoso" />
          </label>
          <label class="field" v-if="userModal.mode === 'create'">
            <span>Password</span>
            <input v-model="userModal.password" type="text" placeholder="Password awal" />
          </label>
          <label class="field">
            <span>Role</span>
            <select v-model="userModal.role">
              <option v-for="r in u.roles.value" :key="r.name" :value="r.name">{{ r.label }} ({{ r.name }})</option>
            </select>
          </label>
          <label class="field full">
            <span>Keterangan</span>
            <input v-model="userModal.description" placeholder="Opsional" />
          </label>
          <label class="check">
            <input type="checkbox" v-model="userModal.active" /> <span>Akun aktif</span>
          </label>
        </div>
        <p v-if="userModal.error" class="error">{{ userModal.error }}</p>
        <div class="modal-foot">
          <button class="btn secondary" @click="userModal.open = false">Batal</button>
          <button class="btn btn-run" :disabled="userModal.saving" @click="saveUser">
            {{ userModal.saving ? "Menyimpan…" : "Simpan" }}
          </button>
        </div>
      </div>
    </div>

    <!-- ============ MODAL RESET PASSWORD ============ -->
    <div v-if="pwModal.open" class="modal-backdrop" @click.self="pwModal.open = false">
      <div class="modal sm">
        <h3>Reset Password — {{ pwModal.username }}</h3>
        <label class="field full">
          <span>Password Baru</span>
          <input v-model="pwModal.password" type="text" placeholder="Password baru" />
        </label>
        <p v-if="pwModal.error" class="error">{{ pwModal.error }}</p>
        <div class="modal-foot">
          <button class="btn secondary" @click="pwModal.open = false">Batal</button>
          <button class="btn btn-run" :disabled="pwModal.saving" @click="saveResetPw">Simpan</button>
        </div>
      </div>
    </div>

    <!-- ============ MODAL ROLE ============ -->
    <div v-if="roleModal.open" class="modal-backdrop" @click.self="roleModal.open = false">
      <div class="modal">
        <h3>{{ roleModal.mode === "create" ? "Tambah Role" : `Edit Role ${roleModal.name}` }}</h3>
        <div class="modal-grid">
          <label class="field">
            <span>Nama (id)</span>
            <input v-model="roleModal.name" :disabled="roleModal.mode === 'edit'" placeholder="mis. operator" />
          </label>
          <label class="field">
            <span>Label</span>
            <input v-model="roleModal.label" placeholder="Operator" />
          </label>
        </div>
        <div class="menu-picker">
          <span class="picker-lbl">Menu yang diizinkan</span>
          <div class="chips">
            <button
              v-for="m in u.menus.value" :key="m.key" type="button"
              class="chip" :class="{ on: roleModal.menus.includes(m.key) }"
              @click="toggleMenu(m.key)"
            >{{ m.label }}</button>
          </div>
        </div>
        <p v-if="roleModal.error" class="error">{{ roleModal.error }}</p>
        <div class="modal-foot">
          <button class="btn secondary" @click="roleModal.open = false">Batal</button>
          <button class="btn btn-run" :disabled="roleModal.saving" @click="saveRole">
            {{ roleModal.saving ? "Menyimpan…" : "Simpan" }}
          </button>
        </div>
      </div>
    </div>
</template>
