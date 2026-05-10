import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchHealth } from './fetchHealth';

describe('fetchHealth', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('returns payload on 200 JSON', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, sidecar: { status: 'ok' } }),
      })
    );
    const r = await fetchHealth();
    expect(r).toEqual({
      success: true,
      payload: { ok: true, sidecar: { status: 'ok' } },
    });
  });

  it('returns message on non-OK HTTP', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: () => Promise.resolve({}),
      })
    );
    const r = await fetchHealth();
    expect(r).toEqual({ success: false, message: 'HTTP 503' });
  });

  it('returns timeout message when request is aborted', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((_url: string, init?: RequestInit) => {
        return new Promise<Response>((_resolve, reject) => {
          const s = init?.signal;
          if (!s) {
            reject(new Error('no signal'));
            return;
          }
          if (s.aborted) {
            reject(new DOMException('Aborted', 'AbortError'));
            return;
          }
          s.addEventListener('abort', () => {
            reject(new DOMException('Aborted', 'AbortError'));
          });
        });
      })
    );
    const r = await fetchHealth(35);
    expect(r).toEqual({ success: false, message: 'Zeitüberschreitung beim Health-Check' });
  }, 10_000);

  it('returns message when JSON body is invalid', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.reject(new SyntaxError('Unexpected token')),
      })
    );
    const r = await fetchHealth();
    expect(r).toEqual({ success: false, message: 'Ungültige JSON-Antwort' });
  });
});
