import type { LocationQuery } from 'vue-router';

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

/** First scalar string for a route query value (handles ``string[]`` from duplicate keys). */
export function parseIsoDateQueryParam(value: unknown): string | null {
  const raw = Array.isArray(value) ? value[0] : value;
  if (typeof raw !== 'string' || !ISO_DATE.test(raw)) return null;
  return raw;
}

/** Drop null/empty entries; first element only for arrays (stable ``router.replace`` payloads). */
export function flattenLocationQuery(query: LocationQuery): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, val] of Object.entries(query)) {
    const first = Array.isArray(val) ? val[0] : val;
    if (typeof first === 'string' && first.length > 0) {
      out[key] = first;
    }
  }
  return out;
}

/** Local calendar date as ``YYYY-MM-DD`` (browser timezone). */
export function localIsoDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}
