"use client";

import { motion } from "framer-motion";
import { Activity, CloudRain, Droplets, ThermometerSun } from "lucide-react";

type SummaryMetric = {
  key: string;
  label: string;
  unit: string;
  value: number | string | null;
  loading?: boolean;
  fallbackText?: string;
};

type SummaryOption = {
  value: number;
  label: string;
};

type EnvironmentSummarySliderProps = {
  title?: string;
  metrics: SummaryMetric[];
  selectedValue: number;
  options: SummaryOption[];
  onSelect: (value: number) => void;
  summaryText: string;
};

const METRIC_ICONS = {
  temperature: ThermometerSun,
  air_smoke: Activity,
  humidity: Droplets,
  rain_percent: CloudRain,
} as const;

const formatMetricValue = (metric: SummaryMetric) => {
  if (metric.loading) {
    return "Loading...";
  }

  if (metric.value === null || Number.isNaN(metric.value)) {
    return metric.fallbackText || "N/A";
  }

  if (typeof metric.value === "string") {
    return metric.value;
  }

  const suffix = metric.unit ? ` ${metric.unit}` : "";
  return `${metric.value.toFixed(1)}${suffix}`;
};

export default function EnvironmentSummarySlider({
  title = "Environment Summary",
  metrics,
  selectedValue,
  options,
  onSelect,
  summaryText,
}: EnvironmentSummarySliderProps) {
  return (
    <div className="w-full">
      <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
        >
          <h2 className="m-0 text-[1.35rem] font-semibold tracking-[-0.03em] text-slate-900 md:text-[1.55rem]">
            {title}
          </h2>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.05 }}
          className="flex flex-wrap gap-3 md:justify-end"
        >
          {options.map((option) => {
            const active = option.value === selectedValue;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => onSelect(option.value)}
                className={[
                  "inline-flex min-h-12 items-center justify-center rounded-full border px-5 text-[1rem] font-medium transition-all duration-200",
                  active
                    ? "border-slate-900 bg-slate-900 text-white shadow-[0_10px_24px_rgba(15,23,42,0.18)]"
                    : "border-slate-200 bg-white/80 text-slate-700 hover:border-slate-300 hover:bg-slate-50",
                ].join(" ")}
              >
                {option.label}
              </button>
            );
          })}
        </motion.div>
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-4 md:grid-cols-2">
        {metrics.map((metric, index) => {
          const Icon = METRIC_ICONS[metric.key as keyof typeof METRIC_ICONS] ?? Activity;

          return (
            <motion.article
              key={metric.key}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.06 * index }}
              whileHover={{ y: -4 }}
              className="group relative overflow-hidden rounded-[28px] border border-sky-100/90 bg-gradient-to-br from-white via-slate-50 to-sky-50 px-5 py-5 shadow-[0_16px_34px_rgba(15,23,42,0.06)]"
            >
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.12),_transparent_42%)] opacity-90" />
              <div className="relative flex items-start justify-between gap-4">
                <div>
                  <p className="m-0 text-[1.02rem] font-medium text-slate-500">
                    {metric.label}
                  </p>
                  <p className="mt-5 mb-0 text-[1.9rem] font-semibold tracking-[-0.04em] text-slate-900">
                    {formatMetricValue(metric)}
                  </p>
                </div>
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-white/70 bg-white/70 text-slate-700 shadow-sm transition-transform duration-200 group-hover:scale-105">
                  <Icon className="h-5 w-5" strokeWidth={2.1} />
                </div>
              </div>
            </motion.article>
          );
        })}
      </div>

      <motion.p
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.12 }}
        className="mt-6 mb-0 text-[1.12rem] font-semibold tracking-[-0.02em] text-slate-700"
      >
        {summaryText}
      </motion.p>
    </div>
  );
}
