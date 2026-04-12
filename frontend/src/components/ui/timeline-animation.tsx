"use client";

import * as React from "react";
import { motion, useInView } from "framer-motion";

import { cn } from "@/lib/utils";

export interface TimelineContentProps
  extends React.ComponentPropsWithoutRef<"div"> {
  as?: React.ElementType;
  animationNum?: number;
  customVariants?: Record<string, any>;
  timelineRef?: React.RefObject<HTMLElement>;
}

export function TimelineContent({
  as: Comp = "div",
  className,
  animationNum = 0,
  customVariants,
  timelineRef,
  ...props
}: TimelineContentProps) {
  const ref = React.useRef<HTMLDivElement>(null);
  const inView = useInView(timelineRef ?? ref, { once: true, margin: "-160px" });

  const MotionComponent = React.useMemo(() => {
    return motion(Comp) as unknown as React.ComponentType<any>;
  }, [Comp]);

  return (
    <MotionComponent
      ref={timelineRef ? undefined : ref}
      className={cn(className)}
      initial="hidden"
      animate={inView ? "visible" : "hidden"}
      variants={customVariants}
      custom={animationNum}
      {...props}
    />
  );
}
