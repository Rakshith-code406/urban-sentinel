const RENDER_BACKEND_URL = "https://urban-sentinel-backend-xmm1.onrender.com";

function resolveApiBase() {
  const configured = (import.meta.env.VITE_API_BASE_URL || "").trim().replace(/\/$/, "");
  if (configured) {
    return configured;
  }

  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return "";
    }
  }

  return RENDER_BACKEND_URL;
}

export const API_BASE = resolveApiBase();

export function apiUrl(path) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${normalizedPath}`;
}
