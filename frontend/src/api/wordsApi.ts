import { buildApiUrl } from '@/api/buildApiUrl';
import type { Word, WordCreatePayload, WordPatchPayload } from '@/types/word';

export type ListWordsResult =
  | { ok: true; data: Word[] }
  | { ok: false; status: number; message: string };

export async function listWords(params: { category?: string }): Promise<ListWordsResult> {
  const search = new URLSearchParams();
  if (params.category?.trim()) {
    search.set('category', params.category.trim());
  }
  const qs = search.toString();
  const path = qs ? `/api/words?${qs}` : '/api/words';
  try {
    const res = await fetch(buildApiUrl(path), { headers: { Accept: 'application/json' } });
    if (!res.ok) {
      let message = `HTTP ${res.status}`;
      try {
        const body = (await res.json()) as { error?: string };
        if (body.error) message = body.error;
      } catch {
        /* ignore */
      }
      return { ok: false, status: res.status, message };
    }
    const data = (await res.json()) as Word[];
    return { ok: true, data };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Netzwerkfehler';
    return { ok: false, status: 0, message };
  }
}

export type WordMutationResult<T> =
  | { ok: true; data: T }
  | { ok: false; status: number; message: string };

async function readErrorMessage(res: Response): Promise<string> {
  let message = `HTTP ${res.status}`;
  try {
    const body = (await res.json()) as { error?: string };
    if (body.error) message = body.error;
  } catch {
    /* ignore */
  }
  return message;
}

export async function createWord(payload: WordCreatePayload): Promise<WordMutationResult<Word>> {
  try {
    const res = await fetch(buildApiUrl('/api/words'), {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      return { ok: false, status: res.status, message: await readErrorMessage(res) };
    }
    const data = (await res.json()) as Word;
    return { ok: true, data };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Netzwerkfehler';
    return { ok: false, status: 0, message };
  }
}

export async function patchWord(
  id: number,
  payload: WordPatchPayload
): Promise<WordMutationResult<Word>> {
  try {
    const res = await fetch(buildApiUrl(`/api/words/${id}`), {
      method: 'PATCH',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      return { ok: false, status: res.status, message: await readErrorMessage(res) };
    }
    const data = (await res.json()) as Word;
    return { ok: true, data };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Netzwerkfehler';
    return { ok: false, status: 0, message };
  }
}

export type DeleteWordResult = { ok: true } | { ok: false; status: number; message: string };

export async function deleteWord(id: number): Promise<DeleteWordResult> {
  try {
    const res = await fetch(buildApiUrl(`/api/words/${id}`), { method: 'DELETE' });
    if (res.status === 204) {
      return { ok: true };
    }
    return { ok: false, status: res.status, message: await readErrorMessage(res) };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Netzwerkfehler';
    return { ok: false, status: 0, message };
  }
}
