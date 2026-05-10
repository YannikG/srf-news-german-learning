import { getApiBaseUrl } from '@/config/apiBase';

/** Absolute or same-origin path for ``fetch`` (matches ``fetchHealth`` pattern). */
export function buildApiUrl(path: string): string {
  const base = getApiBaseUrl().replace(/\/+$/, '');
  const p = path.startsWith('/') ? path : `/${path}`;
  return base ? `${base}${p}` : p;
}
