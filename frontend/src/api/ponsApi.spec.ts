import { afterEach, describe, expect, it, vi } from 'vitest';
import { lookupPons } from './ponsApi';

function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === 'string') return input;
  if (input instanceof URL) return input.href;
  return (input as Request).url;
}

describe('lookupPons', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns hits on success', async () => {
    const hits = [{ type: 'translation', source: 'Haus', target: 'house' }];
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ hits }),
        })
      )
    );

    const r = await lookupPons('Haus', 'deen');
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.hits).toEqual(hits);
    }
  });

  it('passes q and l params', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = requestUrl(input);
        expect(url).toContain('q=K%C3%BCche');
        expect(url).toContain('l=deuk');
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ hits: [] }),
        });
      })
    );

    await lookupPons('Küche', 'deuk');
  });

  it('returns error on HTTP failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 503,
          json: () => Promise.resolve({ error: 'PONS Tageslimit erreicht' }),
        })
      )
    );

    const r = await lookupPons('Haus');
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.message).toContain('Tageslimit');
      expect(r.status).toBe(503);
    }
  });

  it('returns error on network failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new Error('ERR_CONNECTION_REFUSED')))
    );

    const r = await lookupPons('Haus');
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.message).toContain('ERR_CONNECTION_REFUSED');
    }
  });
});
