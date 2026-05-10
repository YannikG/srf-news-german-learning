import type { HealthState } from './healthTypes';

/** Docker-style container ``state`` to short German label (footer and header). */
export function formatOllamaContainerStateLabel(state: string): string {
  const s = state.trim().toLowerCase();
  const map: Record<string, string> = {
    running: 'läuft',
    exited: 'gestoppt',
    created: 'erstellt',
    paused: 'pausiert',
    restarting: 'Neustart',
    dead: 'tot',
    removing: 'wird entfernt',
    inspect_error: 'Sidecar-Inspect fehlgeschlagen',
    unknown: 'unbekannt',
  };
  return map[s] ?? state;
}

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
    if (sc.status === 'ok' && sc.ollama?.state) {
      parts.push(`Ollama: ${formatOllamaContainerStateLabel(sc.ollama.state)}`);
    }
    if (sc.detail) {
      parts.push(`(${sc.detail})`);
    }
  } else {
    parts.push('Sidecar: nicht konfiguriert');
  }
  return parts.join(' · ');
}
