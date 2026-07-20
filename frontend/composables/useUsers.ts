// CRUD user & role untuk halaman Manajemen User (butuh menu 'users').
import { ref } from "vue";

export interface UserRow {
  username: string;
  full_name: string;
  description: string;
  role: string;
  active: boolean;
  created_at?: string;
  updated_at?: string;
}
export interface RoleRow {
  name: string;
  label: string;
  menus: string[];
}
export interface MenuDef {
  key: string;
  label: string;
}

export function useUsers() {
  const users = ref<UserRow[]>([]);
  const roles = ref<RoleRow[]>([]);
  const menus = ref<MenuDef[]>([]);
  const loading = ref(false);
  const error = ref("");

  async function loadAll() {
    loading.value = true;
    error.value = "";
    try {
      const [u, r, m] = await Promise.all([
        apiGet<{ users: UserRow[] }>("/api/users"),
        apiGet<{ roles: RoleRow[] }>("/api/roles"),
        apiGet<{ menus: MenuDef[] }>("/api/menus"),
      ]);
      users.value = u.users;
      roles.value = r.roles;
      menus.value = m.menus;
    } catch (e: any) {
      error.value = e?.message || "Gagal memuat data";
    } finally {
      loading.value = false;
    }
  }

  // --- Users ---
  const createUser = (body: Record<string, any>) =>
    apiSend("/api/users", "POST", body);
  const updateUser = (username: string, body: Record<string, any>) =>
    apiSend(`/api/users/${encodeURIComponent(username)}`, "PUT", body);
  const resetPassword = (username: string, new_password: string) =>
    apiSend(`/api/users/${encodeURIComponent(username)}/password`, "POST", { new_password });
  const deleteUser = (username: string) =>
    apiSend(`/api/users/${encodeURIComponent(username)}`, "DELETE");

  // --- Roles ---
  const createRole = (body: Record<string, any>) =>
    apiSend("/api/roles", "POST", body);
  const updateRole = (name: string, body: Record<string, any>) =>
    apiSend(`/api/roles/${encodeURIComponent(name)}`, "PUT", body);
  const deleteRole = (name: string) =>
    apiSend(`/api/roles/${encodeURIComponent(name)}`, "DELETE");

  return {
    users, roles, menus, loading, error, loadAll,
    createUser, updateUser, resetPassword, deleteUser,
    createRole, updateRole, deleteRole,
  };
}
