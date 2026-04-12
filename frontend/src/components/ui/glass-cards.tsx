"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  AlertTriangle,
  CarFront,
  CloudDrizzle,
  Flame,
  Gauge,
  Lightbulb,
  ShieldAlert,
  type LucideIcon,
  Thermometer,
  Trash2,
  Trees,
  Volume2,
  Waves,
} from "lucide-react";

gsap.registerPlugin(ScrollTrigger);

type SensorSeverity = "Safe" | "Moderate" | "Danger";

type SensorCardItem = {
  id: string;
  title: string;
  shortCode: string;
  description: string;
  value: string;
  status: string;
  trend: string;
  severity: SensorSeverity;
  freshness: string;
  image: string;
  currentSituation?: string;
  publicUpdate?: string;
  commandGuidance?: string;
  priorityBand?: string;
};

type EmergencyReportResult = {
  kind: "submitted" | "duplicate";
  message: string;
};

type IconKey =
  | "air"
  | "temperature"
  | "humidity"
  | "flood"
  | "traffic"
  | "noise"
  | "light"
  | "bin"
  | "rain"
  | "fire";

type StackedCardsProps = {
  cards: SensorCardItem[];
  locationLabel?: string;
  lastUpdated?: string;
  onEmergencyReport: (card: SensorCardItem) => Promise<EmergencyReportResult> | EmergencyReportResult;
  focusCardId?: string;
  focusRequestKey?: number;
};

type SingleCardProps = {
  card: SensorCardItem;
  index: number;
  totalCards: number;
  onEmergencyReport: (card: SensorCardItem) => Promise<EmergencyReportResult> | EmergencyReportResult;
  shouldFocus?: boolean;
  focusRequestKey?: number;
};

const ICON_MAP: Record<IconKey, LucideIcon> = {
  air: Trees,
  temperature: Thermometer,
  humidity: Gauge,
  flood: Waves,
  traffic: CarFront,
  noise: Volume2,
  light: Lightbulb,
  bin: Trash2,
  rain: CloudDrizzle,
  fire: Flame,
};

const CARD_META: Record<string, { icon: IconKey; accent: string }> = {
  air_smoke: { icon: "air", accent: "rgba(34, 211, 238, 0.86)" },
  temperature: { icon: "temperature", accent: "rgba(251, 146, 60, 0.86)" },
  humidity: { icon: "humidity", accent: "rgba(59, 130, 246, 0.86)" },
  flood_level: { icon: "flood", accent: "rgba(56, 189, 248, 0.86)" },
  traffic_total: { icon: "traffic", accent: "rgba(250, 204, 21, 0.86)" },
  parking_available: { icon: "traffic", accent: "rgba(125, 211, 252, 0.86)" },
  noise_level: { icon: "noise", accent: "rgba(244, 114, 182, 0.86)" },
  light_percent: { icon: "light", accent: "rgba(250, 204, 21, 0.86)" },
  bin_fill: { icon: "bin", accent: "rgba(163, 230, 53, 0.86)" },
  rain_percent: { icon: "rain", accent: "rgba(96, 165, 250, 0.86)" },
  fire_smoke: { icon: "fire", accent: "rgba(248, 113, 113, 0.86)" },
};

const severityCopy: Record<SensorSeverity, string> = {
  Safe: "Stable conditions",
  Moderate: "Needs attention",
  Danger: "Immediate response",
};

const severityGlow: Record<SensorSeverity, string> = {
  Safe: "rgba(52, 211, 153, 0.9)",
  Moderate: "rgba(250, 204, 21, 0.9)",
  Danger: "rgba(248, 113, 113, 0.9)",
};

