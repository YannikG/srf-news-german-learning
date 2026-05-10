import { mount } from '@vue/test-utils';
import { defineComponent, nextTick } from 'vue';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Word } from '@/types/word';
import { useWordsDictionary } from './useWordsDictionary';

function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === 'string') return input;
  if (input instanceof URL) return input.href;
  return (input as Request).url;
}

function isWordsListUrl(url: string): boolean {
  return url.includes('/api/words') && !/\/api\/words\/\d+(\?|$)/.test(url);
}

describe('useWordsDictionary', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('CRUD-Flow: GET leer, POST, GET Liste, PATCH, GET aktualisiert, DELETE, GET leer', async () => {
    const w1: Word = {
      id: 1,
      german_label: 'Haus',
      category: 'Nomen',
      difficulty: 'Neu',
      translation: 'house',
      cefr_level: null,
      created_at: '2026-01-01T00:00:00',
      updated_at: '2026-01-01T00:00:00',
    };
    const w1patched: Word = {
      ...w1,
      translation: 'home',
      difficulty: 'Leicht',
    };

    const rows: Word[] = [];

    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = requestUrl(input);
      const method = init?.method ?? 'GET';

      if (isWordsListUrl(url)) {
        if (method === 'GET') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve([...rows]),
          });
        }
        if (method === 'POST') {
          rows.splice(0, rows.length, w1);
          return Promise.resolve({
            ok: true,
            status: 201,
            json: () => Promise.resolve(w1),
          });
        }
      }

      if (url.includes('/api/words/1') && !url.includes('/api/words/1?')) {
        if (method === 'PATCH') {
          rows.splice(0, rows.length, w1patched);
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(w1patched),
          });
        }
        if (method === 'DELETE') {
          rows.splice(0, rows.length);
          return Promise.resolve({ ok: true, status: 204 });
        }
      }

      return Promise.reject(new Error(`unexpected fetch ${method} ${url}`));
    });

    vi.stubGlobal('fetch', fetchMock);

    let dict: ReturnType<typeof useWordsDictionary> | undefined;
    const TestCmp = defineComponent({
      setup() {
        dict = useWordsDictionary();
        return dict;
      },
      template: '<div />',
    });
    mount(TestCmp);

    await nextTick();
    await Promise.resolve();
    await nextTick();

    expect(dict).toBeDefined();
    const d = dict!;
    expect(d.items.value).toEqual([]);

    const createRes = await d.create({
      german_label: 'Haus',
      category: 'Nomen',
      difficulty: 'Neu',
      translation: 'house',
      cefr_level: null,
    });
    expect(createRes.ok).toBe(true);
    expect(d.items.value.map((x) => x.german_label)).toEqual(['Haus']);

    const patchRes = await d.update(1, { translation: 'home', difficulty: 'Leicht' });
    expect(patchRes.ok).toBe(true);
    expect(d.items.value[0]?.translation).toBe('home');
    expect(d.items.value[0]?.difficulty).toBe('Leicht');

    const delRes = await d.remove(1);
    expect(delRes.ok).toBe(true);
    expect(d.items.value).toEqual([]);

    expect(fetchMock.mock.calls.some((c) => c[1]?.method === 'POST')).toBe(true);
    expect(fetchMock.mock.calls.some((c) => c[1]?.method === 'PATCH')).toBe(true);
    expect(fetchMock.mock.calls.some((c) => c[1]?.method === 'DELETE')).toBe(true);
  });
});
