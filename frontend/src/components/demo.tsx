"use client";

import React from "react";
import { ContainerScroll } from "@/components/ui/container-scroll-animation";

const cityOpsImage =
  "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1600&q=80";

export function HeroScrollDemo() {
  return (
    <section className="flex flex-col overflow-hidden rounded-[2rem] bg-slate-950/95 pb-24 pt-10 text-white shadow-[0_24px_60px_rgba(15,23,42,0.24)] ring-1 ring-white/10 md:pt-20">
      <ContainerScroll
        titleComponent={
          <>
            <p className="mb-5 text-xs font-semibold uppercase tracking-[0.4em] text-amber-300/90">
              Urban Sentinel Preview
            </p>
            <h2 className="text-3xl font-semibold text-white md:text-5xl">
              See the city before you
              <br />
              <span className="mt-1 block bg-gradient-to-r from-cyan-300 via-sky-200 to-amber-200 bg-clip-text text-4xl font-bold leading-none text-transparent md:text-[5.5rem]">
                step into it
              </span>
            </h2>
            <p className="mx-auto mt-6 max-w-3xl text-sm leading-7 text-slate-300 md:text-lg">
              Scroll through a cinematic preview of the command center experience, built for live
              civic monitoring across traffic, safety, weather, and neighborhood risk signals.
            </p>
          </>
        }
      >
        <div className="relative h-full w-full overflow-hidden rounded-2xl">
          <img
            src={cityOpsImage}
            alt="Night city operations view"
            className="mx-auto h-full w-full rounded-2xl object-cover object-center"
            draggable={false}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/20 to-transparent" />
          <div className="absolute inset-x-0 bottom-0 grid gap-3 p-4 text-left md:grid-cols-3 md:p-8">
            <article className="rounded-2xl border border-white/10 bg-slate-950/70 p-4 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Response</p>
              <strong className="mt-2 block text-3xl text-white">10s</strong>
              <span className="text-sm text-slate-300">Live environment refresh cycle</span>
            </article>
            <article className="rounded-2xl border border-white/10 bg-slate-950/70 p-4 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Coverage</p>
              <strong className="mt-2 block text-3xl text-white">11</strong>
              <span className="text-sm text-slate-300">Integrated monitoring streams</span>
            </article>
            <article className="rounded-2xl border border-white/10 bg-slate-950/70 p-4 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Priority</p>
              <strong className="mt-2 block text-3xl text-amber-300">Hotspots</strong>
              <span className="text-sm text-slate-300">Immediate attention zones surfaced first</span>
            </article>
          </div>
        </div>
      </ContainerScroll>
    </section>
  );
}
