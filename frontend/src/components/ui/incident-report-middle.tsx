"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/services/api";
import { API_BASE } from "@/services/apiBase";
import { motion } from "framer-motion";
import { AlertTriangle, CalendarDays, Clock3, ShieldAlert } from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { cn } from "@/lib/utils";

type RangeMode = "5m" | "30m" | "1d" | "custom";

type IncidentApiPoint = {
  timestamp: string;
  danger_count: number;
  moderate_count: number;
  safe_count: number;
  incident_count: number;
};

type IncidentApiResponse = {
  range_key: RangeMode;
  window_label: string;
  bucket_minutes: number;
  count: number;
  total_samples: number;
  all_samples?: number;
  critical_incidents: number;
  danger_incidents: number;
  moderate_incidents: number;
  safe_incidents: number;
  monitored_sensor_total?: number;
  system_status: string;
  selected_date?: string | null;
  window_start?: string | null;
  window_end?: string | null;
  data: IncidentApiPoint[];
};

type ChartPoint = {
  timestamp: string;
  time: string;
  danger: number;
  moderate: number;
  safe: number;
  total: number;
};

type IncidentSummaryCounts = {
  danger: number;
  moderate: number;
  safe: number;
  total: number;
};

interface IncidentReportCardProps {
  currentDangerCount?: number;
  currentModerateCount?: number;
  currentSafeCount?: number;
  isDarkMode?: boolean;
  selectedLocationLabel?: string;
  latitude?: number | null;
  longitude?: number | null;
}

const INCIDENT_REFRESH_MS = 10000;
const REPORT_RANGE_TO_API: Record<Exclude<RangeMode, "custom">, string> = {
  "5m": "5min",
  "30m": "30min",
  "1d": "1day",
};

const RANGE_OPTIONS: Array<{ value: RangeMode; label: string }> = [
  { value: "5m", label: "Last 5 Min" },
  { value: "30m", label: "Last 30 Min" },
  { value: "1d", label: "Last 1 Day" },
  { value: "custom", label: "Custom Date" },
];

const EMPTY_RESPONSE: IncidentApiResponse = {
  range_key: "30m",
  window_label: "Last 30 Minutes",
  bucket_minutes: 5,
  count: 0,
  total_samples: 0,
  all_samples: 0,
  critical_incidents: 0,
  danger_incidents: 0,
  moderate_incidents: 0,
  safe_incidents: 0,
  monitored_sensor_total: 0,
  system_status: "Stable",
  selected_date: null,
  window_start: null,
  window_end: null,
  data: [],
};

function todayIsoDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDateLabel(value: string) {
  if (!value) return "Select date";
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return "Select date";
  return parsed.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function formatAxisTime(value: string, rangeKey: RangeMode) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "0:00";
  }
  if (rangeKey === "1d" || rangeKey === "custom") {
    return parsed.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  }
  return parsed.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatWindowSpan(start?: string | null, end?: string | null) {
  if (!start || !end) return "Live range selected";
  const startDate = new Date(start);
  const endDate = new Date(end);
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
    return "Live range selected";
  }
  const dateLabel = startDate.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
  const timeLabel = `${startDate.toLocaleTimeString("en-IN", {
    hour: "numeric",
    minute: "2-digit",
  })} - ${endDate.toLocaleTimeString("en-IN", {
    hour: "numeric",
    minute: "2-digit",
  })}`;
  return `${dateLabel} | ${timeLabel}`;
}

function buildChartData(rows: IncidentApiPoint[], rangeKey: RangeMode): ChartPoint[] {
  return rows.map((item) => ({
    timestamp: item.timestamp,
    time: formatAxisTime(item.timestamp, rangeKey),
    danger: Number(item.danger_count || 0),
    moderate: Number(item.moderate_count || 0),
    safe: Number(item.safe_count || 0),
    total: Number(item.incident_count || 0),
  }));
}

function buildTimelineSummary(rows: ChartPoint[], rangeKey: RangeMode) {
  const maxItems = rangeKey === "5m" ? 6 : rangeKey === "30m" ? 6 : 8;
  return rows.slice(-maxItems);
}

function buildSummaryCounts(rows: ChartPoint[]): IncidentSummaryCounts {
  const latestNonZero = [...rows].reverse().find((item) => item.total > 0);
  if (!latestNonZero) {
    return { danger: 0, moderate: 0, safe: 0, total: 0 };
  }
  return {
    danger: latestNonZero.danger,
    moderate: latestNonZero.moderate,
    safe: latestNonZero.safe,
    total: latestNonZero.total,
  };
}

