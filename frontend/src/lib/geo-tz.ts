/** Map the browser's IANA timezone to a representative {tz, lat, lng} so the
 *  personal Jyothishyam is computed where the person actually is now — its
 *  sunrise, tarabala day-boundary and Rahu kalam are location-dependent, not
 *  just offset-dependent. Falls back to the birth place when unknown. */

const TZ_COORDS: Record<string, [number, number]> = {
  "Asia/Kolkata": [17.385, 78.4867], "Asia/Calcutta": [17.385, 78.4867],
  "Asia/Colombo": [6.9271, 79.8612], "Asia/Kathmandu": [27.7172, 85.324],
  "Asia/Dubai": [25.2048, 55.2708], "Asia/Qatar": [25.2854, 51.531],
  "Asia/Riyadh": [24.7136, 46.6753], "Asia/Kuwait": [29.3759, 47.9774],
  "Asia/Singapore": [1.3521, 103.8198], "Asia/Kuala_Lumpur": [3.139, 101.6869],
  "Asia/Tokyo": [35.6762, 139.6503], "Asia/Hong_Kong": [22.3193, 114.1694],
  "Europe/London": [51.5074, -0.1278], "Europe/Dublin": [53.3498, -6.2603],
  "Europe/Paris": [48.8566, 2.3522], "Europe/Berlin": [52.52, 13.405],
  "Europe/Zurich": [47.3769, 8.5417], "Europe/Amsterdam": [52.3676, 4.9041],
  "America/New_York": [40.7128, -74.006], "America/Toronto": [43.6532, -79.3832],
  "America/Chicago": [41.8781, -87.6298], "America/Denver": [39.7392, -104.9903],
  "America/Los_Angeles": [34.0522, -118.2437], "America/Vancouver": [49.2827, -123.1207],
  "America/Phoenix": [33.4484, -112.074], "America/Sao_Paulo": [-23.5505, -46.6333],
  "Australia/Sydney": [-33.8688, 151.2093], "Australia/Melbourne": [-37.8136, 144.9631],
  "Australia/Perth": [-31.9523, 115.8613], "Australia/Brisbane": [-27.4698, 153.0251],
  "Pacific/Auckland": [-36.8485, 174.7633], "Africa/Johannesburg": [-26.2041, 28.0473],
};

export interface TzLoc { tz: string; lat: number | null; lng: number | null }

export function currentTzLoc(): TzLoc {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Kolkata";
    const c = TZ_COORDS[tz];
    return c ? { tz, lat: c[0], lng: c[1] } : { tz, lat: null, lng: null };
  } catch {
    return { tz: "Asia/Kolkata", lat: null, lng: null };
  }
}
