import { mount } from '@vue/test-utils';
import { defineComponent, nextTick } from 'vue';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { PonsHit } from '@/types/pons';
import { usePonsLookup } from './usePonsLookup';

function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === 'string') return input;
  if (input instanceof URL) return input.href;
  return (input as Request).url;
}

function healthResponse(ponsAvailable: boolean) {
  return {
    ok: true,
    json: () => Promise.resolve({ ok: true, pons: { available: ponsAvailable } }),
  };
}

const sampleHits: PonsHit[] = [
  {
    type: 'translation',
    source: 'Haus',
    target: 'house',
  },
];

describe('usePonsLookup', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('detects ponsAvailable from health endpoint', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = requestUrl(input);
      if (url.includes('/api/health')) {
        return Promise.resolve(healthResponse(true));
      }
      return Promise.reject(new Error(`unexpected ${url}`));
    });
    vi.stubGlobal('fetch', fetchMock);

    let composable: ReturnType<typeof usePonsLookup> | undefined;
    const Cmp = defineComponent({
      setup() {
        composable = usePonsLookup();
        return composable;
      },
      template: '<div />',
    });
    mount(Cmp);

    await nextTick();
    await Promise.resolve();
    await nextTick();

    expect(composable!.ponsAvailable.value).toBe(true);
  });

  it('sets ponsAvailable false when health says unavailable', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = requestUrl(input);
      if (url.includes('/api/health')) {
        return Promise.resolve(healthResponse(false));
      }
      return Promise.reject(new Error(`unexpected ${url}`));
    });
    vi.stubGlobal('fetch', fetchMock);

    let composable: ReturnType<typeof usePonsLookup> | undefined;
    const Cmp = defineComponent({
      setup() {
        composable = usePonsLookup();
        return composable;
      },
      template: '<div />',
    });
    mount(Cmp);

    await nextTick();
    await Promise.resolve();
    await nextTick();

    expect(composable!.ponsAvailable.value).toBe(false);
  });

  it('lookup returns hits and caches result', async () => {
    let lookupCallCount = 0;
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = requestUrl(input);
      if (url.includes('/api/health')) {
        return Promise.resolve(healthResponse(true));
      }
      if (url.includes('/api/external/pons/dictionary')) {
        lookupCallCount++;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ hits: sampleHits }),
        });
      }
      return Promise.reject(new Error(`unexpected ${url}`));
    });
    vi.stubGlobal('fetch', fetchMock);

    let composable: ReturnType<typeof usePonsLookup> | undefined;
    const Cmp = defineComponent({
      setup() {
        composable = usePonsLookup();
        return composable;
      },
      template: '<div />',
    });
    mount(Cmp);

    await nextTick();
    await Promise.resolve();
    await nextTick();

    const r1 = await composable!.lookup('Haus');
    expect(r1.ok).toBe(true);
    if (r1.ok) {
      expect(r1.hits).toEqual(sampleHits);
    }

    const state = composable!.getState('Haus');
    expect(state?.loading).toBe(false);
    expect(state?.hits).toEqual(sampleHits);
    expect(state?.error).toBeNull();

    const r2 = await composable!.lookup('Haus');
    expect(r2.ok).toBe(true);
    expect(lookupCallCount).toBe(1);
  });

  it('lookup handles error response', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = requestUrl(input);
      if (url.includes('/api/health')) {
        return Promise.resolve(healthResponse(true));
      }
      if (url.includes('/api/external/pons/dictionary')) {
        return Promise.resolve({
          ok: false,
          status: 503,
          json: () => Promise.resolve({ error: 'Tageslimit erreicht' }),
        });
      }
      return Promise.reject(new Error(`unexpected ${url}`));
    });
    vi.stubGlobal('fetch', fetchMock);

    let composable: ReturnType<typeof usePonsLookup> | undefined;
    const Cmp = defineComponent({
      setup() {
        composable = usePonsLookup();
        return composable;
      },
      template: '<div />',
    });
    mount(Cmp);

    await nextTick();
    await Promise.resolve();
    await nextTick();

    const r = await composable!.lookup('Haus');
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.message).toContain('Tageslimit');
    }

    const state = composable!.getState('Haus');
    expect(state?.loading).toBe(false);
    expect(state?.hits).toBeNull();
    expect(state?.error).toContain('Tageslimit');
  });
});
