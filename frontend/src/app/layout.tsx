import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Jyotish AI — Vedic Birth Chart & Life Reading",
  description:
    "Accurate Vedic kundli computed with Swiss Ephemeris — nakshatras, dashas, yogas — with AI readings grounded in classical texts.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
