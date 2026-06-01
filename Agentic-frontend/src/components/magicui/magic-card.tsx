"use client";

import React, { useCallback, useEffect, useRef } from "react";
import { cn } from "../../lib/utils";

interface MagicCardProps {
  children: React.ReactNode;
  className?: string;
  gradientSize?: number;
  gradientColor?: string;
  gradientOpacity?: number;
  gradientFrom?: string;
  gradientTo?: string;
}

export function MagicCard({
  children,
  className,
  gradientSize = 200,
  gradientColor = "#262626",
  gradientOpacity = 0.8,
  gradientFrom = "#9E7AFF",
  gradientTo = "#FE8BBB",
}: MagicCardProps) {
  const divRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!divRef.current || !overlayRef.current) return;

      const rect = divRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      overlayRef.current.style.background = `radial-gradient(${gradientSize}px circle at ${x}px ${y}px, ${gradientColor} 0%, transparent 50%)`;
    },
    [gradientSize, gradientColor]
  );

  useEffect(() => {
    if (!divRef.current || !overlayRef.current) return;

    overlayRef.current.style.background = `radial-gradient(${gradientSize}px circle at 0px 0px, ${gradientColor} 0%, transparent 50%)`;
  }, [gradientSize, gradientColor]);

  return (
    <div
      ref={divRef}
      onMouseMove={handleMouseMove}
      className={cn(
        "group relative overflow-hidden rounded-lg border border-slate-800 bg-slate-900 p-4",
        className
      )}
      style={{
        "--gradient-from": gradientFrom,
        "--gradient-to": gradientTo,
        "--gradient-opacity": gradientOpacity,
      } as React.CSSProperties}
    >
      <div
        ref={overlayRef}
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          opacity: 0,
        }}
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: `linear-gradient(135deg, var(--gradient-from), var(--gradient-to))`,
          opacity: 0,
          maskImage: `radial-gradient(${gradientSize}px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), black 0%, transparent 50%)`,
          WebkitMaskImage: `radial-gradient(${gradientSize}px circle at var(--mouse-x, 0px) var(--mouse-y, 0px), black 0%, transparent 50%)`,
        }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
} 