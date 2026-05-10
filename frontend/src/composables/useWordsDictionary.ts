import { ref, watch } from 'vue';
import { createWord, deleteWord, listWords, patchWord } from '@/api/wordsApi';
import type { Word, WordCreatePayload, WordPatchPayload } from '@/types/word';
import { CEFR_LEVEL_FILTER_NONE } from '@/types/word';

function trimCategoryFilter(value: unknown): string {
  if (value == null || typeof value !== 'string') {
    return '';
  }
  return value.trim();
}

function trimCefrFilter(value: unknown): string {
  if (value == null || typeof value !== 'string') {
    return '';
  }
  return value.trim();
}

function rowMatchesCefrFilter(row: Word, filter: string): boolean {
  const f = trimCefrFilter(filter);
  if (!f) {
    return true;
  }
  if (f === CEFR_LEVEL_FILTER_NONE) {
    return row.cefr_level == null;
  }
  return row.cefr_level === f;
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
 * Loads and mutates dictionary rows. ``categoryFilter`` maps to ``GET /api/words?category=``,
 * ``cefrLevelFilter`` to ``GET /api/words?cefr_level=`` (use ``CEFR_LEVEL_FILTER_NONE`` for rows
 * without a level). After create/update, filters that would hide the saved row are cleared so the
 * table can show the entry without a full reload.
 */
export function useWordsDictionary() {
  const items = ref<Word[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const categoryFilter = ref('');
  const cefrLevelFilter = ref('');
  const knownCategories = ref<string[]>([]);
  let loadRequestSeq = 0;

  async function load(): Promise<void> {
    const seq = ++loadRequestSeq;
    loading.value = true;
    error.value = null;
    try {
      const cat = trimCategoryFilter(categoryFilter.value);
      const cefr = trimCefrFilter(cefrLevelFilter.value);
      const res = await listWords({
        ...(cat ? { category: cat } : {}),
        ...(cefr ? { cefr_level: cefr } : {}),
      });
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
    [categoryFilter, cefrLevelFilter],
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
    const catFilter = trimCategoryFilter(categoryFilter.value);
    const cefrF = trimCefrFilter(cefrLevelFilter.value);
    let cleared = false;
    if (catFilter && newCat !== catFilter) {
      categoryFilter.value = '';
      cleared = true;
    }
    if (cefrF && !rowMatchesCefrFilter(res.data, cefrF)) {
      cefrLevelFilter.value = '';
      cleared = true;
    }
    if (cleared) {
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
    const catFilter = trimCategoryFilter(categoryFilter.value);
    const cefrF = trimCefrFilter(cefrLevelFilter.value);
    let cleared = false;
    if (catFilter && newCat !== catFilter) {
      categoryFilter.value = '';
      cleared = true;
    }
    if (cefrF && !rowMatchesCefrFilter(res.data, cefrF)) {
      cefrLevelFilter.value = '';
      cleared = true;
    }
    if (cleared) {
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
    cefrLevelFilter,
    knownCategories,
    load,
    create,
    update,
    remove,
  };
}
