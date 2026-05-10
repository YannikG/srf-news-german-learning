<script setup lang="ts">
import Button from 'primevue/button';
import ConfirmDialog from 'primevue/confirmdialog';
import Dialog from 'primevue/dialog';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { formatOllamaContainerStateLabel } from '@/api/formatHealthFooterLine';
import { useApiHealthPoll } from '@/composables/useApiHealthPoll';
import { useSseOllamaStream } from '@/composables/useSseOllamaStream';

const route = useRoute();
const toast = useToast();
const { health, statusLine, refresh: refreshHealth } = useApiHealthPoll();
const {
  ollamaState,
  streamPreview,
  shutdownDialogOpen,
  shutdownWarningSeconds,
  cancelIdleShutdown,
  startOllama,
} = useSseOllamaStream();

const showStreamBox = computed(() => streamPreview.value.length > 0);
const sleepEnabled = computed(() => ollamaState.value?.idle_enabled === true);

/** Docker container state from the last ``GET /api/health`` sidecar inspect (poll ~30s). */
const ollamaRuntimeLine = computed(() => {
  const h = health.value;
  if (h.kind !== 'ok') {
    return null;
  }
  const sc = h.payload.sidecar;
  if (!sc || sc.status !== 'ok') {
    return null;
  }
  const st = sc.ollama?.state;
  if (!st) {
    return null;
  }
  return `Ollama-Container: ${formatOllamaContainerStateLabel(st)}`;
});

async function onCancelShutdown() {
  const r = await cancelIdleShutdown();
  if (!r.ok) {
    toast.add({
      severity: 'error',
      summary: 'Abbruch fehlgeschlagen',
      detail: r.message ?? 'Unbekannter Fehler',
      life: 6000,
    });
    return;
  }
  toast.add({
    severity: 'success',
    summary: 'Automatischer Stopp abgebrochen',
    detail: 'Ollama bleibt vorerst aktiv.',
    life: 4000,
  });
}

async function onStartOllama() {
  const r = await startOllama();
  if (!r.ok) {
    toast.add({
      severity: 'error',
      summary: 'Ollama starten',
      detail: r.message ?? 'Ollama konnte nicht gestartet werden.',
      life: 6000,
    });
    return;
  }
  toast.add({
    severity: 'success',
    summary: 'Ollama starten',
    detail:
      'Der Start wurde ausgelöst. Je nach Modell kann es etwas dauern, bis Ollama wieder bereit ist.',
    life: 5000,
  });
  void refreshHealth();
}
</script>

<template>
  <Toast position="top-center" />
  <ConfirmDialog />
  <Dialog
    v-model:visible="shutdownDialogOpen"
    modal
    header="Ollama wird gestoppt"
    :closable="false"
    :draggable="false"
  >
    <p class="text-sm text-slate-700">
      Ollama wird in etwa {{ shutdownWarningSeconds }} Sekunden automatisch gestoppt. Mit «Abbruch»
      bleibt der Dienst vorerst aktiv.
    </p>
    <template #footer>
      <Button label="Abbruch" severity="secondary" @click="onCancelShutdown" />
    </template>
  </Dialog>
  <div class="flex min-h-screen flex-col bg-slate-50">
    <header class="border-b border-slate-200 bg-white shadow-sm">
      <div
        class="mx-auto flex max-w-5xl flex-col gap-3 px-3 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:px-4"
      >
        <div>
          <h1 class="text-base font-bold tracking-tight text-slate-900 sm:text-lg">
            SRF News Lernen
          </h1>
          <p class="text-xs text-slate-500 sm:text-sm">News und Lernmodus</p>
        </div>
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
          <nav class="flex flex-wrap gap-2 text-sm sm:justify-end" aria-label="Hauptnavigation">
            <RouterLink
              to="/"
              class="rounded-md px-3 py-2 font-medium text-slate-700 hover:bg-slate-100"
              active-class="bg-slate-200 text-slate-900"
            >
              News
            </RouterLink>
            <RouterLink
              to="/woerterbuch"
              class="rounded-md px-3 py-2 font-medium text-slate-700 hover:bg-slate-100"
              active-class="bg-slate-200 text-slate-900"
            >
              Wörterbuch
            </RouterLink>
            <RouterLink
              to="/einstellungen"
              class="rounded-md px-3 py-2 font-medium text-slate-700 hover:bg-slate-100"
              active-class="bg-slate-200 text-slate-900"
            >
              Einstellungen
            </RouterLink>
          </nav>
          <div
            v-if="ollamaState !== null && sleepEnabled"
            class="flex flex-col items-stretch gap-1 sm:items-end"
          >
            <p
              v-if="ollamaRuntimeLine"
              class="text-right text-xs text-slate-500"
              role="status"
              data-testid="ollama-runtime-status"
            >
              {{ ollamaRuntimeLine }}
            </p>
            <Button
              label="Ollama starten"
              severity="secondary"
              size="small"
              outlined
              class="self-stretch sm:self-end"
              title="Ollama-Container über das Sidecar starten"
              aria-label="Ollama starten"
              @click="onStartOllama"
            />
          </div>
        </div>
      </div>
    </header>
    <section v-if="showStreamBox" class="border-b border-slate-200 bg-white" aria-live="polite">
      <div class="mx-auto max-w-5xl px-3 py-2 sm:px-4">
        <div
          class="max-h-40 overflow-y-auto rounded-md border border-slate-200 bg-slate-50 p-3 text-left text-xs leading-relaxed text-slate-600"
        >
          <pre class="whitespace-pre-wrap font-sans">{{ streamPreview }}</pre>
        </div>
      </div>
    </section>
    <main class="flex-1">
      <RouterView :key="route.fullPath" />
    </main>
    <footer class="border-t border-slate-200 bg-white py-3 text-slate-600">
      <div
        class="mx-auto flex max-w-5xl flex-col gap-1 px-3 text-center text-xs sm:px-4 sm:text-sm"
      >
        <p class="font-medium text-slate-800">SRF News Lernen</p>
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
