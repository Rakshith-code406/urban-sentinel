import { useNavigate } from "react-router-dom";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, ChevronUp, ClipboardList, Clock3, FileSearch, ShieldAlert, X } from "lucide-react";
import { StackedCards } from "@/components/ui/glass-cards";
import { TestimonialStack } from "@/components/ui/glass-testimonial-swiper";
import { IncidentReportMiddle } from "@/components/ui/incident-report-middle";
import { SENSOR_CARD_IMAGES } from "@/components/ui/sensor-card-content";
import AdminControlPanel from "@/components/AdminControlPanel";
import EnvironmentSummary from "@/components/EnvironmentSummary";
import { api } from "@/services/api";
import { API_BASE } from "@/services/apiBase";
import { fetchDashboardBootstrap, readDashboardBootstrapCache } from "@/services/dashboardCache";
import { clearAuthSession, getStoredUser } from "@/services/session";
import "../styles/home.css";

const POLL_INTERVAL_MS = 10000;
const LOCATION_STORAGE_KEY = "urbanSentinelLocation";
const SENSOR_SNAPSHOT_CACHE_KEY = "urbanSentinel.sensorSnapshot";
const LOCATION_FALLBACK_LABEL = "Location not available";
const NON_WEATHER_SIMULATION_CONFIG = {
  noise_level: { baseline: 45, min: 30, max: 120, moderate: 80, danger: 100, drift: 2.4, label: "Noise Level", dangerWhen: "high" },
  flood_level: { baseline: 10, min: 0, max: 100, moderate: 45, danger: 80, drift: 1.8, label: "Flood Level", dangerWhen: "high" },
  light_percent: { baseline: 70, min: 0, max: 100, moderate: 35, danger: 20, drift: 3.2, label: "Light Intensity", dangerWhen: "low" },
  bin_fill: { baseline: 30, min: 0, max: 100, moderate: 70, danger: 90, drift: 1.5, label: "Waste Bin Fill", dangerWhen: "high" },
};
const NON_WEATHER_SIMULATION_SENSOR_IDS = new Set(Object.keys(NON_WEATHER_SIMULATION_CONFIG));
const RESOLVED_SENSOR_FALLBACKS = {
  flood_level: { value: 5, increment: 6, status: "RESOLVED - Water receding" },
  traffic_total: { value: 2, increment: 2, status: "RESOLVED - Flow restored" },
  noise_level: { value: 38, increment: 4, status: "RESOLVED - Noise reduced" },
  light_percent: { value: 72, increment: 3, status: "RESOLVED - Lighting restored" },
  bin_fill: { value: 18, increment: 6, status: "RESOLVED - Bin cleared" },
  fire_smoke: { value: 10, increment: 6, status: "RESOLVED - Smoke under control" },
  parking_available: { value: 2, increment: 2, status: "RESOLVED - Parking restored", cycle: [0, 1, 2, 1] },
};
const DEFAULT_SENSOR_DATA = {
  traffic_total: 30,
  fire_smoke: 0,
  parking_available: 6,
  noise_level: 40,
  flood_level: 10,
  light_percent: 70,
  bin_fill: 20,
};
const STREET_LIGHT_DAY_THRESHOLD = 70;
const STREET_LIGHT_OPERATIONAL_MIN = 40;
const STREET_LIGHT_OPERATIONAL_MAX = 80;
const STREET_LIGHT_FAULT_LOW = 20;
const STREET_LIGHT_FAULT_HIGH = 95;

