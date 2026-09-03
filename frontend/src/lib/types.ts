export interface NakshatraInfo {
  index: number;
  name: string;
  pada: number;
  lord: string;
  fraction_elapsed: number;
}

export interface GrahaInfo {
  name: string;
  lon: number;
  sign: number;
  sign_name: string;
  degree_in_sign: string;
  house: number;
  retrograde: boolean;
  combust: boolean;
  dignity: string;
  nakshatra: NakshatraInfo;
  vargas: Record<string, number>;
}

export interface DashaPeriod {
  lord: string;
  start: string;
  end: string;
  start_jd: number;
  end_jd: number;
  years?: number;
  antardashas?: DashaPeriod[];
}

export interface ChartV1 {
  jaimini?: {
    chara_karakas?: { karakas?: Record<string, { graha: string; deg_in_sign?: number }> };
    arudha_padas?: Record<string, number>;
    karakamsa?: { sign: number; sign_name: string };
    ishta_devata?: { deity?: string; indicator_graha?: string; basis?: string };
    chara_dasha?: { sign_name: string; years: number; start: string; end: string }[];
  };
  kp?: {
    planets?: Record<string, { star_lord: string; sub_lord: string; sub_sub_lord: string }>;
    cusps?: { house?: number; star_lord?: string; sub_lord?: string }[];
  };
  bhava_chalita?: {
    houses: { house: number; madhya: number; start: number; end: number }[];
    grahas: Record<string, { house: number; in_sandhi: boolean }>;
  };
  use_chandra_lagna?: boolean;
  schema: string;
  engine_version: string;
  input: {
    date: string; time: string; lat: number; lng: number; tz: string;
    utc: string; utc_offset_hours: number; time_accuracy: string;
    ayanamsa: string; house_system: string; node_type: string;
  };
  ayanamsa_value: number;
  lagna: {
    lon: number; sign: number; sign_name: string; degree_in_sign: string;
    nakshatra: NakshatraInfo; lord: string;
  };
  grahas: Record<string, GrahaInfo>;
  bhavas: { house: number; sign: number; sign_name: string; lord: string; occupants: string[] }[];
  aspects: { from: string; to: string; type: string }[];
  panchanga: {
    tithi: { index: number; name: string; paksha: string };
    vara: { name: string; lord: string };
    nakshatra: NakshatraInfo;
    yoga: { index: number; name: string };
    karana: { index: number; name: string };
  };
  yogas: { key: string; name: string; factors: string[] }[];
  vimshottari: {
    moon_nakshatra: string;
    balance_at_birth_years: number;
    mahadashas: DashaPeriod[];
  };
  current_dasha: {
    maha: string; antar: string; pratyantar: string;
    maha_end: string; antar_end: string; pratyantar_end: string;
  } | null;
  moon_sign_name: string;
}

export const GRAHA_ABBR: Record<string, string> = {
  sun: "Su", moon: "Mo", mars: "Ma", mercury: "Me", jupiter: "Ju",
  venus: "Ve", saturn: "Sa", rahu: "Ra", ketu: "Ke",
};

export const GRAHA_LABEL: Record<string, string> = {
  sun: "Sun (Surya)", moon: "Moon (Chandra)", mars: "Mars (Mangala)",
  mercury: "Mercury (Budha)", jupiter: "Jupiter (Guru)", venus: "Venus (Shukra)",
  saturn: "Saturn (Shani)", rahu: "Rahu", ketu: "Ketu",
};

export const SIGN_SHORT = [
  "Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis",
];
