import { describe, expect, it } from 'vitest';
import { formatHealthFooterLine } from './formatHealthFooterLine';

describe('formatHealthFooterLine', () => {
  it('formats loading', () => {
    expect(formatHealthFooterLine({ kind: 'loading' })).toBe('Status: wird geladen …');
  });

  it('formats error', () => {
    expect(formatHealthFooterLine({ kind: 'error', message: 'nope' })).toBe('Status: nope');
  });

  it('formats ok with sidecar', () => {
    expect(
      formatHealthFooterLine({
        kind: 'ok',
        payload: { ok: true, sidecar: { status: 'ok' } },
      })
    ).toBe('API: OK · Sidecar: OK');
  });

  it('labels inspect_error from SSE health fallback', () => {
    expect(
      formatHealthFooterLine({
        kind: 'ok',
        payload: {
          ok: true,
          sidecar: { status: 'ok', ollama: { state: 'inspect_error' } },
        },
      })
    ).toBe('API: OK · Sidecar: OK · Ollama: Sidecar-Inspect fehlgeschlagen');
  });

  it('includes Ollama container state when sidecar inspect returns it', () => {
    expect(
      formatHealthFooterLine({
        kind: 'ok',
        payload: {
          ok: true,
          sidecar: { status: 'ok', ollama: { state: 'exited', name: '/x' } },
        },
      })
    ).toBe('API: OK · Sidecar: OK · Ollama: gestoppt');
  });

  it('formats ok without sidecar', () => {
    expect(
      formatHealthFooterLine({
        kind: 'ok',
        payload: { ok: true },
      })
    ).toBe('API: OK · Sidecar: nicht konfiguriert');
  });

  it('includes sidecar detail when sidecar reports error', () => {
    expect(
      formatHealthFooterLine({
        kind: 'ok',
        payload: { ok: true, sidecar: { status: 'error', detail: 'timeout' } },
      })
    ).toBe('API: OK · Sidecar: Fehler · (timeout)');
  });
});
