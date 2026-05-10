import { buildApiUrl } from '@/api/buildApiUrl';
import {
  CEFR_LEVELS,
  TRANSLATION_LANGUAGES,
  type AppSettings,
  type CefrLevel,
  type PatchAppSettings,
  type TranslationLanguage,
} from '@/types/settings';

export type FetchSettingsResult =
  | { ok: true; data: AppSettings }
  | { ok: false; status: number; message: string };

export type PatchSettingsResult =
  | { ok: true; data: AppSettings }
  | { ok: false; status: number; message: string };

type SettingsHttpResult = FetchSettingsResult;

const MSG_INVALID_JSON = 'Ungültige JSON-Antwort';
const MSG_NETWORK = 'Netzwerkfehler';
const MSG_INVALID_SHAPE = 'Unerwartetes Antwortformat vom Server.';

function readErrorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === 'object' && 'error' in body) {
    const err = (body as { error?: unknown }).error;
    if (typeof err === 'string' && err.trim()) {
      return err;
    }
  }
  return fallback;
}

function isCefrLevel(value: string): value is CefrLevel {
  return (CEFR_LEVELS as readonly string[]).includes(value);
}

function isTranslationLanguage(value: string): value is TranslationLanguage {
  return (TRANSLATION_LANGUAGES as readonly string[]).includes(value);
}

/** Integer, null, or absent (treat absent as null when building ``AppSettings``). */
function isIntOrNullish(value: unknown): value is number | null | undefined {
  if (value === null || value === undefined) {
    return true;
  }
  return typeof value === 'number' && Number.isInteger(value);
}

/** Narrow ``GET``/``PATCH`` JSON to ``AppSettings`` or reject. */
export function parseAppSettings(body: unknown): AppSettings | null {
  if (!body || typeof body !== 'object') {
    return null;
  }
  const o = body as Record<string, unknown>;
  const dc = o.default_cefr;
  const tl = o.translation_language;
  if (typeof dc !== 'string' || !isCefrLevel(dc)) {
    return null;
  }
  if (typeof tl !== 'string' || !isTranslationLanguage(tl)) {
    return null;
  }
  if (!isIntOrNullish(o.retrieval_top_k)) {
    return null;
  }
  if (!isIntOrNullish(o.retrieval_context_max_chars)) {
    return null;
  }
  return {
    default_cefr: dc,
    translation_language: tl,
    retrieval_top_k: o.retrieval_top_k ?? null,
    retrieval_context_max_chars: o.retrieval_context_max_chars ?? null,
  };
}

/** Shared JSON parse, HTTP error mapping, and ``parseAppSettings`` for both verbs. */
async function interpretSettingsResponse(res: Response): Promise<SettingsHttpResult> {
  let body: unknown;
  try {
    body = await res.json();
  } catch {
    return { ok: false, status: res.status, message: MSG_INVALID_JSON };
  }
  if (!res.ok) {
    return {
      ok: false,
      status: res.status,
      message: readErrorMessage(body, `HTTP ${res.status}`),
    };
  }
  const data = parseAppSettings(body);
  if (!data) {
    return { ok: false, status: res.status, message: MSG_INVALID_SHAPE };
  }
  return { ok: true, data };
}

/** Loads ``GET /api/settings``. */
export async function fetchSettings(): Promise<FetchSettingsResult> {
  try {
    const res = await fetch(buildApiUrl('/api/settings'), {
      headers: { Accept: 'application/json' },
    });
    return await interpretSettingsResponse(res);
  } catch (e) {
    const message = e instanceof Error ? e.message : MSG_NETWORK;
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
    return await interpretSettingsResponse(res);
  } catch (e) {
    const message = e instanceof Error ? e.message : MSG_NETWORK;
    return { ok: false, status: 0, message };
  }
}
