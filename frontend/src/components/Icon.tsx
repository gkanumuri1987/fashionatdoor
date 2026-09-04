/** Jaathaka icon set — bespoke thin line-art, celestial + Vedic in feel, drawn
 *  to sit beside the gold Ashtadala mark. Every glyph is stroke-based and uses
 *  currentColor, so it inherits gold from text color and stays crisp at any
 *  size. Refined, never emoji-routine.
 *
 *  Usage: <Icon name="chart" className="h-5 w-5" /> */

export type IconName =
  | "about" | "chart" | "chat" | "match" | "vastu"
  | "calendar" | "palm" | "plans" | "account" | "sparkle";

const PATHS: Record<IconName, React.ReactNode> = {
  // A domed temple pavilion — the home/story page.
  about: (
    <>
      <path d="M4 11.5 12 4l8 7.5" />
      <path d="M12 4c1.6 0 2.6-.9 2.6-2M12 2v2" />
      <path d="M6 11v8.5h12V11" />
      <path d="M9.6 19.5v-4a2.4 2.4 0 0 1 4.8 0v4" />
    </>
  ),
  // North-Indian kundli diamond — the birth chart itself.
  chart: (
    <>
      <path d="M4 4h16v16H4z" />
      <path d="M12 4l8 8-8 8-8-8z" />
    </>
  ),
  // Speech bubble cradling a spark — talk to your chart.
  chat: (
    <>
      <path d="M5 5h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-7l-4.5 3.2V16H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z" />
      <path d="M12 8.2l.9 2.4 2.4.9-2.4.9-.9 2.4-.9-2.4-2.4-.9 2.4-.9z" />
    </>
  ),
  // Two interlocking rings — Kundli Milan / union.
  match: (
    <>
      <circle cx="9" cy="12" r="5.2" />
      <circle cx="15" cy="12" r="5.2" />
    </>
  ),
  // Compass rose with a direction needle — Vastu.
  vastu: (
    <>
      <circle cx="12" cy="12" r="8.4" />
      <path d="M12 5.4l2.4 6.6L12 18.6 9.6 12z" />
      <path d="M12 3.2v1.4M12 19.4v1.4M3.2 12h1.4M19.4 12h1.4" />
    </>
  ),
  // Almanac leaf with a spark inside — the festival calendar.
  calendar: (
    <>
      <path d="M4.5 6.5a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2h-11a2 2 0 0 1-2-2z" />
      <path d="M4.5 9.5h15M8 3.5v3M16 3.5v3" />
      <path d="M12 12.4l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z" />
    </>
  ),
  // Open palm with the three great lines — palmistry.
  palm: (
    <>
      <path d="M8.5 13V6.2a1.25 1.25 0 0 1 2.5 0V11" />
      <path d="M11 11V5a1.25 1.25 0 0 1 2.5 0v6" />
      <path d="M13.5 11.5V6a1.25 1.25 0 0 1 2.5 0v7" />
      <path d="M16 13.5v-3a1.25 1.25 0 0 1 2.5 0V15a6 6 0 0 1-6 6h-1.3a6 6 0 0 1-4.2-1.7l-3-3a1.3 1.3 0 0 1 1.9-1.9l1.6 1.5V8.4a1.25 1.25 0 0 1 2.5 0V13.5" />
    </>
  ),
  // Lotus in bloom — the auspicious plans / membership mark.
  plans: (
    <>
      <path d="M12 20c-2.4 0-4.4-3-4.4-6.6 0-2.9 1.8-5.4 4.4-6.9 2.6 1.5 4.4 4 4.4 6.9C16.4 17 14.4 20 12 20z" />
      <path d="M12 20C7.3 20 4 16.6 4 12.4c2.7 0 5 1.6 6 3.7" />
      <path d="M12 20c4.7 0 8-3.4 8-7.6-2.7 0-5 1.6-6 3.7" />
    </>
  ),
  // Portrait bust — the account.
  account: (
    <>
      <circle cx="12" cy="8.5" r="3.6" />
      <path d="M5 20a7 7 0 0 1 14 0" />
    </>
  ),
  // Four-point spark — accents / plans teaser.
  sparkle: (
    <path d="M12 3l1.8 6.2L20 11l-6.2 1.8L12 19l-1.8-6.2L4 11l6.2-1.8z" />
  ),
};

export default function Icon({ name, className = "h-5 w-5", strokeWidth = 1.6 }:
  { name: IconName; className?: string; strokeWidth?: number }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"
         className={className} aria-hidden role="img"
         xmlns="http://www.w3.org/2000/svg">
      {PATHS[name]}
    </svg>
  );
}
