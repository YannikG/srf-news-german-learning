import { ref, watch } from 'vue';
import { createWord, deleteWord, listWords, patchWord } from '@/api/wordsApi';
import type { Word, WordCreatePayload, WordPatchPayload } from '@/types/word';

function trimCategoryFilter(value: unknown): string {
  if (value == null || typeof value !== 'string') {
    return '';
  }
  return value.trim();
}

function mergeKnownCategories(existing: string[], words: Word[]): string[] {
  const set = new Set(existing);
  for (const w of words) {
    const c = w.category.trim();
    if (c) set.add(c);
  }
  return [...set].sort((a, b) => a.localeCompare(b, 'de'));
}

/**
 * Loads and mutates dictionary rows; ``categoryFilter`` maps to ``GET /api/words?category=``.
 * After create/update, merges the server row into ``knownCategories`` so the filter list stays
 * complete even when the active filter hides the new or updated row.
 * If the active category filter would exclude the saved row, the filter is cleared so the table
 * can show the new or moved entry without a full page reload.
 */
export function useWordsDictionary() {
  const items = ref<Word[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const categoryFilter = ref('');
  const knownCategories = ref<string[]>([]);
  let loadRequestSeq = 0;

  async function load(): Promise<void> {
    const seq = ++loadRequestSeq;
    loading.value = true;
    error.value = null;
    try {
      const filter = trimCategoryFilter(categoryFilter.value);
      const res = await listWords(filter ? { category: filter } : {});
      if (seq !== loadRequestSeq) {
        return;
      }
      if (!res.ok) {
        error.value = res.message;
        return;
      }
      items.value = res.data;
      knownCategories.value = mergeKnownCategories(knownCategories.value, res.data);
    } finally {
      if (seq === loadRequestSeq) {
        loading.value = false;
      }
    }
  }

  watch(
    categoryFilter,
    () => {
      void load();
    },
    { immediate: true }
  );

  async function create(
    payload: WordCreatePayload
  ): Promise<{ ok: true } | { ok: false; message: string }> {
    const res = await createWord(payload);
    if (!res.ok) {
      return { ok: false, message: res.message };
    }
    knownCategories.value = mergeKnownCategories(knownCategories.value, [res.data]);
    const newCat = res.data.category.trim();
    const filter = trimCategoryFilter(categoryFilter.value);
    if (filter && newCat !== filter) {
      categoryFilter.value = '';
      return { ok: true };
    }
    await load();
    return { ok: true };
  }

  async function update(
    id: number,
    payload: WordPatchPayload
  ): Promise<{ ok: true } | { ok: false; message: string }> {
    const res = await patchWord(id, payload);
    if (!res.ok) {
      return { ok: false, message: res.message };
    }
    knownCategories.value = mergeKnownCategories(knownCategories.value, [res.data]);
    const newCat = res.data.category.trim();
    const filter = trimCategoryFilter(categoryFilter.value);
    if (filter && newCat !== filter) {
      categoryFilter.value = '';
      return { ok: true };
    }
    await load();
    return { ok: true };
  }

  async function remove(id: number): Promise<{ ok: true } | { ok: false; message: string }> {
    const res = await deleteWord(id);
    if (!res.ok) {
      return { ok: false, message: res.message };
    }
    await load();
    return { ok: true };
  }

  return {
    items,
    loading,
    error,
    categoryFilter,
    knownCategories,
    load,
    create,
    update,
    remove,
  };
}
