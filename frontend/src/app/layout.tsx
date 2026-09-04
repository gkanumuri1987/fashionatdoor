import type { Metadata, Viewport } from "next";
import { Fraunces, Inter, Mandali, Noto_Sans_Devanagari } from "next/font/google";
import "./globals.css";
import { LangProvider } from "@/lib/i18n";
import SideNav from "@/components/SideNav";
import TodayPopup from "@/components/TodayPopup";

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

// Mandali — Purushoth Kumar Guttula's Telugu face (single 400 weight;
// heavier weights are browser-synthesized).
const mandali = Mandali({
  subsets: ["telugu"],
  weight: "400",
  variable: "--font-telugu",
  display: "swap",
});

const notoDevanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-noto-deva",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Jaathaka — Vedic Birth Chart & Jyothishyam",
  description:
    "Jaathaka — your Vedic jaathakam computed to arc-second precision (never AI-guessed): kundli, readings, Jyothishyam, Kundli Milan, panchanga calendar.",
};

export const viewport: Viewport = {
  themeColor: "#0a0714",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en"
          className={`${inter.variable} ${fraunces.variable} ${mandali.variable} ${notoDevanagari.variable}`}>
      <body className="font-sans antialiased">
        <LangProvider>
          <SideNav />
          <TodayPopup />
          <div className="lg:pl-60">{children}</div>
        </LangProvider>
      </body>
    </html>
  );
}
