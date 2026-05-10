import Aura from '@primeuix/themes/aura';
import { flushPromises, mount } from '@vue/test-utils';
import ConfirmationService from 'primevue/confirmationservice';
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice';
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
      'EventSource',
      class {
        close = vi.fn();
        addEventListener = vi.fn();
        constructor(_url: string) {}
      }
    );
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url =
          typeof input === 'string'
            ? input
            : input instanceof URL
              ? input.href
              : (input as Request).url;
        if (url.includes('/api/articles')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ items: [], next_cursor: null }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ ok: true, sidecar: { status: 'ok' } }),
        });
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
        plugins: [
          router,
          ToastService,
          ConfirmationService,
          [PrimeVue, { theme: { preset: Aura, options: { darkModeSelector: false } } }],
        ],
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('SRF News Lernen');
    expect(wrapper.text()).toContain('News und Lernmodus');
    expect(wrapper.find('main').exists()).toBe(true);
    expect(wrapper.text()).toContain('News');
    expect(wrapper.text()).toContain('Wörterbuch');
    expect(wrapper.text()).toContain('Einstellungen');
    expect(wrapper.text()).toContain('Timeline aus der lokalen Datenbank');
    expect(wrapper.text()).toContain('API: OK');
    expect(wrapper.text()).toContain('Sidecar: OK');
  });
});
