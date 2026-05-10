import { mount } from '@vue/test-utils';
import { defineComponent } from 'vue';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { PostNewsRefreshResult } from '@/api/postNewsRefresh';
import { useNewsRefresh } from './useNewsRefresh';

describe('useNewsRefresh', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('zwei schnelle Refresh-Calls: erster fetched true, zweiter fetched false wie Backend-Cooldown', async () => {
    const next = '2099-01-01T00:00:00Z';
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            fetched: true,
            articles_upserted: 2,
            next_allowed_fetch_at: next,
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            fetched: false,
            articles_upserted: 0,
            next_allowed_fetch_at: next,
          }),
      });
    vi.stubGlobal('fetch', fetchMock);

    const TestCmp = defineComponent({
      setup() {
        const { refresh } = useNewsRefresh();
        return { refresh };
      },
      template: '<div />',
    });
    const wrapper = mount(TestCmp);
    const vm = wrapper.vm as { refresh: () => Promise<PostNewsRefreshResult> };
    const r1 = await vm.refresh();
    const r2 = await vm.refresh();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(r1.ok && r1.data.fetched).toBe(true);
    expect(r2.ok && r2.data.fetched).toBe(false);
    expect(r2.ok && r2.data.next_allowed_fetch_at).toBe(next);
  });
});
