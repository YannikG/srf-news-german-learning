import { getApiBaseUrl } from '@/config/apiBase';
import type { HealthPayload } from './healthTypes';

export type FetchHealthResult =
  | { success: true; payload: HealthPayload }
  | { success: false; message: string };

function isAbortError(e: unknown): boolean {
  if (e instanceof DOMException && e.name === 'AbortError') {
    return true;
  }
  if (e instanceof Error && e.name === 'AbortError') {
    return true;
  }
  return false;
}

/**
 * Performs ``GET /api/health`` and parses JSON; no UI state.
 *
 * @param timeoutMs Abort the request after this many milliseconds (default 15s)
 *   so the app shell does not stay on ``loading`` forever if the server hangs.
 */
export async function fetchHealth(timeoutMs: number = 15_000): Promise<FetchHealthResult> {
  const base = getApiBaseUrl();
  const url = `${base}/api/health`;
  const controller = new AbortController();
  const kill = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });
    if (!res.ok) {
      return { success: false, message: `HTTP ${res.status}` };
    }
    let payload: HealthPayload;
    try {
      payload = (await res.json()) as HealthPayload;
    } catch {
      return { success: false, message: 'Ungültige JSON-Antwort' };
    }
    return { success: true, payload };
  } catch (e) {
    if (isAbortError(e)) {
      return { success: false, message: 'Zeitüberschreitung beim Health-Check' };
    }
    const message = e instanceof Error ? e.message : 'Unbekannter Fehler';
    return { success: false, message };
  } finally {
    clearTimeout(kill);
  }
}
