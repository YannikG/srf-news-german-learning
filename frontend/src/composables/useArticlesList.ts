import { ref, watch, type Ref } from 'vue';
import { fetchArticlesList } from '@/api/fetchArticles';
import type { ArticleListItem } from '@/types/article';

const PAGE_SIZE = 20;

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

  async function loadList(reset: boolean): Promise<void> {
    const seq = ++listRequestSeq;
    if (reset) {
      nextCursor.value = null;
      items.value = [];
    }
    listLoading.value = true;
    listError.value = null;
    try {
      const res = await fetchArticlesList({
        date: params.selectedDate.value,
        q: params.debouncedSearch.value,
        cursor: reset ? null : nextCursor.value,
        limit: PAGE_SIZE,
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
    [params.selectedDate, params.debouncedSearch],
    () => {
      void loadList(true);
    },
    { immediate: true }
  );

  return { items, nextCursor, listLoading, listError, loadList };
}