function readCachedSensorSnapshot() {
  if (typeof sessionStorage === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(SENSOR_SNAPSHOT_CACHE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function writeCachedSensorSnapshot(snapshot) {
  if (typeof sessionStorage === "undefined" || !snapshot) return snapshot;
  try {
    sessionStorage.setItem(SENSOR_SNAPSHOT_CACHE_KEY, JSON.stringify(snapshot));
  } catch {
    // Ignore cache write failures.
  }
  return snapshot;
}

function getResolvedSensorValue(sensorId, currentValue, resolutionInfo, config) {
  const elapsedSteps = Math.max(0, Math.floor((Date.now() - resolutionInfo.seenAt) / POLL_INTERVAL_MS));
  const stepCount = elapsedSteps + 1;
  const targetValue = Number(config.value);
  const baselineValue = Number.isFinite(currentValue) ? currentValue : targetValue;
  const increment = Math.max(Number(config.increment) || 0, 0);
  const distanceToTarget = Math.abs(baselineValue - targetValue);
  const movement = increment > 0 ? Math.min(distanceToTarget, stepCount * increment) : distanceToTarget;

  let nextValue = baselineValue;
  if (baselineValue > targetValue) {
    nextValue = baselineValue - movement;
  } else if (baselineValue < targetValue) {
    nextValue = baselineValue + movement;
  }

  const hasReachedTarget = Math.abs(nextValue - targetValue) < 0.0001;
  if (hasReachedTarget && Array.isArray(config.cycle) && config.cycle.length) {
    nextValue = targetValue + config.cycle[elapsedSteps % config.cycle.length];
  }

  return Number(nextValue.toFixed(1));
}

function severityFromStatus(status) {
  const normalized = String(status || "").toUpperCase();
  if (!normalized) return null;
  if (
    normalized.includes("CRITICAL") ||
    normalized.includes("HAZARDOUS") ||
    normalized.includes("FULL!") ||
    normalized.includes("EMERGENCY") ||
    normalized.includes("FAULT") ||
    normalized.includes("ILLEGAL")
  ) {
    return "Danger";
  }
  if (
    normalized.includes("WARNING") ||
    normalized.includes("MODERATE") ||
    normalized.includes("CAUTION") ||
    normalized.includes("NEARLY FULL") ||
    normalized.includes("WATCH")
  ) {
    return "Moderate";
  }
  return "Safe";
}

const SENSOR_DEFINITIONS = [
  {
    id: "flood_level",
    shortCode: "FLD",
    label: "Flood Level",
    unit: "%",
    getValue: (data) => data.flood_level,
    statusKey: "flood_status",
    classify: (value) => getSimulationSeverity("flood_level", value),
    levels: { Safe: "Safe", Moderate: "Moderate", Danger: "Dangerous" },
    advice: {
      Safe: "Road level is stable with no flooding indicators.",
      Moderate: "Water rise detected. Low-lying lanes may get affected.",
      Danger: "Flood conditions likely. Use alternate routes and warn authorities.",
    },
  },
  {
    id: "traffic_total",
    shortCode: "TRF",
    label: "Traffic Density",
    unit: "veh",
    getValue: (data) => data.traffic_total,
    statusKey: "traffic_status",
    classify: (value, data) => severityFromStatus(data.traffic_status) || (value >= 16 ? "Danger" : value >= 8 ? "Moderate" : "Safe"),
    levels: { Safe: "Smooth Flow", Moderate: "Congestion Watch", Danger: "Severe Jam" },
    advice: {
      Safe: "Traffic is moving smoothly across lanes.",
      Moderate: "Congestion building up. Expect slower movement.",
      Danger: "Heavy traffic lock. Delay travel if possible.",
    },
  },
  {
    id: "noise_level",
    shortCode: "NSE",
    label: "Noise Level",
    unit: "dB",
    getValue: (data) => data.noise_level,
    statusKey: "noise_status",
    classify: (value) => getSimulationSeverity("noise_level", value),
    levels: { Safe: "Safe", Moderate: "Moderate", Danger: "Dangerous" },
    advice: {
      Safe: "Ambient sound is within healthy levels.",
      Moderate: "Noise is elevated. Limit long exposure in this area.",
      Danger: "High noise stress detected. Ear protection advised.",
    },
  },
  {
    id: "light_percent",
    shortCode: "LGT",
    label: "Light Intensity",
    unit: "%",
    getValue: (data) => data.light_percent,
    statusKey: "light_status",
    classify: (value) => getSimulationSeverity("light_percent", value),
    levels: { Safe: "Safe", Moderate: "Moderate", Danger: "Dangerous" },
    advice: {
      Safe: "Lighting conditions are being managed correctly for the current time.",
      Moderate: "Ambient light is low, but still within expected night-time behavior.",
      Danger: "Street-light fault detected. Visibility support is compromised.",
    },
  },
  {
    id: "bin_fill",
    shortCode: "BIN",
    label: "Waste Bin Fill",
    unit: "%",
    getValue: (data) => data.bin_fill,
    statusKey: "bin_status",
    classify: (value) => getSimulationSeverity("bin_fill", value),
    levels: { Safe: "Normal", Moderate: "Moderate", Danger: "Nearly Full" },
    advice: {
      Safe: "Bin capacity is healthy.",
      Moderate: "Bin nearing limit. Cleaning cycle should be scheduled.",
      Danger: "Overflow risk high. Priority cleanup required.",
    },
  },
  {
    id: "fire_smoke",
    shortCode: "FIR",
    label: "Fire Smoke",
    unit: "%",
    getValue: (data) => data.fire_smoke,
    statusKey: "fire_status",
    classify: (value, data) => severityFromStatus(data.fire_status) || (value >= 80 ? "Danger" : value >= 45 ? "Moderate" : "Safe"),
    levels: { Safe: "No Smoke", Moderate: "Fire Watch", Danger: "Fire Emergency" },
    advice: {
      Safe: "No major fire-smoke indication.",
      Moderate: "Abnormal smoke traces. Keep area under watch.",
      Danger: "Critical smoke detected. Send emergency alert immediately.",
    },
  },
  {
    id: "parking_available",
    shortCode: "PRK",
    label: "Parking Availability",
    unit: "slots",
    getValue: (data) => data.parking_available,
    statusKey: "parking_status",
    classify: (value, data) => {
      if (String(data.parking_a || "").includes("ILLEGAL") || String(data.parking_b || "").includes("ILLEGAL")) {
        return "Danger";
      }
      return value <= 0 ? "Danger" : value === 1 ? "Moderate" : "Safe";
    },
    levels: { Safe: "Slots Open", Moderate: "One Slot Left", Danger: "Parking Full" },
    advice: {
      Safe: "Parking availability is healthy.",
      Moderate: "Parking space is getting tight.",
      Danger: "Parking capacity is exhausted or illegally occupied.",
    },
  },
];

function parseDashboardTimestamp(value) {
  if (!value) return new Date(NaN);
  if (value instanceof Date) return value;
  const raw = String(value).trim();
  if (!raw) return new Date(NaN);
  const hasTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(raw);
  return new Date(hasTimezone ? raw : `${raw}Z`);
}

function formatTimestamp(value) {
  if (!value) return "Live now";
  const parsed = parseDashboardTimestamp(value);
  if (Number.isNaN(parsed.getTime())) return "Live now";
  return parsed.toLocaleString();
}

function formatNumber(value, unit) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return `0 ${unit}`.trim();
  const rounded = Number(value) % 1 === 0 ? Number(value) : Number(value).toFixed(1);
  return `${rounded} ${unit}`.trim();
}

function normalizeNumber(value, fallback) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function normalizeNullableNumber(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function normalizeIncomingSensorData(data = {}) {
  const next = { ...data };
  next.timestamp = data.timestamp ?? data.last_updated ?? null;
  next.last_updated = data.last_updated ?? data.timestamp ?? null;
  next.temperature = normalizeNullableNumber(data.temperature);
  next.humidity = normalizeNullableNumber(data.humidity);
  next.air_smoke = normalizeNullableNumber(data.air_smoke ?? data.air_quality);
  next.rain_percent = normalizeNullableNumber(data.rain_percent ?? data.rain_intensity);
  next.traffic_total = normalizeNullableNumber(data.traffic_total ?? data.traffic);
  next.fire_smoke = normalizeNullableNumber(data.fire_smoke ?? data.fire);
  next.parking_available = normalizeNullableNumber(data.parking_available ?? data.parking);
  next.noise_level = normalizeNullableNumber(data.noise_level ?? data.noise);
  next.flood_level = normalizeNullableNumber(data.flood_level ?? data.flood);
  next.light_percent = normalizeNullableNumber(data.light_percent ?? data.light);
  next.bin_fill = normalizeNullableNumber(data.bin_fill ?? data.waste);
  return next;
}

const LIVE_SENSOR_VALUE_KEYS = [
  "temperature",
  "humidity",
  "air_smoke",
  "rain_percent",
  "flood_level",
  "noise_level",
  "light_percent",
  "bin_fill",
  "traffic_lane1",
  "traffic_lane2",
  "traffic_total",
  "fire_smoke",
  "parking_available",
];

const LIVE_SENSOR_STATUS_KEYS = [
  "air_status",
  "temp_status",
  "rain_status",
  "flood_status",
  "noise_status",
  "light_status",
  "bin_status",
  "traffic_status",
  "fire_status",
  "parking_status",
  "parking_a",
  "parking_b",
];

function mergeSensorSnapshot(previous = {}, incoming = {}) {
  const next = { ...(previous || {}) };

  Object.entries(incoming || {}).forEach(([key, value]) => {
    if (LIVE_SENSOR_VALUE_KEYS.includes(key)) {
      if (value !== null && value !== undefined && !Number.isNaN(Number(value))) {
        next[key] = Number(value);
      } else if (!(key in next)) {
        next[key] = null;
      }
      return;
    }

    if (value !== undefined && value !== null && value !== "") {
      next[key] = value;
    } else if (!(key in next)) {
      next[key] = value ?? null;
    }
  });

  if (!next.timestamp && next.last_updated) {
    next.timestamp = next.last_updated;
  }
  if (!next.last_updated && next.timestamp) {
    next.last_updated = next.timestamp;
  }

  return next;
}

function getLatestHistoryValues(rows = []) {
  return [...rows].reverse().reduce((accumulator, row) => {
    if (!row || typeof row !== "object") return accumulator;
    LIVE_SENSOR_VALUE_KEYS.forEach((key) => {
      if (accumulator[key] !== undefined) return;
      const numeric = normalizeNullableNumber(row[key]);
      if (numeric !== null) {
        accumulator[key] = numeric;
      }
    });
    LIVE_SENSOR_STATUS_KEYS.forEach((key) => {
      if (accumulator[key] !== undefined) return;
      const value = row[key];
      if (value !== undefined && value !== null && value !== "") {
        accumulator[key] = value;
      }
    });
    if (!accumulator.timestamp && (row.timestamp || row.last_updated)) {
      accumulator.timestamp = row.timestamp ?? row.last_updated;
      accumulator.last_updated = row.last_updated ?? row.timestamp;
    }
    return accumulator;
  }, {});
}

function buildSensorFallbackSnapshot(environment = null) {
  const timestamp = new Date().toISOString();
  return normalizeIncomingSensorData({
    ...DEFAULT_SENSOR_DATA,
    temperature: environment?.temperature ?? 26,
    humidity: environment?.humidity ?? 60,
    air_smoke: environment?.air_smoke ?? 72,
    air_status: environment?.air_status ?? "Moderate",
    temp_status: environment?.temp_status ?? "Live weather",
    rain_percent: environment?.rain_percent ?? 12,
    rain_status: environment?.rain_status ?? "Low",
    timestamp,
    last_updated: timestamp,
  });
}

function trendLabel(current, previous, sensorId) {
  if (!Number.isFinite(current) || !Number.isFinite(previous)) return "No trend";
  const delta = current - previous;
  const absolute = Math.abs(delta);
  let threshold = 1;
  if (sensorId === "temperature") threshold = 0.6;
  if (sensorId === "humidity" || sensorId === "air_smoke" || sensorId === "fire_smoke") threshold = 3;
  if (sensorId === "traffic_total" || sensorId === "parking_available") threshold = 1;
  if (sensorId === "noise_level") threshold = 4;
  if (sensorId === "flood_level" || sensorId === "rain_percent" || sensorId === "bin_fill") threshold = 5;
  if (absolute < threshold) return "Stable";
  if (sensorId === "parking_available") return delta > 0 ? "Opening up" : "Filling up";
  if (sensorId === "light_percent") return delta > 0 ? "Brighter" : "Darker";
  return delta > 0 ? "Rising" : "Falling";
}

function freshnessLabel(timestamp) {
  if (!timestamp) return "Last updated unavailable";
  return formatTimeAgo(timestamp);
}

function emptyCounts() {
  return { Safe: 0, Moderate: 0, Danger: 0 };
}

function shortTimestamp(value) {
  if (!value) return "Just now";
  const parsed = parseDashboardTimestamp(value);
  if (Number.isNaN(parsed.getTime())) return "Just now";
  return parsed.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function truncateText(value, limit = 110) {
  const cleaned = String(value || "").replace(/\s+/g, " ").trim();
  if (!cleaned) return "No description was added for this report.";
  return cleaned.length > limit ? `${cleaned.slice(0, limit - 1)}...` : cleaned;
}

function getInitials(value) {
  const words = String(value || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!words.length) return "UR";
  return words
    .slice(0, 2)
    .map((word) => word.charAt(0).toUpperCase())
    .join("");
}

function isCoordinateLabel(value) {
  const normalized = String(value || "")
    .trim()
    .replace(/\s+/g, " ");
  if (!normalized) return false;
  return /^-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?$/.test(normalized);
}

function formatReadableLocation(address = {}) {
  const city =
    address.city ||
    address.town ||
    address.village ||
    address.hamlet ||
    address.suburb ||
    address.county ||
    "";
  const state = address.state || address.state_district || "";
  const country = address.country || "";
  const parts = [city, state, country].filter(Boolean);
  return parts.length ? parts.join(", ") : LOCATION_FALLBACK_LABEL;
}

function getSafeLocationLabel(value) {
  const normalized = String(value || "").trim();
  if (!normalized || isCoordinateLabel(normalized)) {
    return LOCATION_FALLBACK_LABEL;
  }
  return normalized;
}

function validateRange(value, min, max) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return null;
  if (numeric < min || numeric > max) return null;
  return numeric;
}

function getSimulationSeverity(sensorId, value) {
  const config = NON_WEATHER_SIMULATION_CONFIG[sensorId];
  if (!config || !Number.isFinite(value)) return "Safe";
  if (config.dangerWhen === "low") {
    if (value <= config.danger) return "Danger";
    if (value <= config.moderate) return "Moderate";
    return "Safe";
  }
  if (value >= config.danger) return "Danger";
  if (value >= config.moderate) return "Moderate";
  return "Safe";
}

function clampNumber(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function getNextSimulatedValue(current, config, options = {}) {
  const currentValue = Number.isFinite(current) ? current : config.baseline;
  const anchor = Number.isFinite(options.anchor) ? options.anchor : config.baseline;
  const bias = Number(options.bias || 0);
  const stabilization = (anchor - currentValue) * 0.12;
  const nextValue = clampNumber(currentValue + stabilization + bias, config.min, config.max);
  return Number(nextValue.toFixed(1));
}

function getSimulationOverallStatus(values) {
  const severities = Object.keys(NON_WEATHER_SIMULATION_CONFIG).map((sensorId) =>
    getSimulationSeverity(sensorId, Number(values[sensorId]))
  );
  if (severities.includes("Danger")) return "DANGER";
  if (severities.includes("Moderate")) return "MODERATE";
  return "SAFE";
}

function getSimulationTrend(previousValues, nextValues) {
  if (!previousValues) return "stable";

  const noiseDelta = Number(nextValues.noise_level || 0) - Number(previousValues.noise_level || 0);
  const floodDelta = Number(nextValues.flood_level || 0) - Number(previousValues.flood_level || 0);
  const lightDelta = Number(nextValues.light_percent || 0) - Number(previousValues.light_percent || 0);
  const binDelta = Number(nextValues.bin_fill || 0) - Number(previousValues.bin_fill || 0);
  const riskDelta = noiseDelta * 0.3 + floodDelta * 0.4 - lightDelta * 0.25 + binDelta * 0.35;

  if (riskDelta > 1.2) return "rising";
  if (riskDelta < -1.2) return "falling";
  return "stable";
}

function applyEnvironmentImpact(simulatedValues, environment) {
  const next = { ...simulatedValues };
  const rainPercent = Number(environment?.rain_percent);
  const temperature = Number(environment?.temperature);
  const airQuality = Number(environment?.air_smoke);
  const isNight = environment?.is_day === 0 || environment?.is_day === false;

  if (Number.isFinite(rainPercent) && rainPercent > 0) {
    next.flood_level = clampNumber(next.flood_level + Math.min(6, rainPercent * 0.08), 0, 100);
  }

  if (Number.isFinite(temperature) && temperature >= 30) {
    next.bin_fill = clampNumber(next.bin_fill + Math.min(3.5, (temperature - 29) * 0.35), 0, 100);
  }

  if (isNight) {
    next.light_percent = clampNumber(next.light_percent - 6, 0, 100);
  } else if (next.light_percent < NON_WEATHER_SIMULATION_CONFIG.light_percent.baseline) {
    next.light_percent = clampNumber(next.light_percent + 2.5, 0, 100);
  }

  if (Number.isFinite(airQuality) && airQuality >= 100) {
    next.noise_level = clampNumber(next.noise_level + 1.5, 0, 150);
  }

  return next;
}

function mapAirQualityStatus(value) {
  if (!Number.isFinite(value)) return "Good";
  if (value <= 50) return "Safe";
  if (value <= 100) return "Moderate";
  if (value <= 200) return "Poor";
  return "Hazardous";
}

function mapFloodStatus(value) {
  const severity = getSimulationSeverity("flood_level", value);
  if (severity === "Danger") return "Dangerous";
  if (severity === "Moderate") return "Moderate";
  if (severity === "Safe") return "Safe";
  return "Safe";
}

function mapNoiseStatus(value) {
  const severity = getSimulationSeverity("noise_level", value);
  if (severity === "Danger") return "Dangerous";
  if (severity === "Moderate") return "Moderate";
  if (severity === "Safe") return "Safe";
  return "Safe";
}

function mapBinStatus(value) {
  const severity = getSimulationSeverity("bin_fill", value);
  if (severity === "Danger") return "Nearly Full";
  if (severity === "Moderate") return "Moderate";
  if (severity === "Safe") return "Normal";
  return "Normal";
}

function mapLightStatus(value) {
  if (!Number.isFinite(value)) return "Night Time - Lights ON";
  if (value > STREET_LIGHT_DAY_THRESHOLD) return "Day Time - Lights OFF";
  if (value < STREET_LIGHT_FAULT_LOW || value > STREET_LIGHT_FAULT_HIGH) return "Fault Detected";
  return "Night Time - Lights ON";
}

function updateStreetLightIntensity(prev) {
  const base = Number(prev);
  if (!Number.isFinite(base)) {
    return null;
  }
  return Number(clampNumber(base, STREET_LIGHT_OPERATIONAL_MIN, STREET_LIGHT_OPERATIONAL_MAX).toFixed(1));
}

function getStreetLightMonitoringState(ldrValue, liveIntensity, previousLdrValue) {
  const parsedLdr = Number(ldrValue);
  const safeLdr = Number.isFinite(parsedLdr) ? parsedLdr : STREET_LIGHT_DAY_THRESHOLD + 5;
  const isDayTime = safeLdr > STREET_LIGHT_DAY_THRESHOLD;
  const ambientShift = Number.isFinite(previousLdrValue) ? Math.abs(safeLdr - previousLdrValue) : 0;
  const parsedIntensity = Number(liveIntensity);
  const displayIntensity = Number.isFinite(parsedIntensity)
    ? parsedIntensity
    : null;
  const hasFault =
    !isDayTime &&
    (displayIntensity < STREET_LIGHT_FAULT_LOW ||
      displayIntensity > STREET_LIGHT_FAULT_HIGH ||
      ambientShift >= 35);

  if (isDayTime) {
    return {
      title: "Light Monitoring",
      status: "Day Time",
      statusText: "Lights OFF",
      displayValue: "Lights OFF",
      severity: "Safe",
      adviceLine: "Street lights are currently OFF while daylight conditions remain sufficient.",
      trendText: "Daylight stable",
      liveReading: null,
      isDayTime: true,
      hasFault: false,
    };
  }

  if (hasFault) {
    const emergencyIntensity = Number(
      clampNumber(
        Number.isFinite(displayIntensity) ? displayIntensity : safeLdr,
        10,
        99,
      ).toFixed(0),
    );
    return {
      title: "Street Light System",
      status: "Fault Detected",
      statusText: "Immediate maintenance required",
      displayValue: `${emergencyIntensity}%`,
      severity: "Danger",
      adviceLine: "Light failure detected. Maintenance required immediately.",
      trendText: "Priority HIGH",
      liveReading: emergencyIntensity,
      isDayTime: false,
      hasFault: true,
    };
  }

  return {
    title: "Street Light System",
    status: "Night Time",
    statusText: "Lights ON",
    displayValue: `${Math.round(displayIntensity)}%`,
    severity: "Safe",
    adviceLine: "Lighting functioning normally for current night-time conditions.",
    trendText: "Night lighting stable",
    liveReading: Math.round(displayIntensity),
    isDayTime: false,
    hasFault: false,
  };
}

function normalizeStreetLightIntensity(rawValue) {
  const numeric = Number(rawValue);
  if (!Number.isFinite(numeric)) {
    return null;
  }
  return Number(clampNumber(numeric, STREET_LIGHT_OPERATIONAL_MIN, STREET_LIGHT_OPERATIONAL_MAX).toFixed(1));
}

function buildStreetLightSyncPayload(rawLdrValue, lightState) {
  return {
    light_percent: Number.isFinite(rawLdrValue) ? Math.round(rawLdrValue) : null,
    light_status: lightState.hasFault
      ? "Fault Detected"
      : lightState.isDayTime
        ? "Day Time - Lights OFF"
        : "Night Time - Lights ON",
  };
}

function getStreetLightAlertValue(lightState) {
  if (lightState.hasFault && Number.isFinite(lightState.liveReading)) {
    return `${lightState.liveReading}%`;
  }
  return lightState.isDayTime ? "Day mode" : "Night lighting stable";
}

function getStreetLightAlertMessage(lightState) {
  if (lightState.hasFault) {
    return "Street Light Failure Detected";
  }
  return "No active issue";
}

function detailedStatusToSeverity(status) {
  const normalized = String(status || "").toUpperCase();
  if (normalized === "CRITICAL" || normalized === "DANGER") return "Danger";
  if (normalized === "WARNING") return "Moderate";
  return "Safe";
}

function formatTimeAgo(timestamp) {
  if (!timestamp) return "Last updated: unavailable";
  const parsed = parseDashboardTimestamp(timestamp);
  if (Number.isNaN(parsed.getTime())) return "Last updated: unavailable";
  const diffMs = Date.now() - parsed.getTime();
  const diffMinutes = Math.max(0, Math.round(diffMs / 60000));
  const timeLabel = parsed.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  if (diffMinutes < 1) return `Updated just now • Last updated: ${timeLabel}`;
  if (diffMinutes === 1) return `Updated 1 min ago • Last updated: ${timeLabel}`;
  if (diffMinutes < 60) return `Updated ${diffMinutes} min ago • Last updated: ${timeLabel}`;
  return `Last updated: ${timeLabel}`;
}

function getEnvironmentFallback(target = {}) {
  const timestamp = new Date().toISOString();
  return {
    success: true,
    source: "fallback",
    location: {
      label: target?.label || LOCATION_FALLBACK_LABEL,
      latitude: target?.latitude ?? null,
      longitude: target?.longitude ?? null,
    },
    temperature: 26,
    humidity: 60,
    air_smoke: 72,
    air_quality: "Moderate",
    air_status: "Moderate",
    rain_intensity: "Low",
    rain_percent: 12,
    rain_status: "Low",
    timestamp,
    last_updated: timestamp,
  };
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 2000) {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } finally {
    window.clearTimeout(timer);
  }
}

function normalizeEnvironmentPayload(payload, target) {
  const envelopeStatus = payload?.status;
  const source = payload?.source;
  const data = payload?.data || payload || {};
  const location = data?.location || payload?.location || {
    label: target?.label || LOCATION_FALLBACK_LABEL,
    latitude: target?.latitude ?? null,
    longitude: target?.longitude ?? null,
  };
  return {
    status: envelopeStatus === "success" || envelopeStatus === "fallback" ? envelopeStatus : (source === "fallback" ? "fallback" : "success"),
    source: source || "fallback",
    location,
    temperature: data?.temperature ?? payload?.temperature ?? null,
    humidity: data?.humidity ?? payload?.humidity ?? null,
    air_smoke: data?.airSmoke ?? payload?.air_smoke ?? null,
    air_quality: data?.airQuality ?? payload?.air_quality ?? null,
    air_status: payload?.air_status ?? data?.airQuality ?? payload?.air_quality ?? null,
    rain_intensity: data?.rain ?? payload?.rain_intensity ?? null,
    rain_percent: data?.rainPercent ?? payload?.rain_percent ?? null,
    rain_status: payload?.rain_status ?? data?.rain ?? payload?.rain_intensity ?? null,
    timestamp: data?.timestamp ?? payload?.timestamp ?? null,
    last_updated: data?.lastUpdated ?? payload?.last_updated ?? payload?.timestamp ?? null,
  };
}

function normalizeLiveIotPayload(payload) {
  if (!payload || typeof payload !== "object") return null;

  const airValue = normalizeNullableNumber(
    payload?.air?.live_value ?? payload?.air?.value ?? payload?.air_smoke
  );
  const temperatureValue = normalizeNullableNumber(
    payload?.temperature?.live_value ?? payload?.temperature?.value ?? payload?.temperature
  );
  const humidityValue = normalizeNullableNumber(
    payload?.humidity?.live_value ?? payload?.humidity?.value ?? payload?.humidity
  );
  const rainValue = normalizeNullableNumber(
    payload?.rain?.live_value ?? payload?.rain?.value ?? payload?.rain_percent
  );
  const timestamp = payload?.timestamp ?? payload?.last_updated ?? null;

  return {
    air_smoke: airValue,
    air_status: payload?.air?.status ?? payload?.air_status ?? "Safe",
    air_trend: payload?.air?.trend ?? payload?.air_trend ?? "No trend",
    temperature: temperatureValue,
    humidity: humidityValue,
    temp_status:
      payload?.temperature?.status ??
      payload?.temp_status ??
      payload?.humidity?.status ??
      "Safe",
    rain_percent: rainValue,
    rain_status: payload?.rain?.status ?? payload?.rain_status ?? "Safe",
    timestamp,
    last_updated: timestamp,
  };
}

function normalizeLatestSensorPayload(payload) {
  if (!payload || typeof payload !== "object" || payload?.message) return null;

  return normalizeIncomingSensorData({
    temperature: payload?.temperature,
    humidity: payload?.humidity,
    air_smoke: payload?.air_smoke,
    air_status: payload?.air_status,
    temp_status: payload?.temp_status,
    rain_percent: payload?.rain_percent,
    rain_status: payload?.rain_status,
    flood_level: payload?.flood_level,
    flood_status: payload?.flood_status,
    noise_level: payload?.noise_level,
    noise_status: payload?.noise_status,
    light_percent: payload?.light_percent,
    light_status: payload?.light_status,
    bin_fill: payload?.bin_fill,
    bin_status: payload?.bin_status,
    traffic_lane1: payload?.traffic_lane1,
    traffic_lane2: payload?.traffic_lane2,
    traffic_total: payload?.traffic_total,
    traffic_status: payload?.traffic_status,
    fire_smoke: payload?.fire_smoke,
    fire_status: payload?.fire_status,
    parking_a: payload?.parking_a,
    parking_b: payload?.parking_b,
    parking_available: payload?.parking_available,
    parking_status: payload?.parking_status,
    timestamp: payload?.timestamp,
    last_updated: payload?.last_updated ?? payload?.timestamp,
  });
}

export default function Home() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const cachedBootstrap = readDashboardBootstrapCache();
  const cachedSensorSnapshot = readCachedSensorSnapshot();
  const [stats, setStats] = useState(
    () => cachedBootstrap?.stats || { total_issues: 0, pending: 0, resolved: 0 }
  );
  const [sensorData, setSensorData] = useState(() => cachedSensorSnapshot);
  const [sensorHistory, setSensorHistory] = useState([]);
  const [liveEnvironment, setLiveEnvironment] = useState(null);
  const [sensorDataError, setSensorDataError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [alerts, setAlerts] = useState(() => cachedBootstrap?.alerts || []);
  const [complaints, setComplaints] = useState(() => cachedBootstrap?.complaints || []);
  const [monitoringAlerts, setMonitoringAlerts] = useState(
    () => cachedBootstrap?.monitoring_alerts || []
  );
  const [adminActionBusy, setAdminActionBusy] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [locationState, setLocationState] = useState(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(LOCATION_STORAGE_KEY) || "null");
      if (!stored) {
        return { permission: "unknown", latitude: null, longitude: null, label: LOCATION_FALLBACK_LABEL };
      }
      return {
        ...stored,
        label: getSafeLocationLabel(stored.label),
      };
    } catch {
      return { permission: "unknown", latitude: null, longitude: null, label: LOCATION_FALLBACK_LABEL };
    }
  });
  const [showLocationPopup, setShowLocationPopup] = useState(() => {
    return !globalThis.__urbanSentinelLocationPromptHandled;
  });
  const [pendingRoute, setPendingRoute] = useState("");
  const [resolvedAlertSeenAt, setResolvedAlertSeenAt] = useState({});
  const [locationMenuOpen, setLocationMenuOpen] = useState(false);
  const [locationQuery, setLocationQuery] = useState("");
  const [locationResults, setLocationResults] = useState([]);
  const [locationSearchBusy, setLocationSearchBusy] = useState(false);
  const [reportDetailModal, setReportDetailModal] = useState(null);
  const [focusedEmergencyCardId, setFocusedEmergencyCardId] = useState("");
  const [focusEmergencyRequestKey, setFocusEmergencyRequestKey] = useState(0);
  const [showBackToTopArrow, setShowBackToTopArrow] = useState(false);
  const [activeSnapshotCategory, setActiveSnapshotCategory] = useState("");
  const [streetLightIntensity, setStreetLightIntensity] = useState(62);
  const activeLocationRequestRef = useRef("");
  const autoEmergencyTriggeredRef = useRef({});
  const lastDangerStateRef = useRef({});
  const previousLightLdrRef = useRef(null);
  const weatherSnapshotRef = useRef(null);
  const stableHeroLastUpdatedRef = useRef(null);
  const [alertTriggered, setAlertTriggered] = useState(false);
  const { data: dashboardBootstrapData, refetch: refetchDashboardBootstrap } = useQuery({
    queryKey: ["dashboard-bootstrap"],
    queryFn: fetchDashboardBootstrap,
    initialData: cachedBootstrap || undefined,
    placeholderData: (previous) => previous || cachedBootstrap || undefined,
    staleTime: 5_000,
    refetchInterval: 15_000,
  });

  const hasAdminSession = localStorage.getItem("adminSession") === "true";
  const userProfile = JSON.parse(getStoredUser() || "{}");
  const profileInitial = String(userProfile?.full_name || userProfile?.email || "U")
    .trim()
    .charAt(0)
    .toUpperCase();
  const hasLocationAccess =
    (locationState.permission === "granted" || locationState.permission === "manual") &&
    locationState.latitude !== null &&
    locationState.latitude !== undefined &&
    locationState.longitude !== null &&
    locationState.longitude !== undefined;
  const selectedLocation = hasLocationAccess ? getSafeLocationLabel(locationState.label) : "";
  const heroStatusMessage = hasLocationAccess
    ? `Live monitoring is active for ${getSafeLocationLabel(locationState.label)}.`
    : "Allow location access to enable live monitoring for your selected area.";

  const liveSensorQuery = useMemo(() => {
    const params = new URLSearchParams();
    if (hasLocationAccess) {
      params.set("latitude", String(locationState.latitude));
      params.set("longitude", String(locationState.longitude));
      const label = getSafeLocationLabel(locationState.label);
      if (label && label !== LOCATION_FALLBACK_LABEL) {
        params.set("location", label);
      }
    }
    const query = params.toString();
    return query ? `?${query}` : "";
  }, [hasLocationAccess, locationState.label, locationState.latitude, locationState.longitude]);

  const notify = (text) => {
    setFeedback(text);
    window.setTimeout(() => setFeedback(""), 3500);
  };

  useEffect(() => {
    const user = getStoredUser();

    if (!user) {
      navigate("/login", { replace: true });
    }
  }, [navigate]);

  const handleAuthExpired = useCallback(() => {
    clearAuthSession();
    setAlerts([]);
    setComplaints([]);
    setStats({ total_issues: 0, pending: 0, resolved: 0 });
    navigate("/login", { replace: true });
  }, [navigate]);

  const persistLocationState = useCallback((nextState) => {
    const sanitizedState = {
      ...nextState,
      label: getSafeLocationLabel(nextState?.label),
    };
    localStorage.setItem(LOCATION_STORAGE_KEY, JSON.stringify(sanitizedState));
    setLocationState(sanitizedState);
  }, []);

  const openLocationModal = useCallback(() => {
    setLocationMenuOpen(true);
  }, []);

  const closeLocationModal = useCallback(() => {
    setLocationMenuOpen(false);
  }, []);

  const reverseGeocodeCoordinates = useCallback(async (latitude, longitude) => {
    const params = new URLSearchParams({
      format: "jsonv2",
      lat: String(latitude),
      lon: String(longitude),
      zoom: "14",
      addressdetails: "1",
    });

    try {
      const response = await fetch(`https://nominatim.openstreetmap.org/reverse?${params.toString()}`, {
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Reverse geocoding failed.");
      }

      const payload = await response.json();
      return formatReadableLocation(payload?.address);
    } catch {
      return LOCATION_FALLBACK_LABEL;
    }
  }, []);

  const fetchLiveEnvironment = useCallback(async (target) => {
    if (
      (target?.permission !== "granted" && target?.permission !== "manual") ||
      target?.latitude === null ||
      target?.latitude === undefined ||
      target?.longitude === null ||
      target?.longitude === undefined
    ) {
      setLiveEnvironment(null);
      return;
    }

    const requestKey = `${target.permission}:${target.latitude}:${target.longitude}:${target.label || ""}`;
    activeLocationRequestRef.current = requestKey;

    try {
      const params = new URLSearchParams({
        latitude: String(target.latitude),
        longitude: String(target.longitude),
      });
      if (target.label) {
        params.set("location_name", target.label);
      }
      const response = await fetchWithTimeout(
        `${API_BASE}/iot/live-environment?${params.toString()}`,
        { cache: "no-store" },
        2000,
      );
      const payload = await response.json().catch(() => ({}));
      if (activeLocationRequestRef.current !== requestKey) {
        return;
      }
      const nextPayload =
        response.ok && (payload?.status === "success" || payload?.status === "fallback")
          ? normalizeEnvironmentPayload(payload, target)
          : normalizeEnvironmentPayload(getEnvironmentFallback(target), target);
      setLiveEnvironment(nextPayload);
      weatherSnapshotRef.current = {
        temperature: Number.isFinite(Number(nextPayload?.temperature)) ? Math.round(Number(nextPayload.temperature)) : null,
        humidity: Number.isFinite(Number(nextPayload?.humidity)) ? Number(nextPayload.humidity) : null,
        airQuality: Number.isFinite(Number(nextPayload?.air_smoke)) ? Number(nextPayload.air_smoke) : null,
        rainIntensity: Number.isFinite(Number(nextPayload?.rain_percent)) ? Number(nextPayload.rain_percent) : 0,
        lastUpdated: nextPayload?.last_updated || nextPayload?.timestamp || null,
      };
      if (nextPayload?.location?.label) {
        setLocationState((current) => {
          if (
            activeLocationRequestRef.current !== requestKey ||
            (current.permission === "manual" &&
              current.latitude !== target.latitude &&
              current.longitude !== target.longitude)
          ) {
            return current;
          }
          const next = {
            ...current,
            label: getSafeLocationLabel(nextPayload.location.label),
            latitude: nextPayload.location.latitude ?? current.latitude,
            longitude: nextPayload.location.longitude ?? current.longitude,
          };
          localStorage.setItem(LOCATION_STORAGE_KEY, JSON.stringify(next));
          return next;
        });
      }
    } catch (error) {
      if (activeLocationRequestRef.current !== requestKey) {
        return;
      }
      const fallbackPayload = normalizeEnvironmentPayload(getEnvironmentFallback(target), target);
      setLiveEnvironment(fallbackPayload);
      weatherSnapshotRef.current = {
        temperature: fallbackPayload.temperature,
        humidity: fallbackPayload.humidity,
        airQuality: fallbackPayload.air_smoke,
        rainIntensity: fallbackPayload.rain_percent,
        lastUpdated: fallbackPayload.last_updated,
      };
    }
  }, []);

  const requestBrowserLocation = useCallback(() => {
    if (!navigator.geolocation) {
      persistLocationState({
        permission: "denied",
        latitude: null,
        longitude: null,
        label: LOCATION_FALLBACK_LABEL,
      });
      globalThis.__urbanSentinelLocationPromptHandled = true;
      setShowLocationPopup(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const readableLocation = await reverseGeocodeCoordinates(position.coords.latitude, position.coords.longitude);
        persistLocationState({
          permission: "granted",
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          label: readableLocation,
        });
        globalThis.__urbanSentinelLocationPromptHandled = true;
        setShowLocationPopup(false);
        if (pendingRoute) {
          navigate(pendingRoute);
          setPendingRoute("");
        }
        closeLocationModal();
        setLocationQuery("");
        setLocationResults([]);
      },
      () => {
        persistLocationState({
          permission: "denied",
          latitude: null,
          longitude: null,
          label: LOCATION_FALLBACK_LABEL,
        });
        globalThis.__urbanSentinelLocationPromptHandled = true;
        setShowLocationPopup(false);
        setPendingRoute("");
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 300000 }
    );
  }, [closeLocationModal, navigate, pendingRoute, persistLocationState, reverseGeocodeCoordinates]);

  const fetchSensorData = useCallback(async () => {
    try {
      const [latestRes, smartLiveRes] = await Promise.all([
        fetchWithTimeout(`${API_BASE}/iot/latest`, { cache: "no-store" }, 3000).catch(() => null),
        fetchWithTimeout(`${API_BASE}/api/sensors/live${liveSensorQuery}`, { cache: "no-store" }, 5000).catch(() => null),
      ]);

      let latestSensorPayload = null;
      let smartLivePayload = null;

      if (latestRes?.ok) {
        const data = await latestRes.json().catch(() => ({}));
        latestSensorPayload = normalizeLatestSensorPayload(data);
      }

      if (smartLiveRes?.ok) {
        const payload = await smartLiveRes.json().catch(() => ({}));
        const snapshot = payload?.snapshot || payload;
        if (snapshot && !snapshot?.message && Object.keys(snapshot).length) {
          smartLivePayload = normalizeIncomingSensorData(snapshot);
        }
      }

      const mergedSensorPayload =
        latestSensorPayload || smartLivePayload
          ? {
              ...(latestSensorPayload || {}),
              ...(smartLivePayload || {}),
            }
          : null;

      if (mergedSensorPayload) {
        setSensorData((prev) => writeCachedSensorSnapshot(mergeSensorSnapshot(prev, mergedSensorPayload)));
        setSensorDataError("");
        const stableTimestamp = mergedSensorPayload?.timestamp || mergedSensorPayload?.last_updated || new Date().toISOString();
        if (!stableHeroLastUpdatedRef.current) {
          stableHeroLastUpdatedRef.current = formatTimestamp(stableTimestamp);
          setLastUpdated(stableHeroLastUpdatedRef.current);
        }
      } else {
        setSensorData((prev) => prev);
        setSensorDataError((current) => current || "Waiting for central sensor engine.");
      }
    } catch (error) {
      console.error("Sensor fetch error:", error);
      setSensorData((prev) => prev);
      setSensorDataError((current) => current || "Waiting for central sensor engine.");
    }
  }, [liveEnvironment, liveSensorQuery]);

  const fetchSensorHistory = useCallback(async () => {
    try {
      const [smartHistoryRes, historyRes] = await Promise.all([
        fetchWithTimeout(`${API_BASE}/api/sensors/history${liveSensorQuery ? `${liveSensorQuery}&limit=240` : "?limit=240"}`, { cache: "no-store" }, 5000).catch(() => null),
        fetchWithTimeout(`${API_BASE}/iot/history?hours=744&limit=10000`, { cache: "no-store" }, 5000).catch(() => null),
      ]);

      if (smartHistoryRes?.ok) {
        const payload = await smartHistoryRes.json().catch(() => ({}));
        setSensorHistory(Array.isArray(payload?.data) ? payload.data : []);
        return;
      }

      if (historyRes?.ok) {
        const payload = await historyRes.json().catch(() => ({}));
        setSensorHistory(Array.isArray(payload?.data) ? payload.data : []);
      }
    } catch (error) {
      console.error("Sensor history fetch error:", error);
    }
  }, [liveSensorQuery]);

  const fetchDashboardData = useCallback(async () => {
    try {
      const payload =
        queryClient.getQueryData(["dashboard-bootstrap"]) ||
        (await queryClient.fetchQuery({
          queryKey: ["dashboard-bootstrap"],
          queryFn: fetchDashboardBootstrap,
          staleTime: 5_000,
        }));
      setMonitoringAlerts(Array.isArray(payload?.monitoring_alerts) ? payload.monitoring_alerts : []);
      setAlerts(Array.isArray(payload?.alerts) ? payload.alerts : []);
      setComplaints(Array.isArray(payload?.complaints) ? payload.complaints : []);
      setStats(payload?.stats || { total_issues: 0, pending: 0, resolved: 0 });
      return;
    } catch (bootstrapError) {
      console.error("Dashboard bootstrap error:", bootstrapError);
    }

    const [monitoringAlertsRes, alertsRes, complaintsRes, statsRes] = await Promise.all([
      api(`${API_BASE}/api/alerts?limit=25`).catch(() => null),
      api(`${API_BASE}/user/emergency-alerts?limit=20`).catch(() => null),
      api(`${API_BASE}/issues`).catch(() => null),
      api(`${API_BASE}/user/stats`).catch(() => null),
    ]);

    if (monitoringAlertsRes?.ok) {
      const payload = await monitoringAlertsRes.json();
      setMonitoringAlerts(Array.isArray(payload?.alerts) ? payload.alerts : []);
    } else {
      setMonitoringAlerts([]);
    }

    if (alertsRes?.status === 401 || complaintsRes?.status === 401 || statsRes?.status === 401) {
      handleAuthExpired();
      return;
    }

    if (alertsRes?.ok) {
      const payload = await alertsRes.json();
      setAlerts(Array.isArray(payload?.alerts) ? payload.alerts : []);
    } else {
      setAlerts([]);
    }

    if (complaintsRes?.ok) {
      const payload = await complaintsRes.json();
      setComplaints(Array.isArray(payload) ? payload : []);
    } else {
      setComplaints([]);
    }

    if (statsRes?.ok) {
      const payload = await statsRes.json();
      setStats(payload);
    } else {
      setStats({ total_issues: 0, pending: 0, resolved: 0 });
    }
  }, [handleAuthExpired, queryClient]);

  useEffect(() => {
    if (!dashboardBootstrapData) return;
    setMonitoringAlerts(Array.isArray(dashboardBootstrapData?.monitoring_alerts) ? dashboardBootstrapData.monitoring_alerts : []);
    setAlerts(Array.isArray(dashboardBootstrapData?.alerts) ? dashboardBootstrapData.alerts : []);
    setComplaints(Array.isArray(dashboardBootstrapData?.complaints) ? dashboardBootstrapData.complaints : []);
    setStats(dashboardBootstrapData?.stats || { total_issues: 0, pending: 0, resolved: 0 });
  }, [dashboardBootstrapData]);

  const searchLocation = useCallback(async () => {
    const cleaned = locationQuery.trim();
    if (cleaned.length < 2) {
      setLocationResults([]);
      return;
    }

    setLocationSearchBusy(true);
    try {
      const response = await api(`${API_BASE}/iot/location-search?query=${encodeURIComponent(cleaned)}`);
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload?.detail || "Unable to search locations.");
      }
      const payload = await response.json();
      setLocationResults(Array.isArray(payload?.results) ? payload.results : []);
    } catch (error) {
      notify(error.message || "Unable to search locations.");
      setLocationResults([]);
    } finally {
      setLocationSearchBusy(false);
    }
  }, [locationQuery]);

  useEffect(() => {
    const bootTimer = window.setTimeout(() => {
      fetchDashboardData();
    }, 0);

    const dashboardTimer = window.setInterval(() => {
      fetchDashboardData();
    }, POLL_INTERVAL_MS);

    return () => {
      window.clearTimeout(bootTimer);
      window.clearInterval(dashboardTimer);
    };
  }, [fetchDashboardData, handleAuthExpired]);

  useEffect(() => {
    fetchSensorData();
    const interval = window.setInterval(() => {
      fetchSensorData();
    }, 3000);

    return () => window.clearInterval(interval);
  }, [fetchSensorData]);

  useEffect(() => {
    fetchSensorHistory();
    const interval = window.setInterval(() => {
      fetchSensorHistory();
    }, 30000);

    return () => window.clearInterval(interval);
  }, [fetchSensorHistory]);

  useEffect(() => {
    const eventSource = new EventSource(`${API_BASE}/panel/events`);
    let refreshTimer = 0;

    const scheduleRefresh = () => {
      window.clearTimeout(refreshTimer);
      refreshTimer = window.setTimeout(() => {
        fetchSensorData();
        fetchDashboardData();
      }, 120);
    };

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data || "{}");
        const eventType = String(payload?.type || "");
        if (
          [
            "emergency-alert-created",
            "emergency-status-updated",
            "emergency-deleted",
            "emergency-assigned",
            "worker-emergency-status-updated",
            "monitoring-alert-created",
          ].includes(eventType)
        ) {
          scheduleRefresh();
        }
      } catch {
        // Ignore malformed live events and continue polling.
      }
    };

    return () => {
      window.clearTimeout(refreshTimer);
      eventSource.close();
    };
  }, [fetchDashboardData, fetchSensorData]);

  useEffect(() => {
    if (!locationMenuOpen) return undefined;

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        closeLocationModal();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [closeLocationModal, locationMenuOpen]);

  useEffect(() => {
    if (
      (locationState.permission === "granted" || locationState.permission === "manual") &&
      locationState.latitude !== null &&
      locationState.latitude !== undefined &&
      locationState.longitude !== null &&
      locationState.longitude !== undefined
    ) {
      fetchLiveEnvironment(locationState);
      const timer = window.setInterval(() => fetchLiveEnvironment(locationState), 60000);
      return () => window.clearInterval(timer);
    }
    setLiveEnvironment(null);
    weatherSnapshotRef.current = null;
    return undefined;
  }, [fetchLiveEnvironment, locationState]);

  useEffect(() => {
    const updateBackToTopVisibility = () => {
      const scrollTop = window.scrollY || document.documentElement.scrollTop;
      const viewportHeight = window.innerHeight;
      const fullHeight = document.documentElement.scrollHeight;
      const nearBottom = scrollTop + viewportHeight >= fullHeight - 140;
      setShowBackToTopArrow(nearBottom && scrollTop > viewportHeight * 0.6);
    };

    updateBackToTopVisibility();
    window.addEventListener("scroll", updateBackToTopVisibility, { passive: true });
    window.addEventListener("resize", updateBackToTopVisibility);

    return () => {
      window.removeEventListener("scroll", updateBackToTopVisibility);
      window.removeEventListener("resize", updateBackToTopVisibility);
    };
  }, []);

  const latestAlertBySensor = useMemo(() => {
    const map = {};
    for (const alert of alerts) {
      if (!alert?.sensor_id || map[alert.sensor_id]) continue;
      map[alert.sensor_id] = alert;
    }
    return map;
  }, [alerts]);

  useEffect(() => {
    setResolvedAlertSeenAt((current) => {
      let changed = false;
      const next = { ...current };
      Object.entries(latestAlertBySensor).forEach(([sensorId, alert]) => {
        if (alert?.status === "Resolved") {
          if (!next[sensorId] || next[sensorId].alertId !== alert.id) {
            next[sensorId] = { alertId: alert.id, seenAt: Date.now() };
            changed = true;
          }
        } else if (next[sensorId]) {
          delete next[sensorId];
          changed = true;
        }
      });
      Object.keys(next).forEach((sensorId) => {
        if (!latestAlertBySensor[sensorId]) {
          delete next[sensorId];
          changed = true;
        }
      });
      return changed ? next : current;
    });
  }, [latestAlertBySensor]);

  const baseSensorData = useMemo(() => {
    if (!sensorData) return null;

    const merged = { ...sensorData };
    const validated = { ...merged };
    validated.temperature = validateRange(merged.temperature, -10, 60);
    validated.humidity = validateRange(merged.humidity, 0, 100);
    validated.air_smoke = validateRange(merged.air_smoke, 0, 500);
    validated.rain_percent = validateRange(merged.rain_percent, 0, 100);
    validated.flood_level = validateRange(merged.flood_level, 0, 100);
    validated.noise_level = validateRange(merged.noise_level, 0, 150);
    validated.bin_fill = validateRange(merged.bin_fill, 0, 100);
    validated.light_percent = validateRange(merged.light_percent, 0, 100);

    validated.air_status = Number.isFinite(validated.air_smoke) ? mapAirQualityStatus(validated.air_smoke) : "Good";
    validated.flood_status = Number.isFinite(validated.flood_level) ? mapFloodStatus(validated.flood_level) : "Safe";
    validated.noise_status = Number.isFinite(validated.noise_level) ? mapNoiseStatus(validated.noise_level) : "Safe";
    validated.bin_status = Number.isFinite(validated.bin_fill) ? mapBinStatus(validated.bin_fill) : "Normal";
    validated.light_status = Number.isFinite(validated.light_percent) ? mapLightStatus(validated.light_percent) : "Night Time - Lights ON";
    validated.rain_status = merged.rain_status || (Number.isFinite(validated.rain_percent) ? (validated.rain_percent > 75 ? "Heavy" : validated.rain_percent >= 35 ? "Moderate" : "Low") : "Low");
    validated.temp_status = Number.isFinite(validated.temperature) ? (merged.temp_status || "Live weather") : "Normal";

    return validated;
  }, [sensorData]);

  const latestHistoryValues = useMemo(() => getLatestHistoryValues(sensorHistory), [sensorHistory]);

  const effectiveSensorData = useMemo(() => {
    if (!baseSensorData) return null;
    const fallbackTimestamp = liveEnvironment?.last_updated || liveEnvironment?.timestamp || null;
    const resolved = {
      ...baseSensorData,
      temperature: baseSensorData.temperature ?? normalizeNullableNumber(liveEnvironment?.temperature),
      humidity: baseSensorData.humidity ?? normalizeNullableNumber(liveEnvironment?.humidity),
      air_smoke: baseSensorData.air_smoke ?? normalizeNullableNumber(liveEnvironment?.air_smoke),
      rain_percent: baseSensorData.rain_percent ?? normalizeNullableNumber(liveEnvironment?.rain_percent),
      flood_level: baseSensorData.flood_level ?? latestHistoryValues.flood_level ?? null,
      noise_level: baseSensorData.noise_level ?? latestHistoryValues.noise_level ?? null,
      light_percent: baseSensorData.light_percent ?? latestHistoryValues.light_percent ?? null,
      bin_fill: baseSensorData.bin_fill ?? latestHistoryValues.bin_fill ?? null,
      traffic_lane1: baseSensorData.traffic_lane1 ?? latestHistoryValues.traffic_lane1 ?? null,
      traffic_lane2: baseSensorData.traffic_lane2 ?? latestHistoryValues.traffic_lane2 ?? null,
      traffic_total: baseSensorData.traffic_total ?? latestHistoryValues.traffic_total ?? null,
      fire_smoke: baseSensorData.fire_smoke ?? latestHistoryValues.fire_smoke ?? null,
      parking_available: baseSensorData.parking_available ?? latestHistoryValues.parking_available ?? null,
      parking_a: baseSensorData.parking_a ?? latestHistoryValues.parking_a ?? null,
      parking_b: baseSensorData.parking_b ?? latestHistoryValues.parking_b ?? null,
      traffic_status: baseSensorData.traffic_status ?? latestHistoryValues.traffic_status ?? "Stable conditions",
      parking_status: baseSensorData.parking_status ?? latestHistoryValues.parking_status ?? "Stable conditions",
      fire_status: baseSensorData.fire_status ?? latestHistoryValues.fire_status ?? "Stable conditions",
      air_status:
        baseSensorData.air_status && baseSensorData.air_status !== "--"
          ? baseSensorData.air_status
          : (liveEnvironment?.air_status || baseSensorData.air_status),
      rain_status:
        baseSensorData.rain_status && baseSensorData.rain_status !== "--"
          ? baseSensorData.rain_status
          : (liveEnvironment?.rain_status || baseSensorData.rain_status),
      temp_status:
        baseSensorData.temp_status && baseSensorData.temp_status !== "--"
          ? baseSensorData.temp_status
          : (liveEnvironment?.temp_status || baseSensorData.temp_status),
      timestamp: baseSensorData.timestamp || latestHistoryValues.timestamp || fallbackTimestamp,
      last_updated: baseSensorData.last_updated || latestHistoryValues.last_updated || fallbackTimestamp,
    };
    resolved.noise_status =
      resolved.noise_status && resolved.noise_status !== "--"
        ? resolved.noise_status
        : (Number.isFinite(Number(resolved.noise_level)) ? mapNoiseStatus(Number(resolved.noise_level)) : "Safe");
    resolved.flood_status =
      resolved.flood_status && resolved.flood_status !== "--"
        ? resolved.flood_status
        : (Number.isFinite(Number(resolved.flood_level)) ? mapFloodStatus(Number(resolved.flood_level)) : "Safe");
    resolved.light_status =
      resolved.light_status && resolved.light_status !== "--"
        ? resolved.light_status
        : (Number.isFinite(Number(resolved.light_percent)) ? mapLightStatus(Number(resolved.light_percent)) : "Night Time - Lights ON");
    resolved.bin_status =
      resolved.bin_status && resolved.bin_status !== "--"
        ? resolved.bin_status
        : (Number.isFinite(Number(resolved.bin_fill)) ? mapBinStatus(Number(resolved.bin_fill)) : "Normal");
    return resolved;
  }, [baseSensorData, latestHistoryValues, liveEnvironment]);

  useEffect(() => {
    if (!hasLocationAccess) {
      setStreetLightIntensity(62);
      previousLightLdrRef.current = null;
      return;
    }

    const rawLdrValue = Number(effectiveSensorData?.light_percent);
    const isDayTime = Number.isFinite(rawLdrValue) ? rawLdrValue > STREET_LIGHT_DAY_THRESHOLD : true;

    if (isDayTime) {
      setStreetLightIntensity(62);
      previousLightLdrRef.current = rawLdrValue;
      return;
    }

    const previousLdrValue = previousLightLdrRef.current;
    const ambientShift = Number.isFinite(previousLdrValue) ? Math.abs(rawLdrValue - previousLdrValue) : 0;
    if (Number.isFinite(rawLdrValue) && (rawLdrValue < STREET_LIGHT_FAULT_LOW || rawLdrValue > STREET_LIGHT_FAULT_HIGH || ambientShift >= 35)) {
      setStreetLightIntensity(Number(clampNumber(rawLdrValue, 10, 99).toFixed(0)));
    } else {
      setStreetLightIntensity((current) => normalizeStreetLightIntensity(current) ?? 62);
    }

    previousLightLdrRef.current = rawLdrValue;
  }, [effectiveSensorData?.light_percent, hasLocationAccess]);

  const sensorCards = useMemo(
    () =>
      SENSOR_DEFINITIONS.map((sensor) => {
        if (!effectiveSensorData) {
          return {
            ...sensor,
            numericValue: 0,
            displayValue: formatNumber(0, sensor.unit),
            severity: "Safe",
            adviceLine: "System operating normally.",
            statusText: "Stable conditions",
            trendText: "Stable",
            publicUpdate: "System operating normally",
            commandGuidance: "Conditions are within a healthy range. Keep monitoring and maintain the current response posture.",
            priorityBand: "Stable conditions",
          };
        }
        const rawValue = sensor.getValue(effectiveSensorData);
        const hasValue = rawValue !== undefined && rawValue !== null && !Number.isNaN(Number(rawValue));
        const numericValue = hasValue ? Number(rawValue) : 0;
        const previousRow = sensorHistory.length > 1 ? sensorHistory[sensorHistory.length - 2] : {};
        const previousValue = Number(sensor.getValue(previousRow));
        const smartDetail = effectiveSensorData?.sensor_details?.[sensor.id];
        const severity = smartDetail?.severity
          ? smartDetail.severity
          : smartDetail?.status
          ? detailedStatusToSeverity(smartDetail.status)
          : (hasValue ? sensor.classify(numericValue, effectiveSensorData) : "Safe");
        return {
          ...sensor,
          numericValue,
          displayValue: formatNumber(numericValue, sensor.unit),
          severity,
          adviceLine: smartDetail?.current_situation || sensor.advice[severity],
          statusText: smartDetail?.current_situation || sensor.levels[severity] || "Stable conditions",
          trendText: smartDetail?.trend_label || smartDetail?.trend || trendLabel(numericValue, previousValue, sensor.id),
          publicUpdate: smartDetail?.public_update || "System operating normally",
          commandGuidance: smartDetail?.command_guidance || "Conditions are within a healthy range. Keep monitoring and maintain the current response posture.",
          priorityBand: smartDetail?.priority_band || "Stable conditions",
          messageText: "",
          statusDetail: "",
          liveReading: numericValue,
        };
      }),
    [effectiveSensorData, sensorHistory, streetLightIntensity]
  );

  const safetyOverview = useMemo(
    () =>
      sensorCards.reduce(
        (accumulator, sensor) => {
          accumulator[sensor.severity] += 1;
          return accumulator;
        },
        emptyCounts()
      ),
    [sensorCards]
  );

  const criticalSensors = useMemo(
    () => sensorCards.filter((sensor) => sensor.severity === "Danger").slice(0, 3),
    [sensorCards]
  );

  const snapshotSensorLists = useMemo(
    () => ({
      Danger: sensorCards.filter((sensor) => sensor.severity === "Danger"),
      Moderate: sensorCards.filter((sensor) => sensor.severity === "Moderate"),
      Safe: sensorCards.filter((sensor) => sensor.severity === "Safe"),
    }),
    [sensorCards]
  );

  const stackedSensorCards = useMemo(
    () =>
      sensorCards
        .slice(0, 11)
        .map((sensor) => ({
          id: sensor.id,
          title: sensor.label,
          shortCode: sensor.shortCode,
          description: sensor.adviceLine,
          value: sensor.displayValue,
          status: sensor.statusText,
          trend: sensor.trendText,
          severity: sensor.severity,
          freshness: freshnessLabel(effectiveSensorData?.timestamp),
          image: SENSOR_CARD_IMAGES[sensor.id] || SENSOR_CARD_IMAGES.air_smoke,
          currentSituation: sensor.statusText,
          publicUpdate: sensor.publicUpdate,
          commandGuidance: sensor.commandGuidance,
          priorityBand: sensor.priorityBand,
        })),
    [sensorCards, effectiveSensorData?.timestamp]
  );

  const referenceTimeMs = useMemo(() => {
    const sourceTimestamp = effectiveSensorData?.timestamp || sensorHistory[sensorHistory.length - 1]?.timestamp;
    const parsed = parseDashboardTimestamp(sourceTimestamp).getTime();
    return Number.isFinite(parsed) ? parsed : 0;
  }, [effectiveSensorData, sensorHistory]);

  const reportSectionDetails = useMemo(() => {
    const sortedComplaints = [...complaints].sort(
      (left, right) => new Date(right?.created_at || 0).getTime() - new Date(left?.created_at || 0).getTime()
    );
    const sortedAlerts = [...alerts].sort(
      (left, right) => new Date(right?.created_at || 0).getTime() - new Date(left?.created_at || 0).getTime()
    );

    const pendingComplaints = sortedComplaints.filter((issue) => {
      const status = String(issue?.status || "").toLowerCase();
      return status && status !== "resolved" && status !== "rejected";
    });
    const resolvedComplaints = sortedComplaints.filter(
      (issue) => String(issue?.status || "").toLowerCase() === "resolved"
    );
    const hotspotAlerts = sortedAlerts.filter((alert) => {
      const severity = String(alert?.severity || "").toLowerCase();
      const priority = String(alert?.priority || "").toLowerCase();
      return severity === "danger" || severity === "critical" || priority === "immediate" || priority === "critical";
    });
    const hotspotSensors = snapshotSensorLists.Danger;

    const complaintToCard = (issue, index, accent) => ({
      id: issue?.id || issue?.complaint_number || `complaint-${index}`,
      initials: getInitials(issue?.category || issue?.title || issue?.complaint_number || "UR"),
      name: issue?.complaint_number || issue?.title || "Submitted complaint",
      role: `${issue?.status || "Submitted"} • ${shortTimestamp(issue?.created_at)}`,
      quote: truncateText(issue?.description || issue?.title || issue?.category),
      tags: [
        { text: issue?.category || "General", type: "default" },
        { text: issue?.status || "Submitted", type: accent === "featured" ? "featured" : "default" },
      ],
      stats: [
        { icon: ClipboardList, text: issue?.category || "General" },
        { icon: Clock3, text: shortTimestamp(issue?.created_at) },
      ],
      avatarGradient: accent === "featured"
        ? "linear-gradient(135deg, #34d399, #14b8a6)"
        : "linear-gradient(135deg, #60a5fa, #4f46e5)",
    });

    const alertToCard = (alert, index) => ({
      id: alert?.id || `alert-${index}`,
      initials: getInitials(alert?.sensor_label || "HS"),
      name: alert?.sensor_label || "Critical hotspot",
      role: `${alert?.status || "Open"} • ${shortTimestamp(alert?.created_at)}`,
      quote: truncateText(
        alert?.note || `${alert?.severity || "Danger"} condition reported for ${alert?.sensor_label || "the monitored zone"}.`
      ),
      tags: [
        { text: alert?.severity || "Danger", type: "featured" },
        { text: alert?.priority || "Immediate", type: "default" },
      ],
      stats: [
        { icon: AlertTriangle, text: alert?.priority || "Immediate" },
        { icon: Clock3, text: shortTimestamp(alert?.created_at) },
      ],
      avatarGradient: "linear-gradient(135deg, #fb7185, #f97316)",
    });

    const sensorToHotspotCard = (sensor, index) => {
      const linkedAlert = hotspotAlerts.find((alert) => {
        const sensorLabel = String(sensor?.label || "").trim().toLowerCase();
        const alertLabel = String(alert?.sensor_label || "").trim().toLowerCase();
        return sensorLabel && alertLabel && sensorLabel === alertLabel;
      });

      return {
        id: sensor?.id || linkedAlert?.id || `hotspot-${index}`,
        initials: getInitials(sensor?.label || linkedAlert?.sensor_label || "HS"),
        name: sensor?.label || linkedAlert?.sensor_label || "Critical hotspot",
        role: `${sensor?.statusText || linkedAlert?.status || "Danger"} • ${freshnessLabel(effectiveSensorData?.timestamp)}`,
        quote: truncateText(
          linkedAlert?.note ||
            `${sensor?.label || "This field"} is currently in a danger state with a live reading of ${
              sensor?.displayValue ?? formatNumber(0, "")
            }. ${sensor?.adviceLine || "Immediate attention is recommended."}`
        ),
        tags: [
          { text: sensor?.severity || linkedAlert?.severity || "Danger", type: "featured" },
          { text: sensor?.trendText || linkedAlert?.priority || "Live hotspot", type: "default" },
        ],
        stats: [
          { icon: AlertTriangle, text: sensor?.displayValue ?? formatNumber(0, "") },
          { icon: Clock3, text: freshnessLabel(effectiveSensorData?.timestamp) },
        ],
        avatarGradient: "linear-gradient(135deg, #fb7185, #f97316)",
      };
    };

    const buildEmptyCard = (name, role, quote, gradient) => [
      {
        id: `${name}-empty`,
        initials: getInitials(name),
        name,
        role,
        quote,
        tags: [{ text: "0 items", type: "default" }],
        stats: [
          { icon: FileSearch, text: "Nothing submitted yet" },
          { icon: Clock3, text: "Live dashboard" },
        ],
        avatarGradient: gradient,
      },
    ];

    return {
      total: {
        count: stats.total_issues,
        title: "Total Reports",
        subtitle: "Every complaint you have submitted from this account.",
        icon: ClipboardList,
        items: sortedComplaints.length
          ? sortedComplaints.map((issue, index) => complaintToCard(issue, index, "default"))
          : buildEmptyCard(
              "No reports yet",
              "Submission history",
              "You have not submitted any complaint reports yet. Once you file a report, it will appear here with its latest status.",
              "linear-gradient(135deg, #94a3b8, #64748b)"
            ),
      },
      pending: {
        count: stats.pending,
        title: "Pending Review",
        subtitle: "Reports waiting for admin review or active field response.",
        icon: Clock3,
        items: pendingComplaints.length
          ? pendingComplaints.map((issue, index) => complaintToCard(issue, index, "default"))
          : buildEmptyCard(
              "No pending reports",
              "Review queue clear",
              "All of your submitted complaints have either been resolved or there are no reports waiting for review right now.",
              "linear-gradient(135deg, #38bdf8, #0f766e)"
            ),
      },
      resolved: {
        count: stats.resolved,
        title: "Resolved Issues",
        subtitle: "Reports that admin has already closed successfully.",
        icon: CheckCircle2,
        items: resolvedComplaints.length
          ? resolvedComplaints.map((issue, index) => complaintToCard(issue, index, "featured"))
          : buildEmptyCard(
              "No resolved issues",
              "Resolution tracker",
              "You do not have any resolved complaints yet. Finished cases will be listed here with their latest closure status.",
              "linear-gradient(135deg, #22c55e, #0f766e)"
            ),
      },
      hotspots: {
        count: hotspotSensors.length,
        title: "Critical Hotspots",
        subtitle: "Live danger-level fields detected in your selected area.",
        icon: ShieldAlert,
        items: hotspotSensors.length
          ? hotspotSensors.map((sensor, index) => sensorToHotspotCard(sensor, index))
          : buildEmptyCard(
              "No hotspot alerts",
              "Emergency queue",
              "No live danger-level hotspot is active in your selected area right now.",
              "linear-gradient(135deg, #fb7185, #ef4444)"
            ),
      },
    };
  }, [alerts, complaints, effectiveSensorData?.timestamp, snapshotSensorLists.Danger, stats.pending, stats.resolved, stats.total_issues]);

  const reportSummaryCards = useMemo(
    () => [
      {
        key: "total",
        title: reportSectionDetails.total.title,
        value: reportSectionDetails.total.count,
        description: "Open the full list of complaint reports you have filed.",
        icon: reportSectionDetails.total.icon,
      },
      {
        key: "pending",
        title: reportSectionDetails.pending.title,
        value: reportSectionDetails.pending.count,
        description: "See which reports still need review or action.",
        icon: reportSectionDetails.pending.icon,
      },
      {
        key: "resolved",
        title: reportSectionDetails.resolved.title,
        value: reportSectionDetails.resolved.count,
        description: "Review the cases that were closed successfully.",
        icon: reportSectionDetails.resolved.icon,
      },
      {
        key: "hotspots",
        title: reportSectionDetails.hotspots.title,
        value: reportSectionDetails.hotspots.count,
        description: "Check submitted emergency hotspot alerts and updates.",
        icon: reportSectionDetails.hotspots.icon,
      },
    ],
    [reportSectionDetails]
  );

  const refreshMonitoringState = useCallback(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleResolveMonitoringAlert = useCallback(async (alertId) => {
    setAdminActionBusy(true);
    try {
      const response = await api(`${API_BASE}/api/alerts/${alertId}`, {
        method: "PATCH",
        body: JSON.stringify({ resolve: true }),
      });
      if (!response.ok) {
        throw new Error("Unable to resolve alert");
      }
      notify("Alert resolved successfully.");
      refreshMonitoringState();
    } catch (error) {
      notify(error.message || "Unable to resolve alert");
    } finally {
      setAdminActionBusy(false);
    }
  }, [refreshMonitoringState]);

  const handleAssignMonitoringAlert = useCallback(async (alertId) => {
    setAdminActionBusy(true);
    try {
      const response = await api(`${API_BASE}/api/alerts/${alertId}`, {
        method: "PATCH",
        body: JSON.stringify({ assigned_department: "Emergency Operations" }),
      });
      if (!response.ok) {
        throw new Error("Unable to assign department");
      }
      notify("Department assigned successfully.");
      refreshMonitoringState();
    } catch (error) {
      notify(error.message || "Unable to assign department");
    } finally {
      setAdminActionBusy(false);
    }
  }, [refreshMonitoringState]);

  const handleForceResetLocation = useCallback(async () => {
    setAdminActionBusy(true);
    try {
      const response = await api(`${API_BASE}/api/sensors/reset`, {
        method: "POST",
        body: JSON.stringify({
          location: selectedLocation || locationState.label,
          latitude: locationState.latitude,
          longitude: locationState.longitude,
        }),
      });
      if (!response.ok) {
        throw new Error("Unable to reset sensor state");
      }
      notify("Sensor location reset successfully.");
      refreshMonitoringState();
    } catch (error) {
      notify(error.message || "Unable to reset sensor state");
    } finally {
      setAdminActionBusy(false);
    }
  }, [locationState.label, locationState.latitude, locationState.longitude, refreshMonitoringState, selectedLocation]);

  const handleProtectedNavigation = useCallback(
    (route) => {
      if (hasLocationAccess) {
        navigate(route);
        return;
      }
      setPendingRoute(route);
      setShowLocationPopup(true);
      notify("Allow location access to continue.");
    },
    [hasLocationAccess, navigate]
  );

  const handleEmergencyReport = useCallback(
    async (sensorCard) => {
      if (!hasLocationAccess) {
        setShowLocationPopup(true);
        return {
          kind: "duplicate",
          message: "Allow location access first to report this emergency.",
        };
      }

      const latestAlert = latestAlertBySensor[sensorCard.id];
      if (latestAlert && (latestAlert.status === "Open" || latestAlert.status === "In Progress")) {
        return {
          kind: "duplicate",
          message: `${sensorCard.title} report already submitted. Admin is already handling this emergency.`,
        };
      }

      try {
        const response = await api(`${API_BASE}/user/emergency-alerts`, {
          method: "POST",
          body: JSON.stringify({
            sensor_id: sensorCard.id,
            sensor_label: sensorCard.title,
            severity: "Danger",
            value: sensorCard.value,
            location: getSafeLocationLabel(locationState.label),
            latitude: locationState.latitude,
            longitude: locationState.longitude,
            note:
              sensorCard.id === "light_percent"
                ? `Reported by citizen for street-light failure at ${new Date().toLocaleString()}`
                : `Reported by citizen from dashboard at ${new Date().toLocaleString()}`,
          }),
        });

        if (response.status === 401) {
          handleAuthExpired();
          return {
            kind: "duplicate",
            message: "Your session expired. Please sign in again to send emergency reports.",
          };
        }

        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          return {
            kind: "duplicate",
            message: payload?.detail || "Unable to submit the emergency report right now.",
          };
        }

        fetchDashboardData();
        return {
          kind: "submitted",
          message:
            sensorCard.id === "light_percent"
              ? "Street light fault reported successfully. Maintenance and admin teams have been notified."
              : `${sensorCard.title} emergency reported successfully to the relevant admin domain. Authorities have been notified and will address the issue as soon as possible.`,
        };
      } catch {
        return {
          kind: "duplicate",
          message: "Unable to reach the server right now. Please try again shortly.",
        };
      }
    },
    [fetchDashboardData, handleAuthExpired, hasLocationAccess, latestAlertBySensor]
  );

  useEffect(() => {
    const hasDanger = sensorCards.some((sensor) => sensor.severity === "Danger");
    if (hasDanger && !alertTriggered) {
      setAlertTriggered(true);
    }
    if (!hasDanger && alertTriggered) {
      setAlertTriggered(false);
    }
  }, [alertTriggered, sensorCards]);

  const handleFocusEmergencyCard = useCallback((sensorId) => {
    setFocusedEmergencyCardId(sensorId);
    setFocusEmergencyRequestKey((current) => current + 1);
    setActiveSnapshotCategory("");
  }, []);

  return (
    <div className="home-page">
      <header className="hero">
        {showLocationPopup ? (
          <div className="location-modal-backdrop">
            <div className="location-modal-card" role="dialog" aria-modal="true" aria-labelledby="location-modal-title">
              <p className="location-modal-eyebrow">Location Access</p>
              <h2 id="location-modal-title">Allow location</h2>
              <p>
                Allow your location to show your current area at the top and fetch live environmental conditions for where you are.
              </p>
              <div className="location-modal-actions">
                <button type="button" className="allow" onClick={requestBrowserLocation}>
                  Allow
                </button>
                <button
                  type="button"
                  className="delay"
                  onClick={() => {
                    globalThis.__urbanSentinelLocationPromptHandled = true;
                    setShowLocationPopup(false);
                  }}
                >
                  Deny
                </button>
              </div>
            </div>
          </div>
        ) : null}
        <nav className="hero-nav">
          <div className="hero-nav-left">
            <strong>Urban Sentinel</strong>
            <button
              type="button"
              className={`location-badge ${locationMenuOpen ? "active" : ""}`}
              onClick={openLocationModal}
              aria-expanded={locationMenuOpen}
              aria-haspopup="dialog"
              aria-label="Select location"
            >
              <span aria-hidden="true" />
              <small>{getSafeLocationLabel(locationState.label)}</small>
            </button>
          </div>
          <div className="hero-nav-actions">
            <button
              type="button"
              className="profile-chip"
              onClick={() => setMenuOpen((state) => !state)}
              aria-label="Open account menu"
              aria-expanded={menuOpen}
              aria-controls="user-menu-drawer"
            >
              <span>{profileInitial || "U"}</span>
            </button>
          </div>
        </nav>

        <div className="hero-content hero-layout">
          <div className="hero-copy">
            <p className="eyebrow">Citizen Safety Dashboard</p>
            <h1>Live City Conditions Center</h1>
            <p>
              Monitor every key environment signal in one place, raise high-priority danger alerts to admin,
              and review short-term and monthly condition trends before stepping out.
            </p>
            <p className="last-sync">{heroStatusMessage}</p>
            <div className="hero-actions">
              <button type="button" className="primary-btn" onClick={() => handleProtectedNavigation("/report")}> 
                Report an Issue
              </button>
              <button type="button" className="secondary-btn" onClick={() => handleProtectedNavigation("/track")}> 
                Track Complaint
              </button>
            </div>
          </div>
          <aside
            className="hero-spotlight"
          >
            <span className="spotlight-label">Area Snapshot</span>
            <button
              type="button"
              className="hero-spotlight-location-trigger"
              onClick={openLocationModal}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  openLocationModal();
                }
              }}
              aria-haspopup="dialog"
              aria-expanded={locationMenuOpen}
              aria-label="Choose location"
            >
              <strong>{getSafeLocationLabel(locationState.label)}</strong>
            </button>
            <p>
              {criticalSensors.length
                ? `${criticalSensors.length} hotspot${criticalSensors.length > 1 ? "s" : ""} need urgent action right now.`
                : "No danger-level signals detected right now."}
            </p>
            <div className="spotlight-metrics">
              <button
                type="button"
                className={`snapshot-button ${activeSnapshotCategory === "Danger" ? "active" : ""}`}
                aria-pressed={activeSnapshotCategory === "Danger"}
                onClick={(event) => {
                  event.stopPropagation();
                  setActiveSnapshotCategory((current) => (current === "Danger" ? "" : "Danger"))
                }}
              >
                <span>Danger</span>
                <strong>{safetyOverview.Danger}</strong>
              </button>
              <button
                type="button"
                className={`snapshot-button ${activeSnapshotCategory === "Moderate" ? "active" : ""}`}
                aria-pressed={activeSnapshotCategory === "Moderate"}
                onClick={(event) => {
                  event.stopPropagation();
                  setActiveSnapshotCategory((current) => (current === "Moderate" ? "" : "Moderate"))
                }}
              >
                <span>Moderate</span>
                <strong>{safetyOverview.Moderate}</strong>
              </button>
              <button
                type="button"
                className={`snapshot-button ${activeSnapshotCategory === "Safe" ? "active" : ""}`}
                aria-pressed={activeSnapshotCategory === "Safe"}
                onClick={(event) => {
                  event.stopPropagation();
                  setActiveSnapshotCategory((current) => (current === "Safe" ? "" : "Safe"))
                }}
              >
                <span>Safe</span>
                <strong>{safetyOverview.Safe}</strong>
              </button>
            </div>
          </aside>
        </div>
        <p className="hero-background-text" aria-hidden="true">
          Live City Conditions
        </p>
      </header>
      <main>
        <section className="stats-grid">
          {reportSummaryCards.map((card, index) => {
            const Icon = card.icon;
            return (
              <button
                key={card.key}
                type="button"
                className="report-stat-card"
                onClick={() => setReportDetailModal(reportSectionDetails[card.key])}
              >
                <div className="report-stat-card__glow" />
                <div className="report-stat-card__top">
                  <span className="report-stat-card__icon">
                    <Icon size={18} strokeWidth={2.1} />
                  </span>
                  <span className="report-stat-card__index">0{index + 1}</span>
                </div>
                <h3>{card.value}</h3>
                <p>{card.title}</p>
                <small>{card.description}</small>
              </button>
            );
          })}
        </section>

        <section className="status-ribbon">
          {criticalSensors.length ? (
            criticalSensors.map((sensor) => (
              <button
                key={sensor.id}
                type="button"
                className="status-pill danger hotspot-link"
                onClick={() => handleFocusEmergencyCard(sensor.id)}
              >
                <strong>{sensor.label}</strong>
                <span>{sensor.displayValue}</span>
              </button>
            ))
          ) : (
            <article className="status-pill safe">
              <strong>System outlook</strong>
              <span>All monitored signals are below danger level</span>
            </article>
          )}
        </section>

        <section className="scroll-demo-shell">
            <StackedCards
              cards={stackedSensorCards}
              locationLabel={
                hasLocationAccess ? getSafeLocationLabel(locationState.label) : "Location permission required"
              }
            lastUpdated={hasLocationAccess ? formatTimestamp(effectiveSensorData?.timestamp) : "Live now"}
            onEmergencyReport={handleEmergencyReport}
            focusCardId={focusedEmergencyCardId}
            focusRequestKey={focusEmergencyRequestKey}
          />
        </section>

        <section className="summary-panel">
          <EnvironmentSummary />
        </section>

        {hasAdminSession ? (
          <section className="admin-panel-shell">
            <AdminControlPanel
              alerts={monitoringAlerts}
              loading={adminActionBusy}
              onResolve={handleResolveMonitoringAlert}
              onAssign={handleAssignMonitoringAlert}
              onForceReset={handleForceResetLocation}
              selectedLocationLabel={selectedLocation || locationState.label}
            />
          </section>
        ) : null}

        <section className="history-panel">
          <IncidentReportMiddle
            currentDangerCount={safetyOverview.Danger}
            currentModerateCount={safetyOverview.Moderate}
            currentSafeCount={safetyOverview.Safe}
            selectedLocationLabel={selectedLocation}
            latitude={locationState.latitude}
            longitude={locationState.longitude}
          />
        </section>
      </main>

      {showBackToTopArrow ? (
        <button
          type="button"
          className="back-to-top-arrow"
          aria-label="Scroll back to top"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        >
          <ChevronUp size={20} />
        </button>
      ) : null}

      {locationMenuOpen ? (
        <div className="location-picker-modal-shell" role="dialog" aria-modal="true" aria-labelledby="location-picker-title">
          <div className="location-picker-modal-backdrop" onClick={closeLocationModal} />
          <section className="location-picker-modal-card">
            <header className="location-picker-modal-head">
              <div>
                <p>Location</p>
                <h3 id="location-picker-title">Choose your live area</h3>
              </div>
              <button type="button" onClick={closeLocationModal} aria-label="Close location picker">
                <X size={18} />
              </button>
            </header>
            <div className="location-picker-modal-body">
              <button type="button" className="location-picker-live-btn" onClick={requestBrowserLocation}>
                Use live location
              </button>
              <div className="location-picker-manual">
                <label htmlFor="location-picker-input">Search manually</label>
                <div className="location-search-row">
                  <input
                    id="location-picker-input"
                    type="text"
                    value={locationQuery}
                    onChange={(event) => setLocationQuery(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        event.preventDefault();
                        searchLocation();
                      }
                    }}
                    placeholder="Search city or area"
                    aria-label="Search city or area"
                  />
                  <button type="button" onClick={searchLocation} disabled={locationSearchBusy}>
                    {locationSearchBusy ? "..." : "Search"}
                  </button>
                </div>
              </div>
              {locationState.permission === "manual" && locationState.label ? (
                <div className="location-results">
                  <button type="button" className="location-choice selected">
                    {getSafeLocationLabel(locationState.label)}
                  </button>
                </div>
              ) : null}
              {locationResults.length ? (
                <div className="location-results">
                  {locationResults.map((result) => (
                    <button
                      key={`${result.latitude}-${result.longitude}-${result.label}`}
                      type="button"
                      className="location-choice"
                      onClick={() => {
                        globalThis.__urbanSentinelLocationPromptHandled = true;
                        persistLocationState({
                          permission: "manual",
                          latitude: result.latitude,
                          longitude: result.longitude,
                          label: result.label,
                        });
                        setLocationResults([]);
                        setLocationQuery("");
                        closeLocationModal();
                      }}
                    >
                      {result.label}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </section>
        </div>
      ) : null}

      {menuOpen ? <button type="button" className="menu-drawer-backdrop" aria-label="Close menu" onClick={() => setMenuOpen(false)} /> : null}

      {reportDetailModal && (
        <div className="report-modal-shell" role="dialog" aria-modal="true">
          <div className="report-modal-backdrop" onClick={() => setReportDetailModal(null)} />
          <section className="report-modal-card">
            <header className="report-modal-head">
              <div>
                <p>{reportDetailModal.title}</p>
                <h3>{reportDetailModal.subtitle}</h3>
              </div>
              <button type="button" onClick={() => setReportDetailModal(null)} aria-label="Close report details">
                <X size={18} />
              </button>
            </header>
            <div className="report-modal-meta">
              <span>{reportDetailModal.count} items</span>
              <span>Swipe or tap dots to browse details</span>
            </div>
            <TestimonialStack testimonials={reportDetailModal.items} visibleBehind={2} />
          </section>
        </div>
      )}

      {activeSnapshotCategory ? (
        <div className="report-modal-shell" role="dialog" aria-modal="true">
          <div className="report-modal-backdrop" onClick={() => setActiveSnapshotCategory("")} />
          <section className="report-modal-card snapshot-modal-card">
            <header className="report-modal-head">
              <div>
                <p>Area Snapshot</p>
                <h3>{activeSnapshotCategory} fields in the current zone</h3>
              </div>
              <button type="button" onClick={() => setActiveSnapshotCategory("")} aria-label="Close snapshot details">
                <X size={18} />
              </button>
            </header>
            <div className="report-modal-meta">
              <span>{snapshotSensorLists[activeSnapshotCategory].length} fields</span>
              <span>Live classification based on the latest sensor readings</span>
            </div>
            <div className="snapshot-list-panel snapshot-list-panel--modal">
              <p className="snapshot-list-title">{activeSnapshotCategory} fields</p>
              <div className="snapshot-list-rows">
                {snapshotSensorLists[activeSnapshotCategory].length ? (
                  snapshotSensorLists[activeSnapshotCategory].map((sensor) => (
                    <div key={sensor.id} className="snapshot-list-row">
                      <div>
                        <strong>{sensor.label}</strong>
                        <span>{sensor.displayValue}</span>
                      </div>
                      {activeSnapshotCategory === "Danger" ? (
                        <button
                          type="button"
                          onClick={() => handleFocusEmergencyCard(sensor.id)}
                        >
                          View field
                        </button>
                      ) : null}
                    </div>
                  ))
                ) : (
                  <p className="snapshot-empty">No {activeSnapshotCategory.toLowerCase()} fields right now.</p>
                )}
              </div>
            </div>
          </section>
        </div>
      ) : null}

      {menuOpen && (
        <aside className="menu-drawer" id="user-menu-drawer" aria-label="User menu">
          <header>
            <h3>User Menu</h3>
            <button type="button" onClick={() => setMenuOpen(false)}>Close</button>
          </header>

          <section>
            <h4>Account Details</h4>
            <p>{userProfile?.full_name || "Citizen"}</p>
            <p>{userProfile?.email || "No email"}</p>
            <p>{userProfile?.phone || "No phone"}</p>
          </section>

          <section>
            <h4>Emergency Alerts Sent</h4>
            <div className="scroll-list">
              {alerts.length ? (
                alerts.slice(0, 8).map((alert) => (
                  <article key={alert.id}>
                    <strong>{alert.sensor_label}</strong>
                    <p>{alert.severity} | {alert.priority}</p>
                    <small>{formatTimestamp(alert.created_at)}</small>
                  </article>
                ))
              ) : (
                <p>No emergency alerts yet.</p>
              )}
            </div>
          </section>

          <section>
            <h4>Your Complaints</h4>
            <div className="scroll-list">
              {complaints.length ? (
                complaints.slice(0, 8).map((issue) => (
                  <article key={issue.id}>
                    <strong>{issue.complaint_number}</strong>
                    <p>{issue.title}</p>
                    <small>{issue.status}</small>
                  </article>
                ))
              ) : (
                <p>No complaints found.</p>
              )}
            </div>
          </section>

          <button
            type="button"
            className="logout-btn"
            onClick={() => {
              clearAuthSession();
              window.location.href = "/login";
            }}
          >
            Logout
          </button>
        </aside>
      )}

      {feedback && <div className="feedback-toast" role="status" aria-live="polite">{feedback}</div>}
    </div>
  );
}
