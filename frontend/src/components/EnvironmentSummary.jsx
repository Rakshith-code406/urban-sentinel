import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { CloudRain, Droplets, Thermometer, Wind, X } from "lucide-react";
import { apiUrl } from "../services/apiBase";
import "./EnvironmentSummary.css";

const LIVE_ENVIRONMENT_URL = apiUrl("/iot/live");
const TIMELINE_URL = apiUrl("/iot/timeline");
const POLL_INTERVAL_MS = 5000;
const LOCATION_STORAGE_KEY = "urbanSentinelLocation";
const DEFAULT_DATA = {
  temperature: { live_value: 0, status: "Normal" },
  air: { live_value: 0, status: "Good" },
  humidity: { live_value: 0, status: "Comfortable" },
  rain: { live_value: 0, status: "Low" },
  location: { label: "Monitoring zone", latitude: null, longitude: null },
};

const DETAIL_META = {
  temp: {
    label: "Temperature",
    timelineKey: "temperature",
    rangeKey: "temperature",
    valueSuffix: "\u00B0C",
    unitLabel: "Temperature (\u00B0C)",
    updateWindow: "Today's timeline",
  },
  air: {
    label: "Air Quality",
    timelineKey: "air_smoke",
    rangeKey: "air",
    valueSuffix: "",
    unitLabel: "Air Quality Index",
    updateWindow: "Today's timeline",
  },
  humidity: {
    label: "Humidity",
    timelineKey: "humidity",
    rangeKey: "humidity",
    valueSuffix: "%",
    unitLabel: "Relative Humidity (%)",
    updateWindow: "Today's timeline",
  },
  rain: {
    label: "Rain Intensity",
    timelineKey: "rain_percent",
    rangeKey: "rain",
    valueSuffix: "%",
    unitLabel: "Rain Intensity (%)",
    updateWindow: "Today's timeline",
  },
};

function readStoredLocation() {
  try {
    const storedLocation = JSON.parse(localStorage.getItem(LOCATION_STORAGE_KEY) || "{}");
    return storedLocation && typeof storedLocation === "object" ? storedLocation : {};
  } catch {
    return {};
  }
}

function buildLocationParams() {
  const params = new URLSearchParams();
  const storedLocation = readStoredLocation();
  if (storedLocation?.latitude != null && storedLocation?.longitude != null) {
    params.set("latitude", String(storedLocation.latitude));
    params.set("longitude", String(storedLocation.longitude));
  }
  if (storedLocation?.label) {
    params.set("location_name", storedLocation.label);
  }
  return params;
}

function normalizeMetricValue(value, fallback) {
  if (value === null || value === undefined) {
    return fallback;
  }

  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return fallback;
  }

  return numeric;
}

function formatDisplayValue(value) {
  if (value === "--" || value === null || value === undefined) {
    return "0";
  }

  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "0";
  }

  return numeric % 1 === 0 ? String(numeric) : numeric.toFixed(1);
}

function formatMetricValue(value, suffix = "") {
  return `${formatDisplayValue(value)}${suffix}`;
}

function describeTrend(values) {
  const numbers = values
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value));

  if (numbers.length < 2) {
    return "Stable";
  }

  const first = numbers[0];
  const last = numbers[numbers.length - 1];
  const delta = last - first;

  if (Math.abs(delta) < 0.35) return "Stable";
  if (delta > 0) return "Rising";
  return "Falling";
}

function describeFeelsLike(type, currentValue, humidityValue, statusText) {
  const current = Number(currentValue);
  const humidity = Number(humidityValue);
  const normalizedStatus = String(statusText || "").toLowerCase();

  if (type === "temp") {
    if (!Number.isFinite(current)) return "Comfortable";
    const apparent = current + (Number.isFinite(humidity) ? (humidity - 50) / 20 : 0);
    if (apparent >= 38) return "Very Hot";
    if (apparent >= 32) return "Hot";
    if (apparent >= 26) return "Warm";
    if (apparent >= 20) return "Comfortable";
    return "Cool";
  }

  if (type === "air") {
    if (normalizedStatus.includes("hazard") || current >= 200) return "Hazardous";
    if (normalizedStatus.includes("poor") || current >= 120) return "Poor";
    if (current >= 80) return "Moderate";
    return "Good";
  }

  if (type === "humidity") {
    if (!Number.isFinite(current)) return "Comfortable";
    if (current >= 75) return "Very Humid";
    if (current >= 55) return "Comfortable";
    return "Dry";
  }

  if (!Number.isFinite(current) || current <= 0) return "Dry";
  if (current >= 75) return "Heavy";
  if (current >= 35) return "Moderate";
  return "Light";
}

