import { computed, onMounted, onUnmounted, ref, shallowRef } from 'vue';
import { buildApiUrl } from '@/api/buildApiUrl';

export type OllamaPublicState = {
  idle_enabled: boolean;
  refcount: number;
  idle_shutdown_armed: boolean;
  idle_warning_issued: boolean;
};

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

function parseOllamaState(raw: unknown): OllamaPublicState | null {
  if (!isRecord(raw)) {
    return null;
  }
  const { idle_enabled, refcount, idle_shutdown_armed, idle_warning_issued } = raw;
  if (
    typeof idle_enabled !== 'boolean' ||
    typeof refcount !== 'number' ||
    typeof idle_shutdown_armed !== 'boolean' ||
    typeof idle_warning_issued !== 'boolean'
  ) {
    return null;
  }
  return { idle_enabled, refcount, idle_shutdown_armed, idle_warning_issued };
}

function parseWarningSeconds(raw: unknown): number | null {
  if (!isRecord(raw)) {
    return null;
  }
  const w = raw.warning_seconds;
  return typeof w === 'number' && Number.isFinite(w) ? w : null;
}

function parseLlmChunk(raw: unknown): { article_id: string; delta: string } | null {
  if (!isRecord(raw)) {
    return null;
  }
  const aid = raw.article_id;
  const delta = raw.delta;
  if (typeof aid !== 'string' || typeof delta !== 'string') {
    return null;
  }
  return { article_id: aid, delta };
}

/**
 * Holds one browser EventSource to GET /api/events/stream; exposes Ollama idle and LLM chunk UX state.
 */
export function useSseOllamaStream() {
  const ollamaState = shallowRef<OllamaPublicState | null>(null);
  const streamPreview = ref('');
  const shutdownDialogOpen = ref(false);
  const shutdownWarningSeconds = ref(0);
  let source: EventSource | null = null;

  const ollamaBusy = computed(() => (ollamaState.value?.refcount ?? 0) > 0);

  function appendChunk(chunk: { delta: string }) {
    streamPreview.value += chunk.delta;
  }

  function clearStreamPreview() {
    streamPreview.value = '';
  }

  function attachListeners(es: EventSource) {
    es.addEventListener('ollama_state', (ev) => {
      const parsed = parseOllamaState(safeParseData(ev as MessageEvent));
      if (parsed !== null) {
        ollamaState.value = parsed;
      }
    });

    es.addEventListener('shutdown_warning', (ev) => {
      const sec = parseWarningSeconds(safeParseData(ev as MessageEvent));
      shutdownWarningSeconds.value = sec ?? 0;
      shutdownDialogOpen.value = true;
    });

    es.addEventListener('shutdown_cancelled', () => {
      shutdownDialogOpen.value = false;
    });

    es.addEventListener('llm_chunk', (ev) => {
      const chunk = parseLlmChunk(safeParseData(ev as MessageEvent));
      if (chunk !== null) {
        appendChunk(chunk);
      }
    });

    es.addEventListener('llm_done', () => {
      clearStreamPreview();
    });
  }

  function connect() {
    const ES = globalThis.EventSource;
    if (typeof ES !== 'function') {
      return;
    }
    const url = buildApiUrl('/api/events/stream');
    source = new ES(url) as EventSource;
    attachListeners(source);
  }

  function disconnect() {
    source?.close();
    source = null;
  }

  onMounted(() => {
    connect();
  });

  onUnmounted(() => {
    disconnect();
  });

  async function cancelIdleShutdown(): Promise<{ ok: boolean; message?: string }> {
    const res = await fetch(buildApiUrl('/api/ollama/cancel-idle-shutdown'), {
      method: 'POST',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      const message = await readErrorDetail(res);
      return { ok: false, message };
    }
    shutdownDialogOpen.value = false;
    return { ok: true };
  }

  async function goToSleep(): Promise<{ ok: boolean; message?: string }> {
    const res = await fetch(buildApiUrl('/api/ollama/go-to-sleep'), {
      method: 'POST',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      const message = await readErrorDetail(res);
      return { ok: false, message };
    }
    const body: unknown = await res.json().catch(() => null);
    if (isRecord(body) && body.ok === false) {
      const detail = body.detail;
      return {
        ok: false,
        message: typeof detail === 'string' ? detail : 'Ollama konnte nicht gestoppt werden.',
      };
    }
    return { ok: true };
  }

  return {
    ollamaState,
    ollamaBusy,
    streamPreview,
    shutdownDialogOpen,
    shutdownWarningSeconds,
    cancelIdleShutdown,
    goToSleep,
  };
}

function safeParseData(ev: MessageEvent): unknown {
  try {
    return JSON.parse(ev.data as string);
  } catch {
    return null;
  }
}

async function readErrorDetail(res: Response): Promise<string> {
  try {
    const j: unknown = await res.json();
    if (isRecord(j) && typeof j.detail === 'string') {
      return j.detail;
    }
  } catch {
    /* ignore */
  }
  return `HTTP ${res.status}`;
}
