<script setup lang="ts">
import SelectButton from 'primevue/selectbutton';
import ProgressSpinner from 'primevue/progressspinner';
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { fetchArticleDetail } from '@/api/fetchArticles';
import type { ArticleDetail } from '@/types/article';
import { stripMediaFromText } from '@/utils/stripMediaFromText';

const route = useRoute();
const article = ref<ArticleDetail | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const viewMode = ref<'original' | 'simplified'>('original');

const viewOptions = [
  { label: 'Original', value: 'original' as const },
  { label: 'Vereinfacht', value: 'simplified' as const },
];

const hasSimplification = computed(
  () => !!article.value?.markdown_simplified && article.value.markdown_simplified.length > 0
);

const bodyText = computed(() => {
  if (!article.value) return '';
  const raw =
    viewMode.value === 'simplified' && hasSimplification.value
      ? article.value.markdown_simplified!
      : article.value.markdown_original;
  return stripMediaFromText(raw);
});

async function load(id: number) {
  loading.value = true;
  error.value = null;
  article.value = null;
  viewMode.value = 'original';
  const res = await fetchArticleDetail(id);
  loading.value = false;
  if (!res.ok) {
    error.value = res.message;
    return;
  }
  article.value = res.data;
  viewMode.value = 'original';
}

watch(
  () => route.params.id,
  (id) => {
    const n = Number(id);
    if (!Number.isFinite(n) || n < 1) {
      error.value = 'Ungültige Artikel-ID';
      return;
    }
    void load(n);
  },
  { immediate: true }
);
</script>

<template>
  <article class="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6 sm:px-6">
    <div class="flex flex-wrap items-center gap-2">
      <RouterLink
        :to="route.query.d ? { path: '/', query: { d: route.query.d } } : '/'"
        class="text-sm font-medium text-sky-800 hover:underline"
      >
        Zurück zur News
      </RouterLink>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <ProgressSpinner stroke-width="4" style="width: 3rem; height: 3rem" />
    </div>

    <p v-else-if="error" class="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
      {{ error }}
    </p>

    <template v-else-if="article">
      <header class="border-b border-slate-200 pb-4">
        <p class="text-xs text-slate-500">{{ article.release_date }}</p>
        <h1 class="text-xl font-bold text-slate-900 sm:text-2xl">
          {{ stripMediaFromText(article.title) }}
        </h1>
        <p v-if="article.lead" class="mt-2 text-sm text-slate-600">
          {{ stripMediaFromText(article.lead) }}
        </p>
      </header>

      <div v-if="hasSimplification" class="flex flex-col gap-2">
        <SelectButton
          v-model="viewMode"
          :options="viewOptions"
          option-label="label"
          option-value="value"
          aria-label="Darstellung Original oder vereinfacht"
        />
        <p v-if="article.simplification_cefr_level" class="text-xs text-slate-500">
          Vereinfachung: Niveau {{ article.simplification_cefr_level }}
        </p>
      </div>
      <p v-else class="text-sm text-slate-600">
        Noch keine gespeicherte Vereinfachung für diesen Artikel.
      </p>

      <section
        aria-label="Artikeltext"
        class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      >
        <pre class="whitespace-pre-wrap break-words font-sans text-sm text-slate-800">{{
          bodyText
        }}</pre>
      </section>
    </template>
  </article>
</template>
