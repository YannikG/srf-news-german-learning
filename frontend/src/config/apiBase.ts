/**
 * API origin for absolute fetch URLs. Empty string means same origin (Docker or Vite proxy).
 */
export function getApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (raw === undefined || raw === null) {
    return '';
  }
  return String(raw).replace(/\/+$/, '');
}
