import { api } from "./api";
import { apiUrl } from "./apiBase";

const DASHBOARD_BOOTSTRAP_CACHE_KEY = "urbanSentinel.dashboardBootstrap";
const DASHBOARD_BOOTSTRAP_TTL_MS = 15_000;

function nowMs() {
  return Date.now();
}

export function readDashboardBootstrapCache() {
  if (typeof sessionStorage === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(DASHBOARD_BOOTSTRAP_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed?.savedAt || nowMs() - parsed.savedAt > DASHBOARD_BOOTSTRAP_TTL_MS) {
      sessionStorage.removeItem(DASHBOARD_BOOTSTRAP_CACHE_KEY);
      return null;
    }
    return parsed.data || null;
  } catch {
    return null;
  }
}

export function writeDashboardBootstrapCache(data) {
  if (typeof sessionStorage === "undefined" || !data) return data;
  try {
    sessionStorage.setItem(
      DASHBOARD_BOOTSTRAP_CACHE_KEY,
      JSON.stringify({
        savedAt: nowMs(),
        data,
      })
    );
  } catch {
    // Ignore storage issues and continue with live data only.
  }
  return data;
}

export async function fetchDashboardBootstrap() {
  const response = await api(apiUrl("/user/dashboard-bootstrap"), { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Bootstrap request failed (${response.status})`);
  }
  const payload = await response.json();
  return writeDashboardBootstrapCache(payload);
}

export async function prefetchDashboardBootstrap() {
  try {
    return await fetchDashboardBootstrap();
  } catch {
    return null;
  }
}
