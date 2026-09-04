/** Indian-convention date display (DD/MM/YYYY). Input is an ISO date string
 *  ("YYYY-MM-DD" or a full ISO datetime); output is dd/mm/yyyy. Non-ISO or
 *  empty input is returned unchanged so callers never crash on bad data. */

export function toDDMMYYYY(iso: string | null | undefined): string {
  if (!iso) return "";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return iso;
  return `${m[3]}/${m[2]}/${m[1]}`;
}

/** Day + month only (DD/MM), e.g. for a compact weekly-forecast row. */
export function toDDMM(iso: string | null | undefined): string {
  if (!iso) return "";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return iso;
  return `${m[3]}/${m[2]}`;
}
