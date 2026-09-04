"use client";

import { useId } from "react";

/** Jaathaka logo — an eight-pointed radiant star (Ashtadala / Star of Lakshmi),
 *  an auspicious Hindu celestial form, with a central bindu and a graha in
 *  orbit. Curvy, iconic, scales cleanly to a favicon. Pure inline SVG,
 *  theme-independent, gold-leaf gradient. */

export function JaathakaMark({ size = 40, className = "" }: { size?: number; className?: string }) {
  const uid = useId().replace(/:/g, "");
  const gold = `jk-gold-${uid}`;
  const core = `jk-core-${uid}`;
  return (
    <svg width={size} height={size} viewBox="0 0 120 120" fill="none"
         className={className} aria-hidden role="img"
         xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id={gold} x1="18" y1="10" x2="102" y2="110"
                        gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#f8ea9e" />
          <stop offset="0.5" stopColor="#dcae2f" />
          <stop offset="1" stopColor="#9c6f0d" />
        </linearGradient>
        <radialGradient id={core} cx="0.5" cy="0.42" r="0.6">
          <stop offset="0" stopColor="#fff6d2" />
          <stop offset="1" stopColor="#ecc453" />
        </radialGradient>
      </defs>

      {/* Faint orbit ring — the sky in motion */}
      <circle cx="60" cy="60" r="56" fill="none" stroke={`url(#${gold})`}
              strokeWidth="2" opacity="0.28" />

      {/* Eight-pointed radiant star — Ashtadala, the auspicious eight-petalled form */}
      <path d="M60 8 L67.65 41.52 L96.77 23.23 L78.48 52.35 L112 60
               L78.48 67.65 L96.77 96.77 L67.65 78.48 L60 112 L52.35 78.48
               L23.23 96.77 L41.52 67.65 L8 60 L41.52 52.35 L23.23 23.23
               L52.35 41.52 Z"
            fill={`url(#${gold})`} />

      {/* Luminous central bindu */}
      <circle cx="60" cy="60" r="13" fill={`url(#${core})`} />

      {/* A single graha travelling the orbit — the computed-motion accent */}
      <circle cx="103" cy="34" r="4" fill="#fff6d2" opacity="0.95" />
    </svg>
  );
}

export default function Logo({ size = 34, wordmark = true, className = "" }:
  { size?: number; wordmark?: boolean; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <JaathakaMark size={size} />
      {wordmark && (
        <span className="heading-display text-2xl leading-none tracking-tight">Jaathaka</span>
      )}
    </span>
  );
}
