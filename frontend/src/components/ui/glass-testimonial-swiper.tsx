import React, { CSSProperties, useCallback, useEffect, useRef, useState } from "react";

export interface Testimonial {
  id: string | number;
  initials: string;
  name: string;
  role: string;
  quote: string;
  tags: { text: string; type: "featured" | "default" }[];
  stats: { icon: React.ComponentType<React.SVGProps<SVGSVGElement>>; text: string }[];
  avatarGradient: string;
}

export interface TestimonialStackProps {
  testimonials: Testimonial[];
  visibleBehind?: number;
}

export const TestimonialStack = ({ testimonials, visibleBehind = 2 }: TestimonialStackProps) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState(0);
  const dragStartRef = useRef(0);
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);
  const totalCards = testimonials.length;

  const navigate = useCallback(
    (newIndex: number) => {
      setActiveIndex((newIndex + totalCards) % totalCards);
    },
    [totalCards]
  );

  const handleDragStart = (e: React.MouseEvent | React.TouchEvent, index: number) => {
    if (index !== activeIndex) return;
    setIsDragging(true);
    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    dragStartRef.current = clientX;
    cardRefs.current[activeIndex]?.classList.add("is-dragging");
  };

  const handleDragMove = useCallback(
    (e: MouseEvent | TouchEvent) => {
      if (!isDragging) return;
      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
      setDragOffset(clientX - dragStartRef.current);
    },
    [isDragging]
  );

  const handleDragEnd = useCallback(() => {
    if (!isDragging) return;
    cardRefs.current[activeIndex]?.classList.remove("is-dragging");
    if (Math.abs(dragOffset) > 50) {
      navigate(activeIndex + (dragOffset < 0 ? 1 : -1));
    }
    setIsDragging(false);
    setDragOffset(0);
  }, [activeIndex, dragOffset, isDragging, navigate]);

  useEffect(() => {
    if (activeIndex >= totalCards) {
      setActiveIndex(0);
    }
  }, [activeIndex, totalCards]);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener("mousemove", handleDragMove);
      window.addEventListener("touchmove", handleDragMove);
      window.addEventListener("mouseup", handleDragEnd);
      window.addEventListener("touchend", handleDragEnd);
    }

    return () => {
      window.removeEventListener("mousemove", handleDragMove);
      window.removeEventListener("touchmove", handleDragMove);
      window.removeEventListener("mouseup", handleDragEnd);
      window.removeEventListener("touchend", handleDragEnd);
    };
  }, [handleDragEnd, handleDragMove, isDragging]);

  if (!testimonials?.length) return null;

  return (
    <section className="relative min-h-[360px] pb-12 sm:min-h-[390px]">
      <div className="absolute right-0 top-0 z-[60] flex items-center gap-2">
        <span className="rounded-full border border-white/12 bg-white/8 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-200">
          {activeIndex + 1} of {totalCards}
        </span>
      </div>

      {testimonials.map((testimonial, index) => {
        const displayOrder = (index - activeIndex + totalCards) % totalCards;
        const style: CSSProperties = {};

        if (displayOrder === 0) {
          style.transform = `translateX(${dragOffset}px)`;
          style.opacity = 1;
          style.zIndex = totalCards;
        } else if (displayOrder <= visibleBehind) {
          const scale = 1 - 0.05 * displayOrder;
          const translateY = -1.5 * displayOrder;
          style.transform = `scale(${scale}) translateY(${translateY}rem)`;
          style.opacity = 1 - 0.18 * displayOrder;
          style.zIndex = totalCards - displayOrder;
        } else {
          style.transform = "scale(0.92) translateY(-4rem)";
          style.opacity = 0;
          style.zIndex = 0;
          style.pointerEvents = "none";
        }

        const tagClasses =
          testimonial.tags.length > 0
            ? {
                featured:
                  "border border-cyan-400/30 bg-cyan-400/12 text-cyan-100",
                default:
                  "border border-white/12 bg-white/8 text-slate-200",
              }
            : null;

        return (
          <div
            ref={(el) => {
              cardRefs.current[index] = el;
            }}
            key={testimonial.id}
            className="absolute inset-x-0 top-0 mx-auto w-full max-w-3xl cursor-grab rounded-[32px] border border-white/14 bg-[linear-gradient(180deg,rgba(16,24,39,0.88),rgba(7,16,28,0.92))] text-white shadow-[0_34px_80px_rgba(2,8,23,0.46)] backdrop-blur-xl transition-transform duration-300 ease-out will-change-transform select-none active:cursor-grabbing"
            style={style}
            onMouseDown={(e) => handleDragStart(e, index)}
            onTouchStart={(e) => handleDragStart(e, index)}
          >
            <div className="absolute inset-0 rounded-[32px] bg-[radial-gradient(circle_at_top_right,rgba(56,189,248,0.18),transparent_35%),radial-gradient(circle_at_bottom_left,rgba(129,140,248,0.14),transparent_38%)]" />
            <div className="relative p-6 md:p-8">
              <div className="mb-6 flex items-start justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div
                    className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-base font-semibold text-white shadow-[0_12px_24px_rgba(15,23,42,0.24)]"
                    style={{ background: testimonial.avatarGradient }}
                  >
                    {testimonial.initials}
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-white">{testimonial.name}</h3>
                    <p className="mt-1 text-sm text-slate-300">{testimonial.role}</p>
                  </div>
                </div>
              </div>

              <blockquote className="mb-6 text-base leading-8 text-slate-100 md:text-lg">
                "{testimonial.quote}"
              </blockquote>

              <div className="flex flex-col items-start justify-between gap-4 border-t border-white/10 pt-4 md:flex-row md:items-center">
                <div className="flex flex-wrap gap-2">
                  {testimonial.tags.map((tag, tagIndex) => (
                    <span
                      key={`${testimonial.id}-${tagIndex}`}
                      className={[
                        "rounded-md px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em]",
                        tagClasses ? tagClasses[tag.type] : "",
                      ].join(" ")}
                    >
                      {tag.text}
                    </span>
                  ))}
                </div>
                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300">
                  {testimonial.stats.map((stat, statIndex) => {
                    const IconComponent = stat.icon;
                    return (
                      <span key={`${testimonial.id}-${statIndex}`} className="flex items-center">
                        <IconComponent className="mr-1.5 h-3.5 w-3.5" />
                        {stat.text}
                      </span>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        );
      })}

      <div className="absolute bottom-0 left-0 right-0 flex items-center justify-center gap-3">
        <button
          type="button"
          aria-label="Previous hotspot"
          onClick={() => navigate(activeIndex - 1)}
          className="rounded-full border border-white/14 bg-white/8 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-slate-200 transition-colors duration-200 hover:bg-white/14"
        >
          Prev
        </button>
        {testimonials.map((_, index) => (
          <button
            key={index}
            type="button"
            aria-label={`Go to card ${index + 1}`}
            onClick={() => navigate(index)}
            className={[
              "h-2.5 rounded-full transition-all duration-200",
              activeIndex === index ? "w-8 bg-sky-300" : "w-2.5 bg-white/30 hover:bg-white/50",
            ].join(" ")}
          />
        ))}
        <button
          type="button"
          aria-label="Next hotspot"
          onClick={() => navigate(activeIndex + 1)}
          className="rounded-full border border-white/14 bg-white/8 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-slate-200 transition-colors duration-200 hover:bg-white/14"
        >
          Next
        </button>
      </div>
    </section>
  );
};

export default TestimonialStack;
