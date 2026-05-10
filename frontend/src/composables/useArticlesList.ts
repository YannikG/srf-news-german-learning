import { ref, watch, type Ref } from 'vue';
import { fetchArticlesList, isAbortError } from '@/api/fetchArticles';
import type { ArticleListItem } from '@/types/article';

const PAGE_SIZE = 20;

/** Abort in-flight list fetch when a newer ``loadList`` starts; also used for timeout. */
const LIST_FETCH_TIMEOUT_MS = 30_000;

function normalizeListPayload(data: { items?: unknown; next_cursor?: unknown }): {
  items: ArticleListItem[];
  next_cursor: string | null;
} {
  const raw = data.items;
  const items = Array.isArray(raw) ? (raw as ArticleListItem[]) : [];
  const nc = data.next_cursor;
  const next_cursor = typeof nc === 'string' || nc === null ? nc : null;
  return { items, next_cursor };
}

/**
 * Fetches paginated articles for a fixed calendar day and optional title search.
 * Drops stale HTTP results when ``selectedDate`` or ``debouncedSearch`` changes mid-flight.
 */
export function useArticlesList(params: {
  selectedDate: Ref<string>;
  debouncedSearch: Ref<string>;
}) {
  const items = ref<ArticleListItem[]>([]);
  const nextCursor = ref<string | null>(null);
  const listLoading = ref(false);
  const listError = ref<string | null>(null);
  let listRequestSeq = 0;
  let listFetchCtrl: AbortController | null = null;

  async function loadList(reset: boolean): Promise<void> {
    listFetchCtrl?.abort();
    const ctrl = new AbortController();
    listFetchCtrl = ctrl;

    const seq = ++listRequestSeq;
    if (reset) {
      nextCursor.value = null;
      items.value = [];
    }
    listLoading.value = true;
    listError.value = null;
    const timeoutId = window.setTimeout(() => ctrl.abort(), LIST_FETCH_TIMEOUT_MS);
    try {
      const res = await fetchArticlesList({
        date: params.selectedDate.value,
        q: params.debouncedSearch.value,
        cursor: reset ? null : nextCursor.value,
        limit: PAGE_SIZE,
        signal: ctrl.signal,
      });
      if (seq !== listRequestSeq) return;
      if (!res.ok) {
        listError.value = res.message;
        return;
      }
      const { items: page, next_cursor } = normalizeListPayload(res.data);
      if (reset) {
        items.value = page;
      } else {
        items.value = [...items.value, ...page];
      }
      nextCursor.value = next_cursor;
    } catch (e) {
      if (isAbortError(e)) {
        if (seq !== listRequestSeq) {
          return;
        }
        listError.value =
          'Die Anfrage hat zu lange gedauert. Bitte Seite neu laden oder später erneut versuchen.';
        return;
      }
      if (seq === listRequestSeq) {
        listError.value = e instanceof Error ? e.message : 'Netzwerkfehler';
      }
    } finally {
      window.clearTimeout(timeoutId);
      if (listFetchCtrl === ctrl) {
        listFetchCtrl = null;
      }
      if (seq === listRequestSeq) {
        listLoading.value = false;
      }
    }
  }

  watch(
    [params.selectedDate, params.debouncedSearch],
    () => {
      void loadList(true);
    },
    { immediate: true }
  );

  return { items, nextCursor, listLoading, listError, loadList };
}
