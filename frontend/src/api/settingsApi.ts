import { buildApiUrl } from '@/api/buildApiUrl';
import type { AppSettings, PatchAppSettings } from '@/types/settings';

export type FetchSettingsResult =
  | { ok: true; data: AppSettings }
  | { ok: false; status: number; message: string };

export type PatchSettingsResult =
  | { ok: true; data: AppSettings }
  | { ok: false; status: number; message: string };

function readErrorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === 'object' && 'error' in body) {
    const err = (body as { error?: unknown }).error;
    if (typeof err === 'string' && err.trim()) {
      return err;
    }
  }
  return fallback;
}

/** Loads ``GET /api/settings``. */
export async function fetchSettings(): Promise<FetchSettingsResult> {
  try {
    const res = await fetch(buildApiUrl('/api/settings'), {
      headers: { Accept: 'application/json' },
    });
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      return { ok: false, status: res.status, message: 'Invalid JSON response' };
    }
    if (!res.ok) {
      return {
        ok: false,
        status: res.status,
        message: readErrorMessage(body, `HTTP ${res.status}`),
      };
    }
    return { ok: true, data: body as AppSettings };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Network error';
    return { ok: false, status: 0, message };
  }
}

/** Applies ``PATCH /api/settings`` with a JSON object body. */
export async function patchSettings(patch: PatchAppSettings): Promise<PatchSettingsResult> {
  try {
    const res = await fetch(buildApiUrl('/api/settings'), {
      method: 'PATCH',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(patch),
    });
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      return { ok: false, status: res.status, message: 'Invalid JSON response' };
    }
    if (!res.ok) {
      return {
        ok: false,
        status: res.status,
        message: readErrorMessage(body, `HTTP ${res.status}`),
      };
    }
    return { ok: true, data: body as AppSettings };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Network error';
    return { ok: false, status: 0, message };
  }
}
