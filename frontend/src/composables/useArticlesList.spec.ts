import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, ref } from 'vue';
import { useArticlesList } from './useArticlesList';

const Harness = defineComponent({
  name: 'ArticlesListHarness',
  setup() {
    const selectedDate = ref('2026-05-10');
    const debouncedSearch = ref('');
    const state = useArticlesList({ selectedDate, debouncedSearch });
    return { selectedDate, debouncedSearch, ...state };
  },
  template: '<div />',
});

describe('useArticlesList', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('clears listLoading after empty list response', async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ items: [], next_cursor: null }),
    } as Response);

    const wrapper = mount(Harness);
    await flushPromises();

    try {
      expect(wrapper.vm.listLoading).toBe(false);
      expect(wrapper.vm.items).toEqual([]);
      expect(fetchMock).toHaveBeenCalled();
    } finally {
      wrapper.unmount();
    }
  });

  it('aborts superseded fetch so the latest request still clears loading', async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    let n = 0;
    fetchMock.mockImplementation((_input: RequestInfo | URL, init?: RequestInit) => {
      n += 1;
      if (n === 1) {
        return new Promise((_resolve, reject) => {
          const signal = init?.signal;
          if (!signal) {
            reject(new Error('expected AbortSignal'));
            return;
          }
          if (signal.aborted) {
            reject(new DOMException('Aborted', 'AbortError'));
            return;
          }
          signal.addEventListener('abort', () => {
            reject(new DOMException('Aborted', 'AbortError'));
          });
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ items: [], next_cursor: null }),
      } as Response);
    });

    const wrapper = mount(Harness);
    await flushPromises();

    try {
      expect(wrapper.vm.listLoading).toBe(true);
      wrapper.vm.selectedDate = '2026-05-11';
      await flushPromises();
      expect(wrapper.vm.listLoading).toBe(false);
      expect(wrapper.vm.items).toEqual([]);
      expect(n).toBeGreaterThanOrEqual(2);
    } finally {
      wrapper.unmount();
    }
  });

  it('normalizes missing items array to empty list', async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ next_cursor: null }),
    } as Response);

    const wrapper = mount(Harness);
    await flushPromises();

    try {
      expect(wrapper.vm.listLoading).toBe(false);
      expect(wrapper.vm.items).toEqual([]);
    } finally {
      wrapper.unmount();
    }
  });
});
