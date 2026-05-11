import { buildApiUrl } from '@/api/buildApiUrl';
import type { PonsHit } from '@/types/pons';

export type PonsLookupResult =
  | { ok: true; hits: PonsHit[] }
  | { ok: false; status: number; message: string };

async function readErrorMessage(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { error?: string };
    if (body.error) return body.error;
  } catch {
    /* ignore */
  }
  return `HTTP ${res.status}`;
}

export async function lookupPons(q: string, l?: string): Promise<PonsLookupResult> {
  const params = new URLSearchParams({ q });
  if (l?.trim()) {
    params.set('l', l.trim());
  }
  const path = `/api/external/pons/dictionary?${params.toString()}`;
  try {
    const res = await fetch(buildApiUrl(path), {
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      return { ok: false, status: res.status, message: await readErrorMessage(res) };
    }
    const body = (await res.json()) as { hits?: PonsHit[] };
    return { ok: true, hits: body.hits ?? [] };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Netzwerkfehler';
    return { ok: false, status: 0, message };
  }
}
