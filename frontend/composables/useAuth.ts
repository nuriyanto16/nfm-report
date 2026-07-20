// State autentikasi. Token + identitas disimpan di cookie agar middleware
// (SSR + client) bisa membaca role & menu yang diizinkan.
import { computed } from "vue";

export function useAuth() {
  const opts = { sameSite: "lax" as const, maxAge: 60 * 60 * 12, path: "/" };
  const token = useCookie<string | null>("report_token", opts);
  const username = useCookie<string | null>("report_user", opts);
  const role = useCookie<string | null>("report_role", opts);
  // Menu yang boleh diakses, disimpan sebagai string dipisah koma.
  const menusRaw = useCookie<string | null>("report_menus", opts);

  const isLoggedIn = computed(() => !!token.value);
  const menus = computed<string[]>(() =>
    (menusRaw.value || "").split(",").map((s) => s.trim()).filter(Boolean),
  );
  const isAdmin = computed(() => menus.value.includes("users"));

  function hasMenu(key: string): boolean {
    return menus.value.includes(key);
  }

  function applyMe(me: { username?: string; role?: string; menus?: string[] }) {
    if (me.username) username.value = me.username;
    if (me.role !== undefined) role.value = me.role;
    if (me.menus) menusRaw.value = me.menus.join(",");
  }

  async function login(user: string, password: string): Promise<void> {
    const base = useApiBase();
    const res = await $fetch<{
      token: string; username: string; role: string; menus: string[];
    }>(`${base}/api/login`, { method: "POST", body: { username: user, password } });
    token.value = res.token;
    applyMe(res);
  }

  // Refresh identitas dari server (mis. setelah role diubah admin).
  async function refreshMe(): Promise<void> {
    try {
      const me = await apiGet<{ username: string; role: string; menus: string[] }>(
        "/api/me",
      );
      applyMe(me);
    } catch {
      /* dibiarkan; middleware akan menangani 401 */
    }
  }

  function logout() {
    token.value = null;
    username.value = null;
    role.value = null;
    menusRaw.value = null;
    return navigateTo("/login");
  }

  return {
    token, username, role, menus, isLoggedIn, isAdmin,
    hasMenu, login, logout, refreshMe,
  };
}
