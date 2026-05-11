<script setup lang="ts">
import AutoComplete, { type AutoCompleteCompleteEvent } from 'primevue/autocomplete';
import Button from 'primevue/button';
import Column from 'primevue/column';
import DataTable from 'primevue/datatable';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import Message from 'primevue/message';
import Popover from 'primevue/popover';
import ProgressSpinner from 'primevue/progressspinner';
import Select from 'primevue/select';
import Textarea from 'primevue/textarea';
import { useConfirm } from 'primevue/useconfirm';
import { useToast } from 'primevue/usetoast';
import DOMPurify from 'dompurify';
import { reactive, ref, type Ref } from 'vue';
import { usePonsLookup } from '@/composables/usePonsLookup';
import { useWordsDictionary } from '@/composables/useWordsDictionary';
import type { PonsHit } from '@/types/pons';
import type { CefrLevel, Word, WordDifficulty } from '@/types/word';
import { CEFR_LEVEL_FILTER_NONE, CEFR_LEVELS, WORD_DIFFICULTIES } from '@/types/word';

const toast = useToast();
const confirm = useConfirm();

const {
  items,
  loading,
  error,
  categoryFilter,
  cefrLevelFilter,
  knownCategories,
  create,
  update,
  remove,
} = useWordsDictionary();

const { ponsAvailable, getState, lookup: ponsLookup } = usePonsLookup();

const ponsPopoverRef = ref();
const ponsPopoverWord = ref<string>('');
const ponsPopoverHits = ref<PonsHit[]>([]);
const ponsPopoverError = ref<string | null>(null);
const ponsPopoverLoading = ref(false);

async function onPonsLookup(row: Word, event: Event) {
  ponsPopoverWord.value = row.german_label;
  ponsPopoverHits.value = [];
  ponsPopoverError.value = null;
  ponsPopoverLoading.value = true;
  ponsPopoverRef.value?.show(event);

  const result = await ponsLookup(row.german_label);
  ponsPopoverLoading.value = false;
  if (result.ok) {
    ponsPopoverHits.value = result.hits;
    if (result.hits.length === 0) {
      ponsPopoverError.value = 'Kein Treffer bei PONS gefunden.';
    }
  } else {
    ponsPopoverError.value = result.message;
  }
}

function extractFirstTarget(hits: PonsHit[]): string | null {
  for (const hit of hits) {
    if (hit.type === 'translation' && hit.target) {
      return stripHtml(hit.target);
    }
    if (hit.type === 'entry' && hit.roms) {
      for (const rom of hit.roms) {
        for (const arab of rom.arabs) {
          for (const tr of arab.translations) {
            if (tr.target) return stripHtml(tr.target);
          }
        }
      }
    }
  }
  return null;
}

function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
}

function stripHtml(html: string): string {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  return doc.body.textContent?.trim() ?? html;
}

function adoptPonsTranslation() {
  const row = items.value.find((w) => w.german_label === ponsPopoverWord.value);
  if (!row) return;
  const target = extractFirstTarget(ponsPopoverHits.value);
  if (!target) return;
  ponsPopoverRef.value?.hide();
  editingId.value = row.id;
  form.german_label = row.german_label;
  form.category = row.category;
  form.translation = target;
  form.difficulty = row.difficulty;
  form.cefr_level = toFormCefr(row.cefr_level);
  labelError.value = null;
  dialogVisible.value = true;
}

const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const form = reactive({
  german_label: '',
  category: '',
  translation: '',
  difficulty: 'Neu' as WordDifficulty,
  cefr_level: null as CefrLevel | null,
});
const labelError = ref<string | null>(null);
const saveInFlight = ref(false);

const difficultySelectOptions = WORD_DIFFICULTIES.map((d) => ({ label: d, value: d }));

const cefrLevelToolbarOptions = [
  { label: 'Alle Level', value: '' },
  { label: 'Kein Level', value: CEFR_LEVEL_FILTER_NONE },
  ...CEFR_LEVELS.map((level) => ({ label: level, value: level })),
];