function buildLiveSummaryCounts(danger: number, moderate: number, safe: number): IncidentSummaryCounts {
  const safeDanger = Number.isFinite(danger) ? danger : 0;
  const safeModerate = Number.isFinite(moderate) ? moderate : 0;
  const safeSafe = Number.isFinite(safe) ? safe : 0;
  return {
    danger: safeDanger,
    moderate: safeModerate,
    safe: safeSafe,
    total: safeDanger + safeModerate + safeSafe,
  };
}

function buildEmptyChartData(rangeKey: RangeMode): ChartPoint[] {
  const points = rangeKey === "1d" || rangeKey === "custom" ? 4 : 6;
  const stepMinutes = rangeKey === "5m" ? 1 : rangeKey === "30m" ? 5 : 60;
  const end = new Date();
  return Array.from({ length: points }).map((_, index) => {
    const timestamp = new Date(end.getTime() - (points - index - 1) * stepMinutes * 60 * 1000).toISOString();
    return {
      timestamp,
      time: formatAxisTime(timestamp, rangeKey),
      danger: 0,
      moderate: 0,
      safe: 0,
      total: 0,
    };
  });
}

function buildCacheKey({
  range,
  selectedDate,
  selectedLocationLabel,
  latitude,
  longitude,
}: {
  range: RangeMode;
  selectedDate: string;
  selectedLocationLabel?: string;
  latitude?: number | null;
  longitude?: number | null;
}) {
  return JSON.stringify({
    range,
    selectedDate: range === "custom" ? selectedDate : "",
    selectedLocationLabel: selectedLocationLabel || "",
    latitude: latitude ?? null,
    longitude: longitude ?? null,
  });
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) {
    return null;
  }

  const lookup = (key: string) => payload.find((entry: any) => entry.dataKey === key)?.value ?? 0;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white/95 p-3 shadow-[0_16px_40px_rgba(15,23,42,0.12)] backdrop-blur">
      <p className="text-sm font-semibold text-slate-900">{label}</p>
      <div className="mt-2 space-y-1 text-sm">
        <p className="text-red-500">Danger: {lookup("danger")}</p>
        <p className="text-amber-500">Moderate: {lookup("moderate")}</p>
        <p className="text-emerald-500">Safe: {lookup("safe")}</p>
      </div>
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="grid h-[300px] gap-3">
      <div className="h-6 w-40 animate-pulse rounded-full bg-slate-200" />
      <div className="flex-1 animate-pulse rounded-[1.5rem] bg-slate-200/80" />
      <div className="grid grid-cols-4 gap-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-4 animate-pulse rounded-full bg-slate-200" />
        ))}
      </div>
    </div>
  );
}