function buildScaleMarks(minValue, maxValue) {
  if (!Number.isFinite(minValue) || !Number.isFinite(maxValue)) {
    return ["0", "0", "0", "0"];
  }

  const step = (maxValue - minValue) / 3;
  return [maxValue, maxValue - step, maxValue - step * 2, minValue].map((value) =>
    formatDisplayValue(value)
  );
}

function getBarHeight(value, minValue, maxValue) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return 32;
  }

  if (!Number.isFinite(minValue) || !Number.isFinite(maxValue) || minValue === maxValue) {
    return 88;
  }

  const ratio = (numeric - minValue) / (maxValue - minValue);
  return Math.round(28 + ratio * 108);
}

function buildFallbackPoints(type, metric, timeline) {
  const currentValue = normalizeMetricValue(metric?.live_value, 0);
  const range = timeline?.ranges?.[DETAIL_META[type]?.rangeKey] || {};
  const minValue = normalizeMetricValue(range?.min, currentValue);
  const maxValue = normalizeMetricValue(range?.max, currentValue);
  const midpointValue = Number(((minValue + maxValue) / 2).toFixed(1));

  return [
    { key: "09", label: "9 AM", sourceLabel: "", value: minValue },
    { key: "12", label: "12 PM", sourceLabel: "", value: midpointValue },
    { key: "14", label: "2 PM", sourceLabel: "", value: maxValue },
    { key: "17", label: "5 PM", sourceLabel: "", value: midpointValue },
    { key: "current", label: "Current", sourceLabel: "Now", value: currentValue },
  ];
}

function buildDetailData(type, metric, humidityMetric, timeline) {
  const meta = DETAIL_META[type];
  if (!meta) {
    return null;
  }

  const slots = Array.isArray(timeline?.slots) ? timeline.slots : [];
  const points = slots
    .map((slot) => {
      const value = normalizeMetricValue(slot?.[meta.timelineKey], null);
      if (!Number.isFinite(value)) {
        return null;
      }

      return {
        key: slot?.key || slot?.label,
        label: slot?.label || "Slot",
        sourceLabel: slot?.source_label || "",
        value,
      };
    })
    .filter(Boolean);

  if (!points.length) {
    const fallbackPoints = buildFallbackPoints(type, metric, timeline);
    const fallbackValues = fallbackPoints.map((point) => point.value);
    return {
      ...meta,
      status: metric?.status || "Live",
      currentValue: normalizeMetricValue(metric?.live_value, 0),
      minValue: Math.min(...fallbackValues),
      maxValue: Math.max(...fallbackValues),
      trend: describeTrend(fallbackValues),
      feelsLike: describeFeelsLike(type, metric?.live_value, humidityMetric?.live_value, metric?.status),
      summary: `Current ${meta.label.toLowerCase()} data is available with today's range overview.`,
      advisory: "The graph is shown using the available current reading and today's range.",
      points: fallbackPoints,
      chartCaption: "Today's timeline",
    };
  }

  const currentPoint = points.find((point) => point.key === "current") || points[0] || null;
  const currentValue = normalizeMetricValue(
    currentPoint?.value,
    normalizeMetricValue(metric?.live_value, 0)
  );
  const values = points.map((point) => point.value);
  const range = timeline?.ranges?.[meta.rangeKey] || {};
  const minValue = normalizeMetricValue(range?.min, values.length ? Math.min(...values) : currentValue);
  const maxValue = normalizeMetricValue(range?.max, values.length ? Math.max(...values) : currentValue);
  const trend = describeTrend(values);
  const feelsLike = describeFeelsLike(type, currentValue, humidityMetric?.live_value, metric?.status);
  const status = metric?.status || "Live";

  const summary =
    type === "temp"
      ? `Current temperature is ${formatMetricValue(currentValue, "\u00B0C")}. Today's minimum is ${formatMetricValue(minValue, "\u00B0C")} and maximum is ${formatMetricValue(maxValue, "\u00B0C")}.`
      : type === "air"
        ? `Current air quality index is ${formatMetricValue(currentValue)}. Today's minimum is ${formatMetricValue(minValue)} and maximum is ${formatMetricValue(maxValue)}.`
        : type === "humidity"
          ? `Current humidity is ${formatMetricValue(currentValue, "%")}. Today's minimum is ${formatMetricValue(minValue, "%")} and maximum is ${formatMetricValue(maxValue, "%")}.`
          : `Current rain intensity is ${formatMetricValue(currentValue, "%")}. Today's minimum is ${formatMetricValue(minValue, "%")} and maximum is ${formatMetricValue(maxValue, "%")}.`;

  const advisory =
    type === "temp"
      ? "Review how temperature is moving across the day and compare the current reading with the daytime range."
      : type === "air"
        ? "Review how air quality changes through the day and compare the current reading with the daytime range."
        : type === "humidity"
          ? "Review how humidity changes through the day and compare the current reading with the daytime range."
          : "Review how rain intensity changes through the day and compare the current reading with the daytime range.";

  return {
    ...meta,
    status,
    currentValue,
    minValue,
    maxValue,
    trend,
    feelsLike,
    summary,
    advisory,
    points,
    chartCaption: timeline?.date ? `Day overview for ${timeline.date}` : "Today's timeline",
  };
}

