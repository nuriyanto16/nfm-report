// Wrapper $fetch dengan base URL backend + helper query string.
export function useApiBase(): string {
  return useRuntimeConfig().public.apiBase as string;
}

export function buildQuery(params: Record<string, any>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    if (Array.isArray(v)) {
      if (v.length) q.set(k, v.join(","));
    } else {
      q.set(k, String(v));
    }
  }
  const s = q.toString();
  return s ? `?${s}` : "";
}

function authHeaders(): Record<string, string> {
  const token = useCookie<string | null>("report_token").value;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiGet<T>(path: string, params: Record<string, any> = {}): Promise<T> {
  const base = useApiBase();
  try {
    return await $fetch<T>(`${base}${path}${buildQuery(params)}`, {
      headers: authHeaders(),
    });
  } catch (e: any) {
    // Sesi habis -> kembali ke halaman login.
    if (e?.response?.status === 401 && import.meta.client) {
      await navigateTo("/login");
    }
    throw e;
  }
}

// POST/PUT/DELETE dengan token. Melempar error berisi detail dari backend.
export async function apiSend<T>(
  path: string,
  method: "POST" | "PUT" | "DELETE",
  body?: Record<string, any>,
): Promise<T> {
  const base = useApiBase();
  try {
    return await $fetch<T>(`${base}${path}`, {
      method,
      headers: authHeaders(),
      body,
    });
  } catch (e: any) {
    if (e?.response?.status === 401 && import.meta.client) {
      await navigateTo("/login");
    }
    // Normalisasi pesan agar UI bisa menampilkan detail dari FastAPI.
    const detail = e?.data?.detail || e?.message || "Terjadi kesalahan";
    throw new Error(detail);
  }
}

export function exportUrl(params: Record<string, any>): string {
  return `${useApiBase()}/api/export${buildQuery(params)}`;
}

// Unduh file export dengan menyertakan token auth, lalu trigger save di browser.
export async function downloadExport(params: Record<string, any>): Promise<void> {
  const url = exportUrl(params);
  const res = await fetch(url, { headers: authHeaders() });
  if (res.status === 401) {
    await navigateTo("/login");
    return;
  }
  if (!res.ok) throw new Error(`Export gagal (${res.status})`);
  const blob = await res.blob();
  const cd = res.headers.get("content-disposition") || "";
  const m = cd.match(/filename="?([^"]+)"?/);
  const filename = m ? m[1] : `laporan.${params.format || "bin"}`;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
}
