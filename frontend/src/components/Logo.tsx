"use client";

/** Jaathaka logo — a waxing crescent cradling a guiding sparkle-star, with a
 *  single graha-dot in orbit. Curvy, iconic, scales cleanly to a favicon.
 *  Pure inline SVG, theme-independent, gold-leaf gradient. */

export function JaathakaMark({ size = 40, className = "" }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 120 120" fill="none"
         className={className} aria-hidden role="img"
         xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="jk-gold" x1="18" y1="8" x2="104" y2="112"
                        gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#f8ea9e" />
          <stop offset="0.5" stopColor="#dcae2f" />
          <stop offset="1" stopColor="#9c6f0d" />
        </linearGradient>
        <radialGradient id="jk-star" cx="0.5" cy="0.42" r="0.6">
          <stop offset="0" stopColor="#fff6d2" />
          <stop offset="1" stopColor="#ecc453" />
        </radialGradient>
      </defs>

      {/* Waxing crescent — a smooth curvy sickle opening to the upper-right */}
      <path d="M70 8
               A54 54 0 1 0 70 112
               A42 42 0 1 1 70 8 Z"
            fill="url(#jk-gold)" />

      {/* Guiding sparkle-star cradled in the crescent's hollow, with a long
          lower ray so it reads as a guiding star, not a generic 5-point */}
      <path d="M82 40
               l4.6 12.4 12.8 1.2 -9.8 8.4 3 12.6
               -10.6 -6.8 -10.6 6.8 3 -12.6 -9.8 -8.4 12.8 -1.2 Z"
            fill="url(#jk-star)" />

      {/* A single graha in orbit — the computed-motion accent */}
      <circle cx="34" cy="40" r="3.4" fill="#fff6d2" opacity="0.92" />
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
