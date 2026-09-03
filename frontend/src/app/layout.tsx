import type { Metadata, Viewport } from "next";
import { Fraunces, Inter, Noto_Sans_Devanagari, Noto_Sans_Telugu } from "next/font/google";
import "./globals.css";
import { LangProvider } from "@/lib/i18n";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
  axes: ["opsz"],
});

const notoTelugu = Noto_Sans_Telugu({
  subsets: ["telugu"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-noto-telugu",
  display: "swap",
});

const notoDevanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-noto-deva",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Jyotish AI — Vedic Birth Chart & Life Reading",
  description:
    "Accurate Vedic kundli computed with Swiss Ephemeris — nakshatras, dashas, yogas — with AI readings grounded in classical texts.",
};

export const viewport: Viewport = {
  themeColor: "#0a0714",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en"
          className={`${inter.variable} ${fraunces.variable} ${notoTelugu.variable} ${notoDevanagari.variable}`}>
      <body className="font-sans antialiased">
        <LangProvider>{children}</LangProvider>
      </body>
    </html>
  );
}
