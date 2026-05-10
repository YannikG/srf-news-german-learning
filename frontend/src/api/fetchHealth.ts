import { getApiBaseUrl } from '@/config/apiBase';
import type { HealthPayload } from './healthTypes';

export type FetchHealthResult =
  | { success: true; payload: HealthPayload }
  | { success: false; message: string };

/** Performs ``GET /api/health`` and parses JSON; no UI state. */
export async function fetchHealth(): Promise<FetchHealthResult> {
  const base = getApiBaseUrl();
  const url = `${base}/api/health`;
  try {
    const res = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!res.ok) {
      return { success: false, message: `HTTP ${res.status}` };
    }
    const payload = (await res.json()) as HealthPayload;
    return { success: true, payload };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Unbekannter Fehler';
    return { success: false, message };
  }
}
