import { defineComponent, type Ref } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import type { HealthState } from '@/api/healthTypes';
import { useApiHealthPoll } from './useApiHealthPoll';

function mountPollHost(pollMs: number, capture?: { health: Ref<HealthState> | null }) {
  const Comp = defineComponent({
    setup() {
      const poll = useApiHealthPoll(pollMs);
      if (capture) {
        capture.health = poll.health;
      }
      return { statusLine: poll.statusLine };
    },
    template: '<span data-testid="line">{{ statusLine }}</span>',
  });
  return mount(Comp);
}

describe('useApiHealthPoll', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('loads health on mount and updates status line', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, sidecar: { status: 'ok' } }),
      })
    );

    const wrapper = mountPollHost(60_000);
    await flushPromises();

    expect(wrapper.get('[data-testid="line"]').text()).toContain('API: OK');
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1);
    wrapper.unmount();
  });

  it('does not apply fetch result after unmount when response arrives late', async () => {
    let resolveFetch!: (value: unknown) => void;
    const fetchPromise = new Promise((resolve) => {
      resolveFetch = resolve;
    });

    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(() =>
        fetchPromise.then(() => ({
          ok: true,
          json: () => Promise.resolve({ ok: true, sidecar: { status: 'ok' } }),
        }))
      )
    );

    const capture: { health: Ref<HealthState> | null } = { health: null };
    const wrapper = mountPollHost(60_000, capture);
    await flushPromises();

    expect(capture.health?.value.kind).toBe('loading');

    wrapper.unmount();
    resolveFetch(undefined);
    await flushPromises();

    expect(capture.health?.value.kind).toBe('loading');
  });

  it('clears poll interval on unmount so fetch is not called again', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, sidecar: { status: 'ok' } }),
      })
    );

    const pollMs = 5_000;
    const wrapper = mountPollHost(pollMs);
    await flushPromises();
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(pollMs);
    await flushPromises();
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(2);

    wrapper.unmount();

    vi.advanceTimersByTime(pollMs * 10);
    await flushPromises();
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(2);
  });

  it('sets error state when fetch reports non-OK HTTP', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: () => Promise.resolve({}),
      })
    );

    const wrapper = mountPollHost(60_000);
    await flushPromises();

    expect(wrapper.get('[data-testid="line"]').text()).toContain('HTTP 503');
    wrapper.unmount();
  });
});