const dangerCommentary: Record<string, string> = {
  air_smoke: "Air quality has crossed its safe limit. Residents should avoid prolonged outdoor exposure until the smoke level drops.",
  temperature: "Temperature has moved into a risky range. Outdoor activity should be reduced and heat or cold advisories should be monitored.",
  humidity: "Humidity has reached an uncomfortable and potentially unsafe level. Sensitive groups may experience stress in these conditions.",
  flood_level: "Flood level is approaching a critical threshold. Nearby roads and low-lying zones should be monitored for rapid water rise.",
  traffic_total: "Traffic density is severely elevated. Response teams should expect slower access and possible route blockages.",
  noise_level: "Noise intensity has crossed healthy exposure limits. Nearby residents and field teams may need hearing protection.",
  light_percent: "Ambient lighting support is below the expected safety threshold. Visibility may be compromised in this area.",
  bin_fill: "Waste-bin capacity is at or beyond its safe limit. Overflow and hygiene issues are likely if collection is delayed.",
  rain_percent: "Rain intensity is at a severe level. Road visibility and surface safety may deteriorate quickly.",
  fire_smoke: "Fire-smoke concentration is in the danger zone. Emergency services should assess the area immediately.",
};

function SensorGlassCard({ card, index, totalCards, onEmergencyReport, shouldFocus = false, focusRequestKey = 0 }: SingleCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [showDangerDetails, setShowDangerDetails] = useState(false);
  const [reportState, setReportState] = useState<EmergencyReportResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const cardNode = cardRef.current;
    const containerNode = containerRef.current;
    if (!cardNode || !containerNode) return;

    const targetScale = 1 - (totalCards - index - 1) * 0.025;

    gsap.set(cardNode, {
      scale: 1,
      y: 0,
      opacity: 1,
      transformOrigin: "center top",
    });

    const trigger = ScrollTrigger.create({
      trigger: containerNode,
      start: "top top+=88",
      end: "bottom center",
      scrub: 1,
      onUpdate: (self) => {
        const progress = self.progress;
        const scale = gsap.utils.interpolate(1, targetScale, progress);
        gsap.set(cardNode, {
          scale: Math.max(scale, targetScale),
          y: 0,
          opacity: 1,
          transformOrigin: "center top",
        });
      },
    });

    return () => {
      trigger.kill();
    };
  }, [index, totalCards]);

  useEffect(() => {
    if (!shouldFocus || !containerRef.current) return;

    containerRef.current.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });

    if (card.severity === "Danger") {
      setShowDangerDetails(true);
      setReportState(null);
    }
  }, [card.severity, shouldFocus, focusRequestKey]);

  const meta = CARD_META[card.id];
  const Icon = ICON_MAP[meta.icon];
  const accent = card.severity === "Safe" ? meta.accent : severityGlow[card.severity];
  const commentText = useMemo(
    () => dangerCommentary[card.id] || `${card.title} has reached its critical operating limit and needs immediate authority attention.`,
    [card.id, card.title]
  );
  const domainLabel = useMemo(
    () =>
      card.id === "air_smoke" || card.id === "fire_smoke"
        ? "air-quality response team"
        : card.id === "flood_level" || card.id === "rain_percent"
          ? "weather and flood control unit"
          : card.id === "traffic_total"
            ? "traffic management cell"
            : card.id === "noise_level"
              ? "urban noise control team"
              : card.id === "light_percent"
                ? "street-light maintenance team"
                : card.id === "bin_fill"
                  ? "waste management department"
                  : "environment operations team",
    [card.id]
  );

  return (
    <div
      ref={containerRef}
      className="relative flex min-w-0 items-center justify-center px-3 py-4 sm:px-4 md:sticky md:top-[76px] md:h-[78vh] md:min-h-[34rem] md:px-6 md:py-0"
    >
      <article
        ref={cardRef}
        className="relative isolate w-full max-w-6xl overflow-hidden rounded-[34px] border border-white/15 bg-white/8 shadow-[0_30px_120px_rgba(3,7,18,0.45)] backdrop-blur-2xl"
        style={{
          contain: "layout paint",
          top: `calc(-3vh + ${index * 18}px)`,
          minHeight: "clamp(500px, 64vh, 620px)",
        }}
      >
        <div
          className="absolute inset-0 rounded-[34px] opacity-80"
          style={{
            background: `linear-gradient(135deg, rgba(2, 6, 23, 0.16), rgba(2, 6, 23, 0.8)), url("${card.image}") center/cover`,
          }}
        />
        <div
          className="absolute inset-0 rounded-[34px]"
          style={{
            background: `radial-gradient(circle at top left, ${accent} 0%, transparent 34%), radial-gradient(circle at bottom right, rgba(255,255,255,0.12), transparent 35%)`,
          }}
        />
        <div
          className="pointer-events-none absolute inset-[1px] rounded-[33px]"
          style={{
            border: `1px solid ${accent.replace("0.9", "0.45").replace("0.86", "0.45")}`,
            boxShadow: `inset 0 1px 0 rgba(255,255,255,0.28), 0 0 40px ${accent.replace("0.9", "0.18").replace("0.86", "0.18")}`,
          }}
        />

        <div className="relative z-10 grid min-h-[clamp(500px,64vh,620px)] gap-5 px-5 py-5 text-white md:px-7 md:py-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <div className="flex min-w-0 flex-col justify-between gap-5">
            <div className="space-y-4">
              <div className="flex min-w-0 flex-wrap items-center gap-2">
                <span className="inline-flex max-w-full items-center gap-2 rounded-full border border-white/15 bg-black/20 px-3 py-1.5 text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-white/80">
                  <Icon className="h-4 w-4" />
                  {card.shortCode}
                </span>
                {card.severity === "Danger" ? (
                  <button
                    type="button"
                    onClick={() =>
                      setShowDangerDetails((value) => {
                        const next = !value;
                        if (!next) {
                          setReportState(null);
                        }
                        return next;
                      })
                    }
                    className="rounded-full px-3 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-950 transition-transform hover:scale-[1.03]"
                    style={{ backgroundColor: accent }}
                  >
                    {showDangerDetails ? "Close Danger" : "Danger"}
                  </button>
                ) : (
                  <span
                    className="rounded-full px-3 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-950"
                    style={{ backgroundColor: accent }}
                  >
                    {card.severity}
                  </span>
                )}
              </div>

              <div className="max-w-2xl space-y-2">
                <h3 className="break-words text-[clamp(1.35rem,2.4vw,2.1rem)] font-semibold leading-tight tracking-tight">{card.title}</h3>
                <p className="max-w-xl text-[clamp(0.82rem,1vw,0.95rem)] leading-6 text-slate-200">
                  {card.description}
                </p>
              </div>

              {card.severity === "Danger" && showDangerDetails ? (
                <div className="max-w-2xl rounded-[22px] border border-red-300/20 bg-red-950/30 p-4 shadow-[0_18px_40px_rgba(127,29,29,0.2)] backdrop-blur-xl">
                  <div className="flex items-start gap-3">
                    <ShieldAlert className="mt-1 h-5 w-5 shrink-0 text-red-300" />
                    <div>
                      <p className="text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-red-200/80">
                        Critical comment
                      </p>
                      <p className="mt-2 text-sm leading-6 text-red-50/95">
                        {commentText}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={async () => {
                      if (isSubmitting) return;
                      setIsSubmitting(true);
                      try {
                        const result = await onEmergencyReport(card);
                        setReportState(
                          result || {
                            kind: "submitted",
                            message: `${card.title} emergency reported successfully to the ${domainLabel}. Authorities have been notified and will address the issue as soon as possible.`,
                          }
                        );
                      } finally {
                        setIsSubmitting(false);
                      }
                    }}
                    className="mt-4 inline-flex items-center rounded-full bg-red-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition-colors hover:bg-red-300"
                  >
                    {isSubmitting ? "Sending..." : "Emergency Report"}
                  </button>
                  {reportState ? (
                    <div
                      className={`mt-4 rounded-[22px] p-4 backdrop-blur-xl ${
                        reportState.kind === "submitted"
                          ? "border border-emerald-300/20 bg-emerald-950/30"
                          : "border border-amber-300/20 bg-amber-950/30"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-3">
                          <div className={`mt-1 h-2.5 w-2.5 rounded-full ${reportState.kind === "submitted" ? "bg-emerald-300" : "bg-amber-300"}`} />
                          <div>
                            <p className={`text-xs font-semibold uppercase tracking-[0.28em] ${reportState.kind === "submitted" ? "text-emerald-200/85" : "text-amber-200/85"}`}>
                              {reportState.kind === "submitted" ? "Report sent" : "Already submitted"}
                            </p>
                            <p className={`mt-2 text-sm leading-7 ${reportState.kind === "submitted" ? "text-emerald-50/95" : "text-amber-50/95"}`}>{reportState.message}</p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            setReportState(null);
                            setShowDangerDetails(false);
                          }}
                          className={`shrink-0 rounded-full bg-white/8 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition-colors hover:bg-white/14 ${reportState.kind === "submitted" ? "border border-emerald-300/25 text-emerald-100" : "border border-amber-300/25 text-amber-100"}`}
                        >
                          Close
                        </button>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="min-w-0 rounded-[20px] border border-white/12 bg-black/25 p-4 backdrop-blur-xl">
                <p className="text-[0.68rem] uppercase tracking-[0.2em] text-white/55">Live reading</p>
                <strong className="mt-2 block break-words text-[clamp(1.25rem,2vw,1.75rem)] font-semibold">{card.value}</strong>
                <span className="mt-1 block text-xs text-white/65">{card.freshness}</span>
              </div>
              <div className="min-w-0 rounded-[20px] border border-white/12 bg-black/25 p-4 backdrop-blur-xl">
                <p className="text-[0.68rem] uppercase tracking-[0.2em] text-white/55">Current situation</p>
                <strong className="mt-2 block break-words text-sm font-semibold text-white/95">{card.currentSituation || card.status}</strong>
                <span className="mt-1 block text-xs leading-5 text-white/65">{severityCopy[card.severity]}</span>
              </div>
              <div className="min-w-0 rounded-[20px] border border-white/12 bg-black/25 p-4 backdrop-blur-xl">
                <p className="text-[0.68rem] uppercase tracking-[0.2em] text-white/55">Trend signal</p>
                <strong className="mt-2 block break-words text-sm font-semibold text-white/95">{card.trend}</strong>
                <span className="mt-1 block text-xs leading-5 text-white/65">Compared with previous sample</span>
              </div>
            </div>
          </div>

          <div className="flex min-w-0 flex-col justify-between gap-4">
            <div className="min-w-0 rounded-[22px] border border-white/12 bg-white/10 p-4 backdrop-blur-xl">
              <p className="text-[0.68rem] uppercase tracking-[0.2em] text-white/55">Command guidance</p>
              <p className="mt-3 text-sm leading-6 text-slate-100">
                {card.commandGuidance || (card.severity === "Danger"
                  ? "Escalate this zone now, notify the operations team, and prioritize mitigation in the next response cycle."
                  : card.severity === "Moderate"
                    ? "Track this metric closely for the next updates and prepare a local response if the trend continues."
                    : "Conditions are within a healthy range. Keep monitoring and maintain the current response posture.")}
              </p>
            </div>

            <div className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,10rem),1fr))] gap-3">
              <div className="min-w-0 rounded-[20px] border border-white/12 bg-black/25 p-4">
                <p className="text-[0.68rem] uppercase tracking-[0.2em] text-white/55">Priority band</p>
                <div className="mt-3 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" style={{ color: accent }} />
                  <strong className="break-words text-sm font-semibold">{card.priorityBand || severityCopy[card.severity]}</strong>
                </div>
              </div>
              <div className="min-w-0 rounded-[20px] border border-white/12 bg-black/25 p-4">
                <p className="text-[0.68rem] uppercase tracking-[0.2em] text-white/55">Public update</p>
                <strong className="mt-3 block break-words text-sm font-semibold text-white/95">{card.publicUpdate || card.currentSituation || card.status}</strong>
                <span className="mt-1 block text-xs leading-5 text-white/65">Aligned with latest signal</span>
              </div>
            </div>
          </div>
        </div>
      </article>
    </div>
  );
}

export function StackedCards({
  cards,
  locationLabel,
  lastUpdated,
  onEmergencyReport,
  focusCardId,
  focusRequestKey = 0,
}: StackedCardsProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const containerNode = containerRef.current;
    if (!containerNode) return;

    const animation = gsap.fromTo(
      containerNode,
      { opacity: 0, y: 18 },
      {
        opacity: 1,
        y: 0,
        duration: 0.9,
        ease: "power2.out",
      }
    );

    return () => {
      animation.kill();
    };
  }, []);

  return (
    <section
      ref={containerRef}
      className="relative overflow-hidden rounded-[clamp(1.25rem,2vw,2.25rem)] border border-slate-200/10 bg-[#050816] px-[clamp(0.875rem,2vw,2rem)] py-[clamp(1.5rem,4vw,3rem)] text-white shadow-[0_24px_90px_rgba(2,6,23,0.4)]"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.18),_transparent_26%),radial-gradient(circle_at_bottom_right,_rgba(248,113,113,0.12),_transparent_24%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(148,163,184,0.09)_1px,transparent_1px),linear-gradient(to_bottom,rgba(148,163,184,0.08)_1px,transparent_1px)] bg-[size:72px_72px] opacity-35 [mask-image:radial-gradient(circle_at_center,black,transparent_88%)]" />

      <div className="relative z-10 mx-auto w-full max-w-6xl">
        <div className="mb-[clamp(1.25rem,3vw,2.25rem)] flex min-w-0 flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-3xl min-w-0">
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.28em] text-cyan-300/85">
              Live Urban Intelligence
            </p>
            <h2 className="mt-3 text-[clamp(1.65rem,4vw,3.25rem)] font-semibold leading-tight tracking-tight text-white">
              Live Environment Status
            </h2>
            <p className="mt-3 max-w-2xl text-[clamp(0.85rem,1.2vw,1rem)] leading-6 text-slate-300">
              A premium live stack of your city’s most important environmental signals, combining real-time sensor values,
              trend movement, and response-ready guidance in one immersive view.
            </p>
          </div>

          <div className="grid w-full grid-cols-[repeat(auto-fit,minmax(min(100%,12rem),1fr))] gap-3 md:w-auto md:min-w-[24rem]">
            <article className="min-w-0 rounded-[20px] border border-white/10 bg-white/8 px-4 py-3 backdrop-blur-xl">
              <p className="text-[0.68rem] uppercase tracking-[0.2em] text-white/55">Coverage area</p>
              <strong className="mt-2 block break-words text-sm font-semibold">{locationLabel || "Monitoring zone"}</strong>
            </article>
            <article className="min-w-0 rounded-[20px] border border-white/10 bg-white/8 px-4 py-3 backdrop-blur-xl">
              <p className="text-[0.68rem] uppercase tracking-[0.2em] text-white/55">Last live update</p>
              <strong className="mt-2 block break-words text-sm font-semibold">{lastUpdated || "Waiting for sensor feed"}</strong>
            </article>
          </div>
        </div>

        <div className="space-y-0 pb-[clamp(4rem,9vw,8rem)]">
          {cards.map((card, index) => (
            <SensorGlassCard
              key={card.id}
              card={card}
              index={index}
              totalCards={cards.length}
              onEmergencyReport={onEmergencyReport}
              shouldFocus={focusCardId === card.id}
              focusRequestKey={focusRequestKey}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
