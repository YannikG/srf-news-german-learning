<script setup lang="ts">
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import ProgressSpinner from 'primevue/progressspinner';
import Tag from 'primevue/tag';
import { computed, ref } from 'vue';
import { useToast } from 'primevue/usetoast';
import { useArticlesList } from '@/composables/useArticlesList';
import { useDebouncedRef } from '@/composables/useDebouncedRef';
import { useNewsDateRouteSync } from '@/composables/useNewsDateRouteSync';
import { useNewsRefresh } from '@/composables/useNewsRefresh';
import { notifyPostNewsRefresh } from '@/news/notifyPostNewsRefresh';
import { newsProviderLabel } from '@/utils/newsProviderLabel';
import { stripMediaFromText } from '@/utils/stripMediaFromText';

const toast = useToast();
const {
  loading: refreshLoading,
  refresh,
  cooldownActive,
  nextAllowedFetchAtIso,
} = useNewsRefresh();

const selectedDate = useNewsDateRouteSync();
const searchInput = ref('');
const debouncedSearch = useDebouncedRef(searchInput, 300);

const { items, nextCursor, listLoading, listError, loadList } = useArticlesList({
  selectedDate,
  debouncedSearch,
});

const pullStartY = ref<number | null>(null);
const pullDistance = ref(0);
const touchRefreshing = ref(false);

function leadPreview(lead: string | null): string {
  if (!lead) return '';
  return stripMediaFromText(lead).trim();
}

const cooldownLabel = computed(() => {
  const iso = nextAllowedFetchAtIso.value;
  if (!iso || !cooldownActive.value) return '';
  try {
    return new Date(iso).toLocaleString('de-CH', {
      dateStyle: 'short',
      timeStyle: 'short',
    });
  } catch {
    return iso;
  }
});

async function onRefreshClick() {
  const r = await refresh();
  const outcome = notifyPostNewsRefresh(toast.add, r, cooldownLabel.value);
  if (outcome === 'reload_list') {
    await loadList(true);
  }
}

function onTouchStart(e: TouchEvent) {
  if (window.scrollY > 0) return;
  const t = e.touches[0];
  if (!t) return;
  pullStartY.value = t.clientY;
  pullDistance.value = 0;
}

function onTouchMove(e: TouchEvent) {
  if (pullStartY.value == null || window.scrollY > 0) return;
  const t = e.touches[0];
  if (!t) return;
  const d = t.clientY - pullStartY.value;
  if (d > 0) pullDistance.value = d;
}

async function onTouchEnd() {
  const start = pullStartY.value;
  pullStartY.value = null;
  if (start == null) return;
  if (pullDistance.value > 72 && !touchRefreshing.value && !refreshLoading.value) {
    touchRefreshing.value = true;
    try {
      await onRefreshClick();
    } finally {
      touchRefreshing.value = false;
      pullDistance.value = 0;
    }
  } else {
    pullDistance.value = 0;
  }
}
</script>

<template>
  <section
    class="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6 sm:px-6"
    @touchstart.passive="onTouchStart"
    @touchmove.passive="onTouchMove"
    @touchend="onTouchEnd"
  >
    <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 class="text-lg font-semibold text-slate-800 sm:text-xl">News</h2>
        <p class="text-xs text-slate-500">Timeline aus der lokalen Datenbank</p>
      </div>
      <div class="flex flex-wrap items-end gap-2">
        <label class="flex flex-col gap-1 text-xs font-medium text-slate-600">
          Datum
          <input
            v-model="selectedDate"
            type="date"
            class="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 shadow-sm"
          />
        </label>
        <Button
          label="Aktualisieren"
          icon="pi pi-refresh"
          :loading="refreshLoading || touchRefreshing"
          :disabled="cooldownActive || refreshLoading || touchRefreshing"
          size="small"
          @click="onRefreshClick"
        />
      </div>
    </div>

    <p v-if="pullDistance > 40" class="text-center text-xs text-slate-500">
      Loslassen zum Aktualisieren …
    </p>

    <p v-if="cooldownActive && cooldownLabel" class="text-xs text-amber-800">
      Nächster Abruf ab {{ cooldownLabel }} möglich.
    </p>

    <label class="flex w-full flex-col gap-1 text-xs font-medium text-slate-600">
      Suche im Titel
      <InputText v-model="searchInput" class="w-full" type="search" autocomplete="off" />
    </label>

    <div v-if="listLoading && items.length === 0" class="flex justify-center py-12">
      <ProgressSpinner stroke-width="4" style="width: 3rem; height: 3rem" />
    </div>

    <p v-else-if="listError" class="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
      {{ listError }}
    </p>

    <p v-else-if="items.length === 0" class="text-sm text-slate-600">
      Keine Artikel für dieses Datum{{ debouncedSearch ? ' und diese Suche' : '' }}.
    </p>

    <ul v-else class="flex flex-col gap-3" aria-label="Artikelliste">
      <li v-for="a in items" :key="a.id">
        <RouterLink
          :to="{ name: 'article', params: { id: a.id }, query: { d: selectedDate } }"
          class="block rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:border-slate-300 hover:shadow"
        >
          <div class="flex flex-wrap items-center gap-2">
            <p class="text-xs text-slate-500">{{ a.release_date }}</p>
            <Tag
              :value="`Quelle: ${newsProviderLabel(a.news_provider)}`"
              severity="secondary"
              class="text-xs"
            />
          </div>
          <h3 class="font-semibold text-slate-900">{{ stripMediaFromText(a.title) }}</h3>
          <p v-if="leadPreview(a.lead)" class="mt-1 line-clamp-3 text-sm text-slate-600">
            {{ leadPreview(a.lead) }}
          </p>
          <p class="mt-2 text-xs font-medium text-sky-700">Weiterlesen</p>
        </RouterLink>
      </li>
    </ul>

    <div v-if="listLoading && items.length > 0" class="flex justify-center py-4">
      <ProgressSpinner stroke-width="4" style="width: 2rem; height: 2rem" />
    </div>

    <Button
      v-if="nextCursor"
      label="Mehr laden"
      severity="secondary"
      outlined
      class="self-center"
      :loading="listLoading"
      @click="loadList(false)"
    />
  </section>
</template>
