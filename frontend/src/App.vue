<script setup lang="ts">
import Button from 'primevue/button';
import ConfirmDialog from 'primevue/confirmdialog';
import Dialog from 'primevue/dialog';
import ProgressSpinner from 'primevue/progressspinner';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useApiHealthPoll } from '@/composables/useApiHealthPoll';
import { useSseOllamaStream } from '@/composables/useSseOllamaStream';

const route = useRoute();
const toast = useToast();
const { health, statusLine } = useApiHealthPoll();
const {
  ollamaState,
  ollamaBusy,
  streamPreview,
  shutdownDialogOpen,
  shutdownWarningSeconds,
  cancelIdleShutdown,
  goToSleep,
} = useSseOllamaStream();

const showBusy = computed(() => health.value.kind === 'loading' || ollamaBusy.value);
const showStreamBox = computed(() => streamPreview.value.length > 0);
const sleepEnabled = computed(() => ollamaState.value?.idle_enabled === true);

async function onCancelShutdown() {
  const r = await cancelIdleShutdown();
  if (!r.ok) {
    toast.add({
      severity: 'error',
      summary: 'Abbruch fehlgeschlagen',
      detail: r.message ?? 'Unbekannter Fehler',
      life: 6000,
    });
  }
}

async function onGoToSleep() {
  const r = await goToSleep();
  if (!r.ok) {
    toast.add({
      severity: 'error',
      summary: 'Ruhezustand',
      detail: r.message ?? 'Ollama konnte nicht gestoppt werden.',
      life: 6000,
    });
  }
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
          <Button
            v-if="ollamaState !== null"
            label="Ruhezustand"
            severity="secondary"
            size="small"
            outlined
            :disabled="!sleepEnabled"
            :title="
              sleepEnabled ? 'Ollama jetzt stoppen' : 'Nur verfügbar wenn Sidecar konfiguriert ist.'
            "
            @click="onGoToSleep"
          />
        </div>
      </div>
    </header>
    <section
      v-if="showBusy || showStreamBox"
      class="border-b border-slate-200 bg-slate-100/90"
      aria-live="polite"
    >
      <div class="mx-auto max-w-5xl px-3 py-3 sm:px-4">
        <div v-if="showBusy" class="mb-2 flex items-center gap-3 text-sm text-slate-600">
          <ProgressSpinner
            stroke-width="4"
            class="size-8 shrink-0 text-slate-500 [&_circle]:stroke-current"
          />
          <span>Laden oder Ollama ist aktiv …</span>
        </div>
        <div
          v-if="showStreamBox"
          class="max-h-40 overflow-y-auto rounded-md border border-slate-200 bg-slate-200/60 p-3 text-left text-xs leading-relaxed text-slate-500"
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
