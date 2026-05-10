import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchHealth } from './fetchHealth';

describe('fetchHealth', () => {
  afterEach(() => {
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