export function IncidentReportMiddle({
  currentDangerCount = 0,
  currentModerateCount = 0,
  currentSafeCount = 0,
  isDarkMode = false,
  selectedLocationLabel,
  latitude = null,
  longitude = null,
}: IncidentReportCardProps) {
  const [selectedRange, setSelectedRange] = useState<RangeMode>("30m");
  const [selectedDate, setSelectedDate] = useState(todayIsoDate());
  const [incidentPayload, setIncidentPayload] = useState<IncidentApiResponse>(EMPTY_RESPONSE);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const cacheRef = useRef<Map<string, IncidentApiResponse>>(new Map());
  const refreshInFlightRef = useRef(false);

  const cacheKey = useMemo(
    () =>
      buildCacheKey({
        range: selectedRange,
        selectedDate,
        selectedLocationLabel,
        latitude,
        longitude,
      }),
    [latitude, longitude, selectedDate, selectedLocationLabel, selectedRange],
  );

  useEffect(() => {
    let active = true;

    const fetchIncidents = async (preferFresh = false, silent = false) => {
      if (refreshInFlightRef.current) {
        return;
      }
      const cached = cacheRef.current.get(cacheKey);
      if (cached && !preferFresh) {
        setIncidentPayload(cached);
        setError("");
        setLoading(false);
        return;
      }

      refreshInFlightRef.current = true;
      if (silent) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError("");

      try {
        const params = new URLSearchParams({ range: selectedRange });

        if (selectedRange === "custom") {
          params.set("date", selectedDate);
        }
        if (selectedLocationLabel && (latitude === null || longitude === null)) {
          params.set("location", selectedLocationLabel);
        }
        if (latitude !== null && latitude !== undefined) {
          params.set("latitude", String(latitude));
        }
        if (longitude !== null && longitude !== undefined) {
          params.set("longitude", String(longitude));
        }

        const endpoint =
          selectedRange === "custom"
            ? `${API_BASE}/api/incidents?${params.toString()}`
            : `${API_BASE}/reports?${new URLSearchParams({ range: REPORT_RANGE_TO_API[selectedRange] }).toString()}`;
        const response = await api(endpoint);
        const payload = await response.json().catch(() => ({}));

        if (!response.ok) {
          throw new Error(payload?.detail || "Unable to retrieve data. Please try again later.");
        }

        if (!active) {
          return;
        }

        const normalizedPayload: IncidentApiResponse = {
          ...EMPTY_RESPONSE,
          ...payload,
          data: Array.isArray(payload?.data) ? payload.data : [],
        };

        cacheRef.current.set(cacheKey, normalizedPayload);
        setIncidentPayload(normalizedPayload);
      } catch (fetchError: any) {
        if (!active) {
          return;
        }
        setError(fetchError?.message || "Unable to retrieve data. Please try again later.");
      } finally {
        refreshInFlightRef.current = false;
        if (active) {
          if (silent) {
            setRefreshing(false);
          } else {
            setLoading(false);
          }
        }
      }
    };

    fetchIncidents();

    if (selectedRange !== "custom") {
      (["5m", "30m", "1d"] as RangeMode[]).forEach((rangeValue) => {
        if (rangeValue === "custom") return;
        const preloadKey = buildCacheKey({
          range: rangeValue,
          selectedDate,
          selectedLocationLabel,
          latitude,
          longitude,
        });
        if (cacheRef.current.has(preloadKey)) return;
        const preloadParams = new URLSearchParams({ range: REPORT_RANGE_TO_API[rangeValue] });
        api(`${API_BASE}/reports?${preloadParams.toString()}`)
          .then((response) => response.json().catch(() => ({})))
          .then((payload) => {
            const normalizedPayload: IncidentApiResponse = {
              ...EMPTY_RESPONSE,
              ...payload,
              data: Array.isArray(payload?.data) ? payload.data : [],
            };
            cacheRef.current.set(preloadKey, normalizedPayload);
          })
          .catch(() => undefined);
      });
    }

    const interval = window.setInterval(() => {
      fetchIncidents(true, true);
    }, INCIDENT_REFRESH_MS);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [cacheKey, latitude, longitude, selectedDate, selectedLocationLabel, selectedRange]);

  const chartData = useMemo(
    () => buildChartData(incidentPayload.data, incidentPayload.range_key || selectedRange),
    [incidentPayload.data, incidentPayload.range_key, selectedRange],
  );
  const liveSummaryCounts = useMemo(
    () => buildLiveSummaryCounts(currentDangerCount, currentModerateCount, currentSafeCount),
    [currentDangerCount, currentModerateCount, currentSafeCount],
  );
  const normalizedChartData = useMemo(() => {
    if (!chartData.length) {
      return chartData;
    }
    const latestIndex = chartData.length - 1;
    const next = [...chartData];
    next[latestIndex] = {
      ...next[latestIndex],
      danger: liveSummaryCounts.danger,
      moderate: liveSummaryCounts.moderate,
      safe: liveSummaryCounts.safe,
      total: liveSummaryCounts.total,
    };
    return next;
  }, [chartData, liveSummaryCounts]);
  const fallbackChartData = useMemo(() => buildEmptyChartData(incidentPayload.range_key || selectedRange), [incidentPayload.range_key, selectedRange]);
  const hasChartData = normalizedChartData.some((item) => item.total > 0 || item.danger > 0 || item.moderate > 0 || item.safe > 0);
  const visibleChartData = hasChartData ? normalizedChartData : fallbackChartData;
  const timelineSummary = useMemo(
    () => buildTimelineSummary(visibleChartData, incidentPayload.range_key || selectedRange),
    [incidentPayload.range_key, selectedRange, visibleChartData],
  );
  const summaryCounts = useMemo(() => {
    if (selectedRange === "custom") {
      return buildSummaryCounts(normalizedChartData);
    }
    return liveSummaryCounts;
  }, [liveSummaryCounts, normalizedChartData, selectedRange]);
  const isCustomRange = selectedRange === "custom";
  const emptyMessage = isCustomRange
    ? "No incident data available for the selected date."
    : "System is operating normally. No incidents detected.";
  const criticalBgOpacity = isDarkMode ? "bg-[rgb(232,64,69)]/40" : "bg-red-100";
  const totalBgOpacity = isDarkMode ? "bg-[rgb(64,229,209)]/40" : "bg-teal-100";

  const insightRows = [
    {
      title: "System Status",
      value: incidentPayload.system_status,
      icon: ShieldAlert,
      type: "critical" as const,
    },
    {
      title: "Monitoring Window",
      value: formatWindowSpan(incidentPayload.window_start, incidentPayload.window_end),
      icon: Clock3,
      type: "improvement" as const,
    },
    {
      title: "Historical Date",
      value: isCustomRange ? formatDateLabel(selectedDate) : "Live range selected",
      icon: CalendarDays,
      type: "improvement" as const,
    },
  ];

  return (
    <div
      className={cn(
        "flex w-full min-w-0 max-w-full flex-col justify-between overflow-hidden rounded-[clamp(1.25rem,2vw,2rem)] bg-white text-gray-900 shadow-[0_28px_60px_rgba(15,23,42,0.08)]",
        "dark:bg-black dark:text-white",
      )}
    >
      <div className="flex min-w-0 flex-col gap-5 px-[clamp(1rem,2vw,1.75rem)] pb-4 pt-6">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div className="space-y-2">
            <h3 className="text-[clamp(1.5rem,3vw,2rem)] font-bold tracking-tight">Incident Report</h3>
            <p className="text-[clamp(0.875rem,1.2vw,1rem)] text-slate-500">
              Monitor recent incidents and system activity across your selected time range.
            </p>
          </div>

          <div className="flex flex-col items-start gap-3">
            <div className="flex w-full flex-wrap gap-2">
              {RANGE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setSelectedRange(option.value)}
                  className={cn(
                    "rounded-full border px-4 py-2 text-sm font-medium transition-colors",
                    selectedRange === option.value
                      ? "border-slate-900 bg-slate-900 text-white"
                      : "border-slate-300 bg-slate-50 text-slate-700 hover:bg-slate-100",
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>

            {isCustomRange ? (
              <label className="flex w-full flex-wrap items-center gap-3 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-700 sm:w-auto">
                <CalendarDays className="h-4 w-4 text-slate-500" />
                <input
                  type="date"
                  value={selectedDate}
                  max={todayIsoDate()}
                  onChange={(event) => setSelectedDate(event.target.value)}
                  className="bg-transparent outline-none"
                />
                <span className="font-medium text-slate-500">{formatDateLabel(selectedDate)}</span>
              </label>
            ) : null}
          </div>
        </div>
      </div>

      <div className="min-w-0 px-[clamp(1rem,2vw,1.75rem)] pb-3">
        {error ? (
          <div className="mb-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-600">
            Unable to retrieve data. Please try again later.
          </div>
        ) : null}

        <div className="min-w-0 overflow-hidden rounded-[1.75rem] bg-slate-50/80 p-[clamp(0.75rem,1.5vw,1rem)]">
          {!hasChartData && loading ? (
            <ChartSkeleton />
          ) : (
            <div className="relative min-w-0 space-y-4">
              <div className="flex flex-col gap-2 rounded-[1.25rem] border border-slate-200 bg-white/75 px-4 py-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-800">Incident Trend by Time Window</p>
                  <p className="text-xs text-slate-500">
                    Each point shows how many sensors were in danger, moderate, and safe status during that time bucket.
                  </p>
                </div>
                <div className="text-xs font-medium text-slate-500">
                  {refreshing ? "Syncing latest sensor buckets..." : "Live record view"}
                </div>
              </div>

              <div className="h-[clamp(16rem,34vw,22rem)] w-full min-w-0 overflow-hidden">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={visibleChartData} margin={{ top: 12, right: 16, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="dangerGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ef4444" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="moderateGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.26} />
                      <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="safeGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#22c55e" stopOpacity={0.22} />
                      <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
                    </linearGradient>
                  </defs>

                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                  <XAxis dataKey="time" tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }} />

                  <Line
                    type="linear"
                    dataKey="danger"
                    name="Danger"
                    stroke="#ef4444"
                    strokeWidth={3}
                    dot={{ r: 3, strokeWidth: 0, fill: "#ef4444" }}
                    activeDot={{ r: 6 }}
                    isAnimationActive={false}
                  />
                  <Line
                    type="linear"
                    dataKey="moderate"
                    name="Moderate"
                    stroke="#f59e0b"
                    strokeWidth={3}
                    dot={{ r: 3, strokeWidth: 0, fill: "#f59e0b" }}
                    activeDot={{ r: 5 }}
                    isAnimationActive={false}
                  />
                  <Line
                    type="linear"
                    dataKey="safe"
                    name="Safe"
                    stroke="#22c55e"
                    strokeWidth={3}
                    dot={{ r: 3, strokeWidth: 0, fill: "#22c55e" }}
                    activeDot={{ r: 5 }}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
              </div>

              {!hasChartData && !loading ? (
                <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                  <div className="rounded-full bg-white/90 px-4 py-2 text-sm font-medium text-slate-500 shadow-sm">
                    {emptyMessage}
                  </div>
                </div>
              ) : null}

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
                {timelineSummary.map((point) => (
                  <div key={point.timestamp} className="rounded-[1.1rem] border border-slate-200 bg-white px-3 py-3 shadow-sm">
                    <p className="text-sm font-semibold text-slate-800">{point.time}</p>
                    <div className="mt-2 space-y-1 text-xs">
                      <div className="flex items-center justify-between text-red-600">
                        <span>Danger</span>
                        <strong>{point.danger}</strong>
                      </div>
                      <div className="flex items-center justify-between text-amber-600">
                        <span>Moderate</span>
                        <strong>{point.moderate}</strong>
                      </div>
                      <div className="flex items-center justify-between text-emerald-600">
                        <span>Safe</span>
                        <strong>{point.safe}</strong>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 px-[clamp(1rem,2vw,1.75rem)] pb-6 pt-3 lg:grid-cols-2">
        <div className="flex flex-col gap-2 rounded-[1.5rem] bg-slate-50/80 p-5">
          <span className="text-base text-slate-600 dark:text-slate-300">Critical Incidents</span>
          <div className="flex items-center gap-3">
            <span className="font-mono text-4xl font-semibold">{summaryCounts.danger}</span>
            <div className={cn("flex items-center gap-1 rounded-full px-3 py-1 text-sm font-semibold", criticalBgOpacity, "text-red-700 dark:text-[#F08083]")}>
              <AlertTriangle className="h-4 w-4" />
              Emergency Count
            </div>
          </div>
          <span className="text-sm text-slate-500 dark:text-[#9A9AAF]">
            {summaryCounts.danger} of {summaryCounts.total} monitored sensors are in emergency state for the latest view in {incidentPayload.window_label.toLowerCase()}
          </span>
        </div>

        <div className="flex flex-col gap-2 rounded-[1.5rem] bg-slate-50/80 p-5">
          <span className="text-base text-slate-600 dark:text-slate-300">Total Incident Samples</span>
          <div className="flex items-center gap-3">
            <span className="font-mono text-4xl font-semibold">{summaryCounts.safe + summaryCounts.moderate}</span>
            <div className={cn("flex items-center gap-1 rounded-full px-3 py-1 text-sm font-semibold", totalBgOpacity, "text-teal-700 dark:text-[#40E5D1]")}>
              <ShieldAlert className="h-4 w-4" />
              All Records
            </div>
          </div>
          <span className="text-sm text-slate-500 dark:text-[#9A9AAF]">
            Includes {summaryCounts.safe} safe and {summaryCounts.moderate} moderate sensors out of {summaryCounts.total} monitored sensors
          </span>
        </div>
      </div>

      <div className="min-w-0 divide-y divide-slate-200 px-[clamp(1rem,2vw,1.75rem)] pb-4 font-mono dark:divide-[#262631]">
        {insightRows.map((item, index) => {
          const Icon = item.icon;
          return (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex flex-col gap-3 py-4 md:flex-row md:items-center md:justify-between"
            >
              <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-[#9A9AAF]">
                <Icon className={cn("h-5 w-5", item.type === "critical" ? "text-red-500" : "text-amber-600")} />
                <span className="truncate">{item.title}</span>
              </div>
              <div className="text-lg font-semibold text-slate-900 dark:text-white">{item.value}</div>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-4 border-t border-slate-200/80 px-[clamp(1rem,2vw,1.75rem)] py-5 sm:grid-cols-2 xl:grid-cols-3">
        <div className="rounded-[1.25rem] border border-slate-200 bg-white p-4">
          <p className="text-sm text-slate-500">Current Danger Sensors</p>
          <strong className="mt-2 block text-2xl font-semibold text-red-600">{currentDangerCount}</strong>
        </div>
        <div className="rounded-[1.25rem] border border-slate-200 bg-white p-4">
          <p className="text-sm text-slate-500">Current Moderate Sensors</p>
          <strong className="mt-2 block text-2xl font-semibold text-amber-600">{currentModerateCount}</strong>
        </div>
        <div className="rounded-[1.25rem] border border-slate-200 bg-white p-4">
          <p className="text-sm text-slate-500">Current Safe Sensors</p>
          <strong className="mt-2 block text-2xl font-semibold text-emerald-600">{currentSafeCount}</strong>
        </div>
      </div>
    </div>
  );
}

export default IncidentReportMiddle;
