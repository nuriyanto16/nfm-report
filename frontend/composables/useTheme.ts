import { ref, onMounted } from "vue";

const theme = ref<"dark" | "light">("dark");

export function useTheme() {
  function applyTheme(t: "dark" | "light") {
    theme.value = t;
    if (import.meta.client) {
      document.documentElement.setAttribute("data-theme", t);
      localStorage.setItem("app_theme", t);
    }
  }

  function toggleTheme() {
    applyTheme(theme.value === "dark" ? "light" : "dark");
  }

  function initTheme() {
    if (import.meta.client) {
      const saved = localStorage.getItem("app_theme") as "dark" | "light" | null;
      if (saved === "light" || saved === "dark") {
        applyTheme(saved);
      } else {
        applyTheme("dark"); // Default dark mode as existing
      }
    }
  }

  return {
    theme,
    toggleTheme,
    applyTheme,
    initTheme,
  };
}
