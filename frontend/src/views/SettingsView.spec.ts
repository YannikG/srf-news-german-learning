import Aura from '@primeuix/themes/aura';
import { flushPromises, mount } from '@vue/test-utils';
import ConfirmationService from 'primevue/confirmationservice';
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createMemoryHistory, createRouter } from 'vue-router';
import { routes } from '@/router';
import SettingsView from './SettingsView.vue';

const { toastAdd } = vi.hoisted(() => ({ toastAdd: vi.fn() }));

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({
    add: toastAdd,
    remove: vi.fn(),
    removeGroup: vi.fn(),
    removeAll: vi.fn(),
  }),
}));

const baseRow = {
  default_cefr: 'B1',
  translation_language: 'en',
  retrieval_top_k: null,
  retrieval_context_max_chars: null,
};

describe('SettingsView', () => {
  beforeEach(() => {
    toastAdd.mockClear();
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  async function mountView() {
    const router = createRouter({
      history: createMemoryHistory(),
      routes,
    });
    await router.push('/einstellungen');
    await router.isReady();
    return mount(SettingsView, {
      global: {
        plugins: [
          router,
          ToastService,
          ConfirmationService,
          [PrimeVue, { theme: { preset: Aura, options: { darkModeSelector: false } } }],
        ],
      },
    });
  }

  it('shows success toast after PATCH and verification GET succeed', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ ...baseRow }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ ...baseRow }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ ...baseRow }),
      });
    vi.stubGlobal('fetch', fetchMock);

    const wrapper = await mountView();
    await flushPromises();

    await wrapper.get('[data-testid="settings-save"]').trigger('click');
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledTimes(3);
    const patchCall = fetchMock.mock.calls.find(
      (c) => (c[1] as RequestInit | undefined)?.method === 'PATCH'
    );
    expect(patchCall).toBeDefined();
    expect(toastAdd).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'success', summary: 'Einstellungen' })
    );
  });

  it('shows error toast when PATCH returns 400', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ ...baseRow }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ error: 'translation_language must be one of: en, uk' }),
      });
    vi.stubGlobal('fetch', fetchMock);

    const wrapper = await mountView();
    await flushPromises();
    await wrapper.get('[data-testid="settings-save"]').trigger('click');
    await flushPromises();

    expect(toastAdd).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'error', summary: 'Speichern' })
    );
  });
});