const cefrFormSelectOptions = [
  { label: 'Kein Level', value: null },
  ...CEFR_LEVELS.map((level) => ({ label: level, value: level })),
];

function toFormCefr(value: Word['cefr_level']): CefrLevel | null {
  if (value == null) {
    return null;
  }
  return (CEFR_LEVELS as readonly string[]).includes(value) ? (value as CefrLevel) : null;
}

const toolbarCategorySuggestions = ref<string[]>([]);
const dialogCategorySuggestions = ref<string[]>([]);

function filterCategorySuggestions(query: string, source: readonly string[]): string[] {
  const q = query.trim().toLowerCase();
  if (!q) {
    return [...source];
  }
  return source.filter((c) => c.toLowerCase().includes(q));
}

function applyCategoryFilterSuggestions(
  target: Ref<string[]>,
  event: AutoCompleteCompleteEvent
): void {
  target.value = filterCategorySuggestions(event.query, knownCategories.value);
}

function onToolbarCategoryComplete(event: AutoCompleteCompleteEvent) {
  applyCategoryFilterSuggestions(toolbarCategorySuggestions, event);
}

function onDialogCategoryComplete(event: AutoCompleteCompleteEvent) {
  applyCategoryFilterSuggestions(dialogCategorySuggestions, event);
}

function resetForm() {
  form.german_label = '';
  form.category = '';
  form.translation = '';
  form.difficulty = 'Neu';
  form.cefr_level = null;
  labelError.value = null;
}

function openCreate() {
  editingId.value = null;
  resetForm();
  dialogVisible.value = true;
}

function openEdit(row: Word) {
  editingId.value = row.id;
  form.german_label = row.german_label;
  form.category = row.category;
  form.translation = row.translation;
  form.difficulty = row.difficulty;
  form.cefr_level = toFormCefr(row.cefr_level);
  labelError.value = null;
  dialogVisible.value = true;
}

function formatTs(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('de-CH', {
    dateStyle: 'short',
    timeStyle: 'short',
  });
}

async function saveDialog() {
  if (saveInFlight.value) {
    return;
  }
  const trimmed = form.german_label.trim();
  if (!trimmed) {
    labelError.value = 'Deutschbezeichnung darf nicht leer sein.';
    return;
  }
  labelError.value = null;
  saveInFlight.value = true;
  try {
    if (editingId.value == null) {
      const res = await create({
        german_label: trimmed,
        category: form.category.trim(),
        translation: form.translation.trim(),
        difficulty: form.difficulty,
        cefr_level: form.cefr_level,
      });
      if (!res.ok) {
        toast.add({ severity: 'error', summary: 'Speichern', detail: res.message, life: 6000 });
        return;
      }
      toast.add({ severity: 'success', summary: 'Wort angelegt', life: 3000 });
    } else {
      const res = await update(editingId.value, {
        german_label: trimmed,
        category: form.category.trim(),
        translation: form.translation.trim(),
        difficulty: form.difficulty,
        cefr_level: form.cefr_level,
      });
      if (!res.ok) {
        toast.add({ severity: 'error', summary: 'Speichern', detail: res.message, life: 6000 });
        return;
      }
      toast.add({ severity: 'success', summary: 'Wort aktualisiert', life: 3000 });
    }
    dialogVisible.value = false;
  } finally {
    saveInFlight.value = false;
  }
}

function confirmDelete(row: Word) {
  confirm.require({
    message: `Eintrag «${row.german_label}» wirklich löschen?`,
    header: 'Löschen bestätigen',
    rejectProps: { label: 'Abbrechen', severity: 'secondary', outlined: true },
    acceptProps: { label: 'Löschen', severity: 'danger' },
    accept: () => {
      void (async () => {
        const res = await remove(row.id);
        if (!res.ok) {
          toast.add({ severity: 'error', summary: 'Löschen', detail: res.message, life: 6000 });
          return;
        }
        toast.add({ severity: 'success', summary: 'Gelöscht', life: 3000 });
      })();
    },
  });
}
</script>

