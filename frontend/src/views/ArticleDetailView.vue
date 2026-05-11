<script setup lang="ts">
import SelectButton from 'primevue/selectbutton';
import ProgressSpinner from 'primevue/progressspinner';
import Tag from 'primevue/tag';
import { computed, onUnmounted, ref, watch } from 'vue';
import type { RouteLocationRaw } from 'vue-router';
import { useRoute } from 'vue-router';
import { fetchArticleDetail } from '@/api/fetchArticles';
import type { ArticleDetail } from '@/types/article';
import { renderArticleMarkdown } from '@/utils/renderArticleMarkdown';
import { parseIsoDateQueryParam } from '@/utils/routerQueryDate';
import { newsProviderLabel } from '@/utils/newsProviderLabel';
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

const bodyMarkdown = computed(() => {
  if (!article.value) return '';
  const raw =
    viewMode.value === 'simplified' && hasSimplification.value
      ? article.value.markdown_simplified!
      : article.value.markdown_original;
  return raw;
});

const bodyHtml = computed(() =>
  bodyMarkdown.value ? renderArticleMarkdown(bodyMarkdown.value) : ''
);

const newsListDateParam = computed(() => parseIsoDateQueryParam(route.query.d));

const backToNewsRoute = computed(
  (): RouteLocationRaw =>
    newsListDateParam.value ? { path: '/', query: { d: newsListDateParam.value } } : '/'
);

/** Ignores stale detail responses when the route id changes quickly. */
let detailLoadSeq = 0;

async function load(id: number) {
  const seq = ++detailLoadSeq;
  loading.value = true;
  error.value = null;
  article.value = null;
  viewMode.value = 'original';
  try {
    const res = await fetchArticleDetail(id);
    if (seq !== detailLoadSeq) return;
    if (!res.ok) {
      error.value = res.message;
      return;
    }
    article.value = res.data;
    viewMode.value = 'original';
  } finally {
    if (seq === detailLoadSeq) {
      loading.value = false;
    }
  }
}

watch(
  () => route.params.id,
  (id) => {
    const n = Number(id);
    if (!Number.isFinite(n) || n < 1) {
      detailLoadSeq += 1;
      error.value = 'Ungültige Artikel-ID';
      loading.value = false;
      article.value = null;
      return;
    }
    void load(n);
  },
  { immediate: true }
);

onUnmounted(() => {
  detailLoadSeq += 1;
  loading.value = false;
});
</script>

<template>
  <article class="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6 sm:px-6">
    <div class="flex flex-wrap items-center gap-2">
      <RouterLink :to="backToNewsRoute" class="text-sm font-medium text-sky-800 hover:underline">
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
        <div class="flex flex-wrap items-center gap-2">
          <p class="text-xs text-slate-500">{{ article.release_date }}</p>
          <Tag
            :value="`Quelle: ${newsProviderLabel(article.news_provider)}`"
            severity="secondary"
            class="text-xs"
          />
        </div>
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
        <div
          class="article-md max-w-none text-sm text-slate-800 [&_a]:text-sky-800 [&_a]:underline [&_blockquote]:border-l-4 [&_blockquote]:border-slate-300 [&_blockquote]:pl-3 [&_code]:rounded [&_code]:bg-slate-100 [&_code]:px-1 [&_h1]:mb-3 [&_h1]:text-xl [&_h1]:font-bold [&_h2]:mb-2 [&_h2]:mt-4 [&_h2]:text-lg [&_h2]:font-semibold [&_li]:my-0.5 [&_ol]:my-2 [&_p]:my-2 [&_pre]:overflow-x-auto [&_pre]:rounded [&_pre]:bg-slate-50 [&_pre]:p-3 [&_ul]:my-2"
          v-html="bodyHtml"
        />
      </section>
    </template>
  </article>
</template>
