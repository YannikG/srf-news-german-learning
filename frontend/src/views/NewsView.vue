<script setup lang="ts">
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import ProgressSpinner from 'primevue/progressspinner';
import { computed, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { fetchArticlesList } from '@/api/fetchArticles';
import { useNewsRefresh } from '@/composables/useNewsRefresh';
import type { ArticleListItem } from '@/types/article';
import { stripMediaFromText } from '@/utils/stripMediaFromText';

const toast = useToast();
const route = useRoute();
const router = useRouter();
const {
  loading: refreshLoading,
  refresh,
  cooldownActive,
  nextAllowedFetchAtIso,
} = useNewsRefresh();

function parseQueryDate(q: unknown): string | null {
  const raw = Array.isArray(q) ? q[0] : q;
  if (typeof raw !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(raw)) return null;
  return raw;
}

/** Flatten router query values to plain strings for ``router.replace``. */
function queryRecordForReplace(): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, val] of Object.entries(route.query)) {
    const first = Array.isArray(val) ? val[0] : val;
    if (typeof first === 'string' && first.length > 0) {
      out[key] = first;
    }
  }
  return out;
}

function localIsoDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

const items = ref<ArticleListItem[]>([]);
const nextCursor = ref<string | null>(null);
const listLoading = ref(false);
const listError = ref<string | null>(null);

const selectedDate = ref(parseQueryDate(route.query.d) ?? localIsoDate(new Date()));

watch(
  () => route.query.d,
  (d) => {
    const p = parseQueryDate(d);
    if (p) selectedDate.value = p;
  }
);

watch(selectedDate, (d) => {
  const cur = parseQueryDate(route.query.d);
  if (cur === d) return;
  void router.replace({ path: '/', query: { ...queryRecordForReplace(), d } });
});

const searchInput = ref('');
const debouncedSearch = ref('');
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

watch(searchInput, (v) => {
  if (debounceTimer != null) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    debouncedSearch.value = v;
    debounceTimer = null;
  }, 300);
});

onUnmounted(() => {
  if (debounceTimer != null) {
    clearTimeout(debounceTimer);
    debounceTimer = null;
  }
});

const pullStartY = ref<number | null>(null);
const pullDistance = ref(0);
const touchRefreshing = ref(false);

function leadPreview(lead: string | null): string {
  if (!lead) return '';
  return stripMediaFromText(lead).trim();
}

/** Ignores stale list responses when date or search changes quickly. */
let listRequestSeq = 0;

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

async function loadList(reset: boolean) {
  const seq = ++listRequestSeq;
  if (reset) {
    nextCursor.value = null;
    items.value = [];
  }
  listLoading.value = true;
  listError.value = null;
  try {
    const res = await fetchArticlesList({
      date: selectedDate.value,
      q: debouncedSearch.value,
      cursor: reset ? null : nextCursor.value,
      limit: 20,
    });
    if (seq !== listRequestSeq) return;
    if (!res.ok) {
      listError.value = res.message;
      return;
    }
    if (reset) {
      items.value = res.data.items;
    } else {
      items.value = [...items.value, ...res.data.items];
    }
    nextCursor.value = res.data.next_cursor;
  } finally {
    if (seq === listRequestSeq) {
      listLoading.value = false;
    }
  }
}

watch(
  [selectedDate, debouncedSearch],
  () => {
    void loadList(true);
  },
  { immediate: true }
);

async function onRefreshClick() {
  const r = await refresh();
  if (!r.ok) {
    if (r.code === 'oauth_not_configured') {
      toast.add({
        severity: 'warn',
        summary: 'SRG nicht konfiguriert',
        detail: r.message,
        life: 12000,
      });
      return;
    }
    const summary =
      r.status === 429 || r.code === 'upstream_rate_limited'
        ? 'SRG Rate-Limit (429)'
        : 'Refresh fehlgeschlagen';
    toast.add({
      severity: r.status === 429 ? 'warn' : 'error',
      summary,
      detail: r.message,
      life: 8000,
    });
    return;
  }
  if (r.data.fetched) {
    toast.add({
      severity: 'success',
      summary: 'News aktualisiert',
      detail: `${r.data.articles_upserted} Artikel verarbeitet.`,
      life: 4000,
    });
    await loadList(true);
  } else {
    toast.add({
      severity: 'info',
      summary: 'Cooldown',
      detail: `Nächster Abruf ab ${cooldownLabel.value || r.data.next_allowed_fetch_at}.`,
      life: 5000,
    });
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
      Nächster SRG-Abruf ab {{ cooldownLabel }} möglich.
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
          <p class="text-xs text-slate-500">{{ a.release_date }}</p>
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
