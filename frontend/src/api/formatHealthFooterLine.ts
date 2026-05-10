import type { HealthState } from './healthTypes';

/** Maps poll state to a single German footer line (presentation only). */
export function formatHealthFooterLine(state: HealthState): string {
  if (state.kind === 'loading') {
    return 'Status: wird geladen …';
  }
  if (state.kind === 'error') {
    return `Status: ${state.message}`;
  }
  const apiOk = state.payload.ok;
  const parts: string[] = [];
  parts.push(apiOk ? 'API: OK' : 'API: Fehler');
  const sc = state.payload.sidecar;
  if (sc) {
    const label = sc.status === 'ok' ? 'OK' : 'Fehler';
    parts.push(`Sidecar: ${label}`);
    if (sc.detail) {
      parts.push(`(${sc.detail})`);
    }
  } else {
    parts.push('Sidecar: nicht konfiguriert');
  }
  return parts.join(' · ');
}
