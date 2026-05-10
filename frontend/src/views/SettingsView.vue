<script setup lang="ts">
import Button from 'primevue/button';
import Message from 'primevue/message';
import ProgressSpinner from 'primevue/progressspinner';
import Select from 'primevue/select';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref } from 'vue';
import { fetchSettings, patchSettings } from '@/api/settingsApi';
import {
  CEFR_LEVELS,
  type AppSettings,
  type CefrLevel,
  type TranslationLanguage,
} from '@/types/settings';

const toast = useToast();

const loadState = ref<'idle' | 'loading' | 'error'>('idle');
const loadError = ref<string | null>(null);
const saveInFlight = ref(false);

const serverRow = ref<AppSettings | null>(null);
const translationLanguage = ref<TranslationLanguage>('en');
const defaultCefr = ref<CefrLevel>('B1');

const translationOptions = [
  { label: 'Englisch', value: 'en' as const },
  { label: 'Ukrainisch', value: 'uk' as const },
];

const cefrOptions = CEFR_LEVELS.map((level) => ({ label: level, value: level }));

function applyRow(row: AppSettings) {
  serverRow.value = row;
  translationLanguage.value = row.translation_language;
  defaultCefr.value = row.default_cefr;
}

async function load() {
  loadState.value = 'loading';
  loadError.value = null;
  const res = await fetchSettings();
  if (!res.ok) {
    loadState.value = 'error';
    loadError.value = res.message;
    return;
  }
  applyRow(res.data);
  loadState.value = 'idle';
}

async function onSave() {
  if (saveInFlight.value) {
    return;
  }
  saveInFlight.value = true;
  try {
    const res = await patchSettings({
      translation_language: translationLanguage.value,
      default_cefr: defaultCefr.value,
    });
    if (!res.ok) {
      toast.add({
        severity: 'error',
        summary: 'Speichern',
        detail: res.message,
        life: 6000,
      });
      return;
    }
    const verify = await fetchSettings();
    if (!verify.ok) {
      toast.add({
        severity: 'warn',
        summary: 'Gespeichert',
        detail: `Einstellungen gespeichert, aber erneutes Laden ist fehlgeschlagen: ${verify.message}`,
        life: 6000,
      });
      applyRow(res.data);
      return;
    }
    applyRow(verify.data);
    toast.add({
      severity: 'success',
      summary: 'Einstellungen',
      detail: 'Gespeichert.',
      life: 3000,
    });
  } finally {
    saveInFlight.value = false;
  }
}

function onReset() {
  const row = serverRow.value;
  if (row) {
    applyRow(row);
  }
}

onMounted(() => {
  void load();
});
</script>

<template>
  <section class="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6 sm:px-6">
    <div>
      <h2 class="text-lg font-semibold text-slate-800 sm:text-xl">Einstellungen</h2>
      <p class="text-xs text-slate-500">Übersetzungssprache und Standard-CEFR-Level für die App.</p>
    </div>

    <div v-if="loadState === 'loading' && !serverRow" class="flex justify-center py-12">
      <ProgressSpinner stroke-width="4" style="width: 3rem; height: 3rem" />
    </div>

    <div v-else-if="loadState === 'error' && loadError" class="flex flex-col gap-3">
      <Message severity="error" :closable="false">
        {{ loadError }}
      </Message>
      <Button
        label="Erneut versuchen"
        icon="pi pi-refresh"
        severity="secondary"
        outlined
        data-testid="settings-retry"
        @click="load"
      />
    </div>

    <template v-else-if="serverRow">
      <div class="flex flex-col gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-slate-600" for="settings-translation"
            >Übersetzungssprache</label
          >
          <Select
            id="settings-translation"
            v-model="translationLanguage"
            :options="translationOptions"
            option-label="label"
            option-value="value"
            class="w-full max-w-md"
          />
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-slate-600" for="settings-cefr"
            >Standard-CEFR-Level</label
          >
          <Select
            id="settings-cefr"
            v-model="defaultCefr"
            :options="cefrOptions"
            option-label="label"
            option-value="value"
            class="w-full max-w-xs"
          />
        </div>

        <div class="flex flex-wrap gap-2">
          <Button
            label="Speichern"
            icon="pi pi-check"
            :loading="saveInFlight"
            :disabled="saveInFlight"
            data-testid="settings-save"
            @click="onSave"
          />
          <Button
            label="Zurücksetzen"
            icon="pi pi-undo"
            severity="secondary"
            outlined
            :disabled="saveInFlight"
            type="button"
            @click="onReset"
          />
        </div>
      </div>
    </template>
  </section>
</template>