<template>
  <div class="mx-auto max-w-5xl px-3 py-4 sm:px-4">
    <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">Wörterbuch</h2>
        <p class="text-sm text-slate-600">
          Einträge bearbeiten, filtern und verwalten (lokale Datenbank).
        </p>
      </div>
      <div class="flex flex-col gap-2 sm:flex-row sm:items-end">
        <div class="flex min-w-0 flex-col gap-1">
          <label class="text-xs font-medium text-slate-600" for="dict-category-filter-input"
            >Kategorie</label
          >
          <AutoComplete
            v-model="categoryFilter"
            input-id="dict-category-filter-input"
            :suggestions="toolbarCategorySuggestions"
            class="w-full min-w-[12rem] sm:w-56"
            placeholder="Alle oder Kategorie wählen"
            :dropdown="true"
            :min-length="0"
            :force-selection="false"
            :show-clear="true"
            complete-on-focus
            @complete="onToolbarCategoryComplete"
          />
        </div>
        <div class="flex min-w-0 flex-col gap-1">
          <label class="text-xs font-medium text-slate-600" for="dict-cefr-filter"
            >CEFR-Level</label
          >
          <Select
            id="dict-cefr-filter"
            v-model="cefrLevelFilter"
            :options="cefrLevelToolbarOptions"
            option-label="label"
            option-value="value"
            placeholder="Alle Level"
            class="w-full min-w-[10rem] sm:w-44"
          />
        </div>
        <Button type="button" label="Neues Wort" class="shrink-0" @click="openCreate" />
      </div>
    </div>

    <Message v-if="error" severity="error" class="mb-3" :closable="false">{{ error }}</Message>

    <div class="-mx-1 overflow-x-auto sm:mx-0">
      <DataTable
        :value="items"
        :loading="loading"
        data-key="id"
        striped-rows
        scrollable
        table-style="min-width: 52rem"
        class="text-sm"
        :pt="{ table: { class: 'text-sm' } }"
      >
        <template #empty>
          <span class="text-slate-500">Keine Einträge.</span>
        </template>
        <Column field="german_label" header="Deutsch" />
        <Column field="category" header="Kategorie" />
        <Column field="difficulty" header="Schwierigkeit" style="width: 8rem" />
        <Column field="translation" header="Übersetzung">
          <template #body="{ data }">
            <span v-if="data.translation">{{ data.translation }}</span>
            <Button
              v-else-if="ponsAvailable"
              type="button"
              label="Übersetzung anzeigen"
              size="small"
              severity="secondary"
              text
              class="p-0 text-xs"
              @click="onPonsLookup(data, $event)"
            />
            <span v-else class="text-slate-400">—</span>
          </template>
        </Column>
        <Column field="cefr_level" header="CEFR">
          <template #body="{ data }">
            {{ data.cefr_level ?? '—' }}
          </template>
        </Column>
        <Column header="Erstellt" style="width: 9rem">
          <template #body="{ data }">
            {{ formatTs(data.created_at) }}
          </template>
        </Column>
        <Column header="Aktualisiert" style="width: 9rem">
          <template #body="{ data }">
            {{ formatTs(data.updated_at) }}
          </template>
        </Column>
        <Column header="" style="width: 14rem" :exportable="false">
          <template #body="{ data }">
            <div class="flex flex-wrap items-center gap-1">
              <Button
                v-if="ponsAvailable"
                type="button"
                label="PONS"
                size="small"
                severity="info"
                outlined
                @click="onPonsLookup(data, $event)"
              />
              <Button
                type="button"
                label="Bearbeiten"
                size="small"
                severity="secondary"
                outlined
                @click="openEdit(data)"
              />
              <Button
                type="button"
                label="Löschen"
                size="small"
                severity="danger"
                outlined
                @click="confirmDelete(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <Popover ref="ponsPopoverRef">
      <div class="w-72 max-w-[90vw]">
        <p class="mb-2 text-sm font-semibold text-slate-800">PONS: {{ ponsPopoverWord }}</p>
        <div v-if="ponsPopoverLoading" class="flex items-center justify-center py-4">
          <ProgressSpinner style="width: 2rem; height: 2rem" stroke-width="4" />
        </div>
        <div v-else-if="ponsPopoverError" class="text-sm text-red-600">
          {{ ponsPopoverError }}
        </div>
        <div v-else>
          <ul class="max-h-48 space-y-1 overflow-y-auto text-sm text-slate-700">
            <template v-for="(hit, hi) in ponsPopoverHits" :key="hi">
              <template v-if="hit.type === 'translation'">
                <li class="rounded bg-slate-50 px-2 py-1">
                  <span v-html="sanitizeHtml(hit.target)"></span>
                </li>
              </template>
              <template v-else-if="hit.type === 'entry'">
                <template v-for="(rom, ri) in hit.roms" :key="`${hi}-${ri}`">
                  <template v-for="(arab, ai) in rom.arabs" :key="`${hi}-${ri}-${ai}`">
                    <li
                      v-for="(tr, ti) in arab.translations"
                      :key="`${hi}-${ri}-${ai}-${ti}`"
                      class="rounded bg-slate-50 px-2 py-1"
                    >
                      <span v-html="sanitizeHtml(tr.target)"></span>
                    </li>
                  </template>
                </template>
              </template>
            </template>
          </ul>
          <Button
            v-if="ponsPopoverHits.length > 0"
            type="button"
            label="In Feld übernehmen"
            size="small"
            class="mt-2 w-full"
            @click="adoptPonsTranslation()"
          />
        </div>
      </div>
    </Popover>

    <Dialog
      v-model:visible="dialogVisible"
      modal
      :header="editingId == null ? 'Neues Wort' : 'Wort bearbeiten'"
      class="w-[min(100vw-2rem,28rem)]"
      :draggable="false"
    >
      <div class="flex flex-col gap-3 pt-1">
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-slate-700" for="wf-de">Deutschbezeichnung *</label>
          <InputText id="wf-de" v-model="form.german_label" class="w-full" autocomplete="off" />
          <p v-if="labelError" class="text-sm text-red-600">{{ labelError }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-slate-700" for="wf-cat-input">Kategorie</label>
          <AutoComplete
            v-model="form.category"
            input-id="wf-cat-input"
            :suggestions="dialogCategorySuggestions"
            class="w-full"
            placeholder="Bestehende wählen oder neue eingeben"
            :dropdown="true"
            :min-length="0"
            :force-selection="false"
            :show-clear="true"
            complete-on-focus
            @complete="onDialogCategoryComplete"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-slate-700" for="wf-diff">Schwierigkeit</label>
          <Select
            id="wf-diff"
            v-model="form.difficulty"
            :options="difficultySelectOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-slate-700" for="wf-tr">Übersetzung</label>
          <Textarea id="wf-tr" v-model="form.translation" rows="3" class="w-full" auto-resize />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-slate-700" for="wf-cefr">CEFR-Level</label>
          <Select
            id="wf-cefr"
            v-model="form.cefr_level"
            :options="cefrFormSelectOptions"
            option-label="label"
            option-value="value"
            placeholder="Kein Level"
            class="w-full"
            :show-clear="true"
          />
        </div>
      </div>
      <template #footer>
        <Button
          type="button"
          label="Abbrechen"
          severity="secondary"
          @click="dialogVisible = false"
        />
        <Button
          type="button"
          label="Speichern"
          :loading="saveInFlight"
          :disabled="saveInFlight"
          @click="saveDialog"
        />
      </template>
    </Dialog>
  </div>
</template>
