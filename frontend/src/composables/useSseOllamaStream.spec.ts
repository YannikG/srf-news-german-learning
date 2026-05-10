import Aura from '@primeuix/themes/aura';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice';
import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent } from 'vue';
import { useSseOllamaStream } from './useSseOllamaStream';

class MockEventSource {
  static instances: MockEventSource[] = [];

  url: string;
  private readonly listeners = new Map<string, Set<(ev: MessageEvent) => void>>();
  readyState = 1;

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  addEventListener(type: string, fn: EventListener): void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)!.add(fn as (ev: MessageEvent) => void);
  }

  removeEventListener(type: string, fn: EventListener): void {
    this.listeners.get(type)?.delete(fn as (ev: MessageEvent) => void);
  }

  close(): void {
    this.readyState = 2;
  }

  emit(type: string, payload: unknown): void {
    const data = JSON.stringify(payload);
    const ev = new MessageEvent(type, { data });
    const set = this.listeners.get(type);
    if (set) {
      for (const fn of set) {
        fn(ev);
      }
    }
  }
}

const TestHarness = defineComponent({
  name: 'SseTestHarness',
  components: { Button, Dialog },
  setup() {
    return useSseOllamaStream();
  },
  template: `
    <Dialog v-model:visible="shutdownDialogOpen" modal>
      <Button data-testid="cancel" label="Abbruch" @click="cancelIdleShutdown" />
    </Dialog>
    <span data-testid="preview">{{ streamPreview }}</span>
  `,
});

describe('useSseOllamaStream', () => {
  let lastWrapper: ReturnType<typeof mount> | undefined;

  beforeEach(() => {
    MockEventSource.instances = [];
    vi.stubGlobal('EventSource', MockEventSource);
  });

  afterEach(() => {
    lastWrapper?.unmount();
    lastWrapper = undefined;
    vi.unstubAllGlobals();
  });

  it('calls cancel POST after shutdown_warning and Abbruch', async () => {
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url =
        typeof input === 'string'
          ? input
          : input instanceof URL
            ? input.href
            : (input as Request).url;
      if (url.includes('/api/ollama/cancel-idle-shutdown')) {
        expect(init?.method).toBe('POST');
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ ok: true }),
        });
      }
      return Promise.reject(new Error(`unexpected fetch: ${url}`));
    });
    vi.stubGlobal('fetch', fetchMock);

    lastWrapper = mount(TestHarness, {
      global: {
        plugins: [
          [PrimeVue, { theme: { preset: Aura, options: { darkModeSelector: false } } }],
          ToastService,
        ],
      },
    });

    await flushPromises();
    const es = MockEventSource.instances[0];
    expect(es.url).toContain('/api/events/stream');

    es.emit('shutdown_warning', { warning_seconds: 12 });
    await flushPromises();

    const btn = document.querySelector('[data-testid="cancel"]') as HTMLButtonElement | null;
    expect(btn).toBeTruthy();
    btn!.click();
    await flushPromises();

    expect(fetchMock).toHaveBeenCalled();
    const cancelCalls = fetchMock.mock.calls.filter(([u]) =>
      String(u).includes('/api/ollama/cancel-idle-shutdown')
    );
    expect(cancelCalls.length).toBeGreaterThanOrEqual(1);
  });

  it('appends llm_chunk delta and clears on llm_done', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true }),
      })
    );

    const Plain = defineComponent({
      template: '<span data-testid="preview">{{ streamPreview }}</span>',
      setup() {
        return useSseOllamaStream();
      },
    });

    lastWrapper = mount(Plain, {
      global: {
        plugins: [
          [PrimeVue, { theme: { preset: Aura, options: { darkModeSelector: false } } }],
          ToastService,
        ],
      },
    });

    await flushPromises();
    const wrapper = lastWrapper;
    const es = MockEventSource.instances[0];

    es.emit('llm_chunk', { article_id: 'a1', delta: 'Hallo' });
    await flushPromises();
    expect(wrapper.get('[data-testid="preview"]').text()).toBe('Hallo');

    es.emit('llm_chunk', { article_id: 'a1', delta: ' Welt' });
    await flushPromises();
    expect(wrapper.get('[data-testid="preview"]').text()).toBe('Hallo Welt');

    es.emit('llm_done', { article_id: 'a1', cefr_level: 'B1', simplification_id: 1 });
    await flushPromises();
    expect(wrapper.get('[data-testid="preview"]').text()).toBe('');
  });
});
