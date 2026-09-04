"use client";

/** Jaathaka logo — a curvy crescent that flows into an orbital swirl (the
 *  path of the grahas) with a guiding star, all in gold leaf. Renders the mark
 *  alone or with the wordmark. Pure inline SVG, theme-independent. */

export function JaathakaMark({ size = 40, className = "" }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none"
         className={className} aria-hidden role="img"
         xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="jk-gold" x1="15" y1="8" x2="85" y2="92"
                        gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#f6e08e" />
          <stop offset="0.5" stopColor="#d9ab2e" />
          <stop offset="1" stopColor="#a5760f" />
        </linearGradient>
        <radialGradient id="jk-star" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#fff4c8" />
          <stop offset="1" stopColor="#e9c04a" />
        </radialGradient>
      </defs>

      {/* Crescent moon — the outer curvy body */}
      <path d="M64 12
               A40 40 0 1 0 64 88
               A32 32 0 1 1 64 12 Z"
            fill="url(#jk-gold)" />

      {/* Orbital swirl — a flowing tail curving out of the crescent (the graha path) */}
      <path d="M50 50
               C 62 40, 82 42, 88 58
               C 92 70, 80 84, 66 82"
            stroke="url(#jk-gold)" strokeWidth="5.5" strokeLinecap="round" fill="none"
            opacity="0.92" />

      {/* Guiding star at the orbit's crest */}
      <path d="M84 24
               l2.4 6.2 6.6 0.6 -5 4.4 1.6 6.4 -5.6 -3.6 -5.6 3.6 1.6 -6.4 -5 -4.4 6.6 -0.6 Z"
            fill="url(#jk-star)" />
      {/* small twinkle */}
      <circle cx="70" cy="60" r="2.2" fill="#fff4c8" opacity="0.9" />
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
