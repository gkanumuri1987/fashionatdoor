/** Residence locations for panchanga timing. Each carries a tz + representative
 *  coordinates. The profile saves a key to user_metadata.residence; the
 *  Jyothishyam uses it (falling back to browser-detected, then the birth place). */

import { currentTzLoc, type TzLoc } from "@/lib/geo-tz";

export interface Loc { key: string; label: string; tz: string; lat: number; lng: number }

export const LOCATIONS: Loc[] = [
  { key: "in", label: "🇮🇳 India", tz: "Asia/Kolkata", lat: 17.385, lng: 78.4867 },
  { key: "lk", label: "🇱🇰 Sri Lanka", tz: "Asia/Colombo", lat: 6.9271, lng: 79.8612 },
  { key: "np", label: "🇳🇵 Nepal", tz: "Asia/Kathmandu", lat: 27.7172, lng: 85.324 },
  { key: "gulf", label: "🇦🇪 Gulf (UAE)", tz: "Asia/Dubai", lat: 25.2048, lng: 55.2708 },
  { key: "sg", label: "🇸🇬 Singapore", tz: "Asia/Singapore", lat: 1.3521, lng: 103.8198 },
  { key: "my", label: "🇲🇾 Malaysia", tz: "Asia/Kuala_Lumpur", lat: 3.139, lng: 101.6869 },
  { key: "uk", label: "🇬🇧 United Kingdom", tz: "Europe/London", lat: 51.5074, lng: -0.1278 },
  { key: "eu", label: "🇪🇺 Europe (Central)", tz: "Europe/Berlin", lat: 52.52, lng: 13.405 },
  { key: "us_east", label: "🇺🇸 US East", tz: "America/New_York", lat: 40.7128, lng: -74.006 },
  { key: "us_central", label: "🇺🇸 US Central", tz: "America/Chicago", lat: 41.8781, lng: -87.6298 },
  { key: "us_mountain", label: "🇺🇸 US Mountain", tz: "America/Denver", lat: 39.7392, lng: -104.9903 },
  { key: "us_west", label: "🇺🇸 US West", tz: "America/Los_Angeles", lat: 34.0522, lng: -118.2437 },
  { key: "ca", label: "🇨🇦 Canada (East)", tz: "America/Toronto", lat: 43.6532, lng: -79.3832 },
  { key: "au_syd", label: "🇦🇺 Australia (Sydney)", tz: "Australia/Sydney", lat: -33.8688, lng: 151.2093 },
  { key: "au_per", label: "🇦🇺 Australia (Perth)", tz: "Australia/Perth", lat: -31.9523, lng: 115.8613 },
  { key: "nz", label: "🇳🇿 New Zealand", tz: "Pacific/Auckland", lat: -36.8485, lng: 174.7633 },
  { key: "za", label: "🇿🇦 South Africa", tz: "Africa/Johannesburg", lat: -26.2041, lng: 28.0473 },
];

export function locByKey(key: string | null | undefined): Loc | null {
  return LOCATIONS.find((l) => l.key === key) ?? null;
}

/** Resolve the timing location: saved residence → browser-detected → null
 *  (backend then uses the birth place). */
export function resolveTiming(residenceKey: string | null | undefined): TzLoc {
  const saved = locByKey(residenceKey);
  if (saved) return { tz: saved.tz, lat: saved.lat, lng: saved.lng };
  return currentTzLoc();
}

/** Resolved timing + a human label (matched region name, or the raw tz). */
export function resolveTimingLabeled(residenceKey: string | null | undefined): TzLoc & { label: string; source: "profile" | "device" } {
  const saved = locByKey(residenceKey);
  if (saved) return { tz: saved.tz, lat: saved.lat, lng: saved.lng, label: saved.label, source: "profile" };
  const detected = currentTzLoc();
  const match = LOCATIONS.find((l) => l.tz === detected.tz);
  return { ...detected, label: match ? match.label : detected.tz, source: "device" };
}
