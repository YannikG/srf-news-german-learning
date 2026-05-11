import { afterEach, describe, expect, it, vi } from 'vitest';
import type { TranslationLanguage } from '@/types/settings';
import { fetchSettings, parseAppSettings, patchSettings } from './settingsApi';

const sampleRow = {
  default_cefr: 'B1' as const,
  translation_language: 'en' as const,
  retrieval_top_k: null,
  retrieval_context_max_chars: null,
  active_ingest_provider: 'srgssr',
};

describe('parseAppSettings', () => {
  it('returns null when core fields are invalid', () => {
    expect(parseAppSettings(null)).toBeNull();
    expect(parseAppSettings({})).toBeNull();
    expect(
      parseAppSettings({
        default_cefr: 'X1',
        translation_language: 'en',
        retrieval_top_k: null,
        retrieval_context_max_chars: null,
        active_ingest_provider: 'srgssr',
      })
    ).toBeNull();
  });

  it('returns row when shape matches backend contract', () => {
    expect(
      parseAppSettings({
        default_cefr: 'B1',
        translation_language: 'en',
        retrieval_top_k: 3,
        retrieval_context_max_chars: null,
        active_ingest_provider: 'srgssr',
      })
    ).toEqual({
      default_cefr: 'B1',
      translation_language: 'en',
      retrieval_top_k: 3,
      retrieval_context_max_chars: null,
      active_ingest_provider: 'srgssr',
    });
  });

  it('treats absent retrieval fields as null', () => {
    expect(
      parseAppSettings({
        default_cefr: 'A2',
        translation_language: 'uk',
        active_ingest_provider: 'srgssr',
      })
    ).toEqual({
      default_cefr: 'A2',
      translation_language: 'uk',
      retrieval_top_k: null,
      retrieval_context_max_chars: null,
      active_ingest_provider: 'srgssr',
    });
  });
});

describe('settingsApi', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('fetchSettings returns data on 200', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(sampleRow),
      })
    );
    const r = await fetchSettings();
    expect(r.ok && r.data).toEqual(sampleRow);
  });

  it('fetchSettings returns message on error JSON', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ error: 'translation_language must be a string' }),
      })
    );
    const r = await fetchSettings();
    expect(r).toEqual({
      ok: false,
      status: 400,
      message: 'translation_language must be a string',
    });
  });

  it('fetchSettings rejects 200 JSON that fails parse', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            default_cefr: 'B1',
            translation_language: 'de',
            retrieval_top_k: null,
            retrieval_context_max_chars: null,
            active_ingest_provider: 'srgssr',
          }),
      })
    );
    const r = await fetchSettings();
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.message).toContain('Unerwartetes');
    }
  });

  it('patchSettings sends JSON body and returns data on 200', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          ...sampleRow,
          default_cefr: 'A2' as const,
          active_ingest_provider: 'srgssr',
        }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const r = await patchSettings({ default_cefr: 'A2' });
    expect(r.ok && r.data.default_cefr).toBe('A2');
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0] as [RequestInfo, RequestInit];
    expect(init.method).toBe('PATCH');
    expect(init.headers).toMatchObject({
      Accept: 'application/json',
      'Content-Type': 'application/json',
    });
    expect(JSON.parse(init.body as string)).toEqual({ default_cefr: 'A2' });
  });

  it('patchSettings maps backend error field on non-OK', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ error: 'translation_language must be one of: en, uk' }),
      })
    );
    const r = await patchSettings({
      translation_language: 'de' as TranslationLanguage,
    });
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.message).toContain('translation_language');
    }
  });
});
