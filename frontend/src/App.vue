<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { getApiBaseUrl } from '@/config/apiBase';

const route = useRoute();

/** Mirrors ``GET /api/health`` JSON (subset). */
interface HealthPayload {
  ok: boolean;
  sidecar?: { status: string; detail?: string };
}

type HealthState =
  | { kind: 'loading' }
  | { kind: 'ok'; payload: HealthPayload }
  | { kind: 'error'; message: string };

const health = ref<HealthState>({ kind: 'loading' });
let pollTimer: ReturnType<typeof setInterval> | undefined;

const POLL_MS = 30_000;

async function loadHealth(): Promise<void> {
  const base = getApiBaseUrl();
  const url = `${base}/api/health`;
  try {
    const res = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!res.ok) {
      health.value = { kind: 'error', message: `HTTP ${res.status}` };
      return;
    }
    const payload = (await res.json()) as HealthPayload;
    health.value = { kind: 'ok', payload };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Unbekannter Fehler';
    health.value = { kind: 'error', message };
  }
}

const statusLine = computed(() => {
  const h = health.value;
  if (h.kind === 'loading') {
    return 'Status: wird geladen …';
  }
  if (h.kind === 'error') {
    return `Status: ${h.message}`;
  }
  const apiOk = h.payload.ok;
  const parts: string[] = [];
  parts.push(apiOk ? 'API: OK' : 'API: Fehler');
  const sc = h.payload.sidecar;
  if (sc) {
    const label = sc.status === 'ok' ? 'OK' : 'Fehler';
    parts.push(`Sidecar: ${label}`);
    if (sc.detail) {
      parts.push(`(${sc.detail})`);
    }
  } else {
    parts.push('Sidecar: nicht konfiguriert');
  }
  return parts.join(' · ');
});

onMounted(() => {
  void loadHealth();
  pollTimer = setInterval(() => void loadHealth(), POLL_MS);
});

onUnmounted(() => {
  if (pollTimer !== undefined) {
    clearInterval(pollTimer);
  }
});
</script>

<template>
  <div class="flex min-h-screen flex-col bg-slate-50">
    <header class="border-b border-slate-200 bg-white shadow-sm">
      <div
        class="mx-auto flex max-w-5xl flex-col gap-3 px-3 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:px-4"
      >
        <div>
          <h1 class="text-base font-bold tracking-tight text-slate-900 sm:text-lg">
            SRF News Lernen
          </h1>
          <p class="text-xs text-slate-500 sm:text-sm">Mobile-first App-Shell</p>
        </div>
        <nav class="flex flex-wrap gap-2 text-sm sm:justify-end" aria-label="Hauptnavigation">
          <RouterLink
            to="/"
            class="rounded-md px-3 py-2 font-medium text-slate-700 hover:bg-slate-100"
            active-class="bg-slate-200 text-slate-900"
          >
            Start
          </RouterLink>
          <RouterLink
            to="/stub"
            class="rounded-md px-3 py-2 font-medium text-slate-700 hover:bg-slate-100"
            active-class="bg-slate-200 text-slate-900"
          >
            Platzhalter
          </RouterLink>
        </nav>
      </div>
    </header>
    <main class="flex-1">
      <RouterView :key="route.fullPath" />
    </main>
    <footer class="border-t border-slate-200 bg-white py-3 text-slate-600">
      <div
        class="mx-auto flex max-w-5xl flex-col gap-1 px-3 text-center text-xs sm:px-4 sm:text-sm"
      >
        <p class="font-medium text-slate-800">Phase 6 Shell</p>
        <p
          class="break-words text-slate-500"
          role="status"
          :aria-busy="health.kind === 'loading'"
          :data-state="health.kind"
        >
          {{ statusLine }}
        </p>
      </div>
    </footer>
  </div>
</template>
