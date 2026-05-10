import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { createMemoryHistory, createRouter } from 'vue-router';
import App from './App.vue';
import { routes } from './router';

describe('App shell', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('mounts layout with navigation and outlet', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, sidecar: { status: 'ok' } }),
      })
    );

    const router = createRouter({
      history: createMemoryHistory(),
      routes,
    });
    await router.push('/');
    await router.isReady();

    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('SRF News Lernen');
    expect(wrapper.text()).toContain('Mobile-first App-Shell');
    expect(wrapper.find('main').exists()).toBe(true);
    expect(wrapper.text()).toContain('App-Shell bereit');
    expect(wrapper.text()).toContain('API: OK');
    expect(wrapper.text()).toContain('Sidecar: OK');
  });
});
