// Guard global: butuh login untuk semua halaman kecuali /login, dan
// membatasi akses halaman sesuai menu yang diizinkan role user.

// Peta path -> menu key. Path yang tak terdaftar (mis. /profil) bebas diakses
// selama sudah login.
const ROUTE_MENU: Record<string, string> = {
  "/": "dashboard",
  "/dashboard": "dashboard",
  "/harian": "harian",
  "/mingguan": "mingguan",
  "/bulanan": "bulanan",
  "/monitoring": "monitoring",
  "/project": "project_mgmt",
  "/evaluasi": "evaluasi_tw",
  "/sumber": "sources",
  "/users": "users",
};

export default defineNuxtRouteMiddleware((to) => {
  const token = useCookie<string | null>("report_token", { path: "/" }).value;
  const menus = (useCookie<string | null>("report_menus", { path: "/" }).value || "")
    .split(",").map((s) => s.trim()).filter(Boolean);

  const firstAllowed = () => {
    if (menus.includes("dashboard")) return "/";
    for (const [path, key] of Object.entries(ROUTE_MENU)) {
      if (path !== "/" && path !== "/dashboard" && menus.includes(key)) return path;
    }
    return "/profil"; // fallback: user tanpa menu apa pun tetap bisa ganti password
  };

  if (to.path === "/login") {
    if (token) return navigateTo(firstAllowed());
    return;
  }
  if (!token) return navigateTo("/login");

  // Cek akses menu untuk path yang dilindungi.
  const needed = ROUTE_MENU[to.path];
  if (needed && !menus.includes(needed)) {
    return navigateTo(firstAllowed());
  }
});
