export default defineNuxtConfig({
  compatibilityDate: "2025-01-01",
  devtools: { enabled: false },
  ssr: true,
  css: ["~/assets/css/main.css"],
  runtimeConfig: {
    public: {
      // URL backend FastAPI. Override saat build/deploy via NUXT_PUBLIC_API_BASE.
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8000",
    },
  },
  app: {
    // Untuk deploy di subpath (mis. /tools/report/) set NUXT_APP_BASE_URL.
    baseURL: process.env.NUXT_APP_BASE_URL || "/",
    head: {
      title: "FAST REPORT",
      meta: [{ name: "viewport", content: "width=device-width, initial-scale=1" }],
    },
  },
});