function Card({ title, value, unit, icon, onClick }) {
  return (
    <button type="button" className="env-card" onClick={onClick}>
      <div className="env-icon" aria-hidden="true">
        {icon}
      </div>
      <div className="env-copy">
        <p className="env-title">{title}</p>
        <h2 className="env-value">
          {formatDisplayValue(value)}
          {unit ? ` ${unit}` : ""}
        </h2>
        <span className="env-card-link">Tap for details</span>
      </div>
    </button>
  );
}

function DetailPanel({ type, metric, humidityMetric, timeline, onClose }) {
  const detail = buildDetailData(type, metric, humidityMetric, timeline);

  if (!detail) {
    return null;
  }

  const modal = (
    <div className="env-report-modal-shell" role="dialog" aria-modal="true" aria-labelledby={`env-detail-title-${type}`}>
      <div className="env-report-modal-backdrop" onClick={onClose} />
      <section className="env-report-modal-card" onClick={(event) => event.stopPropagation()}>
        <header className="env-report-modal-head">
          <div>
            <p>Environmental Monitoring Detail</p>
            <h3 id={`env-detail-title-${type}`}>{detail.label} Monitoring Summary</h3>
            <div className="env-report-modal-badges">
              <span className="env-report-modal-badge">Operational Status: {detail.status}</span>
              <span className="env-report-modal-badge">Update Window: {detail.updateWindow}</span>
            </div>
          </div>
          <button type="button" onClick={onClose} aria-label="Close details">
            <X size={18} />
          </button>
        </header>

        <p className="env-modal-subtitle">{detail.summary}</p>
        <p className="env-modal-note">{detail.advisory}</p>

        <div className="env-detail-grid">
          <div>
            <span>Trend</span>
            <strong>{detail.trend}</strong>
          </div>
          <div>
            <span>Current</span>
            <strong>{formatMetricValue(detail.currentValue, detail.valueSuffix)}</strong>
          </div>
          <div>
            <span>Min</span>
            <strong>{formatMetricValue(detail.minValue, detail.valueSuffix)}</strong>
          </div>
          <div>
            <span>Max</span>
            <strong>{formatMetricValue(detail.maxValue, detail.valueSuffix)}</strong>
          </div>
          <div>
            <span>Feels Like</span>
            <strong>{detail.feelsLike}</strong>
          </div>
          <div>
            <span>Update Window</span>
            <strong>{detail.updateWindow}</strong>
          </div>
        </div>

        <section className="env-chart-panel" aria-label={`${detail.label} chart`}>
          <div className="env-chart-head">
            <div>
              <p className="env-chart-eyebrow">Forecast Graph</p>
              <h4>{detail.unitLabel}</h4>
            </div>
            <span className="env-chart-caption">{detail.chartCaption}</span>
          </div>

          <div className="env-chart-scroll">
            <div className="env-chart-layout">
              <div className="env-chart-scale" aria-hidden="true">
                {buildScaleMarks(detail.minValue, detail.maxValue).map((mark, index) => (
                  <span key={`${mark}-${index}`}>{mark}</span>
                ))}
              </div>

              <div className="env-graph">
                {detail.points.map((point) => (
                  <div key={point.key} className="env-graph-bar">
                    <p>{point.label}</p>
                    <span className="env-graph-source">{point.sourceLabel}</span>
                    <strong>{formatMetricValue(point.value, detail.valueSuffix)}</strong>
                    <div className="env-graph-bar-track">
                      <div
                        className="env-graph-bar__fill"
                        style={{ height: `${getBarHeight(point.value, detail.minValue, detail.maxValue)}px` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </section>
    </div>
  );

  if (typeof document === "undefined") {
    return modal;
  }

  return createPortal(modal, document.body);
}

export default function EnvironmentSummary() {
  const [data, setData] = useState(DEFAULT_DATA);
  const [timeline, setTimeline] = useState(null);
  const [activeCard, setActiveCard] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const fetchData = async () => {
      try {
        const params = buildLocationParams();
        const url = params.toString() ? `${LIVE_ENVIRONMENT_URL}?${params.toString()}` : LIVE_ENVIRONMENT_URL;
        const timelineUrl = params.toString() ? `${TIMELINE_URL}?${params.toString()}` : TIMELINE_URL;
        const [liveRes, timelineRes] = await Promise.allSettled([
          fetch(url, { cache: "no-store" }),
          fetch(timelineUrl, { cache: "no-store" }),
        ]);
        const json =
          liveRes.status === "fulfilled" && liveRes.value.ok
            ? await liveRes.value.json().catch(() => ({}))
            : {};
        const timelineJson =
          timelineRes.status === "fulfilled" && timelineRes.value.ok
            ? await timelineRes.value.json().catch(() => null)
            : null;

        if (cancelled) return;

        setData((current) => ({
          temperature: {
            ...current.temperature,
            ...(json?.temperature || {}),
            live_value: normalizeMetricValue(json?.temperature?.live_value, current.temperature.live_value),
          },
          air: {
            ...current.air,
            ...(json?.air || {}),
            live_value: normalizeMetricValue(json?.air?.live_value, current.air.live_value),
          },
          humidity: {
            ...current.humidity,
            ...(json?.humidity || {}),
            live_value: normalizeMetricValue(json?.humidity?.live_value, current.humidity.live_value),
          },
          rain: {
            ...current.rain,
            ...(json?.rain || {}),
            live_value: normalizeMetricValue(json?.rain?.live_value, current.rain.live_value),
          },
          location: json?.location || current.location,
        }));
        if (timelineJson?.slots?.length) {
          setTimeline(timelineJson);
        }
      } catch (error) {
        console.error("Environment summary fetch failed", error);
      }
    };

    fetchData();
    const interval = window.setInterval(fetchData, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    if (!activeCard || typeof document === "undefined") {
      return undefined;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [activeCard]);

  const cards = useMemo(
    () => [
      {
        key: "temp",
        title: "Temperature",
        value: data?.temperature?.live_value ?? 0,
        unit: "\u00B0C",
        icon: <Thermometer size={28} strokeWidth={2.1} />,
      },
      {
        key: "air",
        title: "Air Quality",
        value: data?.air?.live_value ?? 0,
        unit: "",
        icon: <Wind size={28} strokeWidth={2.1} />,
      },
      {
        key: "humidity",
        title: "Humidity",
        value: data?.humidity?.live_value ?? 0,
        unit: "%",
        icon: <Droplets size={28} strokeWidth={2.1} />,
      },
      {
        key: "rain",
        title: "Rain Intensity",
        value: data?.rain?.live_value ?? 0,
        unit: "%",
        icon: <CloudRain size={28} strokeWidth={2.1} />,
      },
    ],
    [data]
  );

  const activeMetric =
    activeCard === "temp"
      ? data?.temperature
      : activeCard
        ? data?.[activeCard]
        : null;

  const locationChips = useMemo(
    () => [
      {
        label: data?.location?.label || "Monitoring zone",
        temp: `${formatDisplayValue(data?.temperature?.live_value)}\u00B0`,
        tone: "cool",
      },
    ],
    [data]
  );

  return (
    <section className="env-container" aria-label="Environment Summary">
      <div className="env-location-row">
        {locationChips.map((chip) => (
          <button key={chip.label} type="button" className={`env-location-chip env-location-chip--${chip.tone}`}>
            <span>{chip.label}</span>
            <strong>{chip.temp}</strong>
          </button>
        ))}
      </div>

      <div className="env-heading">
        <div>
          <h2 className="env-title-main">Environment Summary</h2>
          <p className="env-subtitle">
            Live atmospheric conditions with a clean day-view chart for quick comparison.
          </p>
        </div>
        <div className="env-status-pill">Live Monitoring</div>
      </div>

      <div className="env-grid">
        {cards.map((card) => (
          <Card
            key={card.key}
            title={card.title}
            value={card.value}
            unit={card.unit}
            icon={card.icon}
            onClick={() => setActiveCard(card.key)}
          />
        ))}
      </div>

      {activeCard ? (
        <DetailPanel
          type={activeCard}
          metric={activeMetric}
          humidityMetric={data?.humidity}
          timeline={timeline}
          onClose={() => setActiveCard(null)}
        />
      ) : null}
    </section>
  );
}
