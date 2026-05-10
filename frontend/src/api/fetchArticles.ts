import { buildApiUrl } from '@/api/buildApiUrl';
import type { ArticleDetail, ArticlesListResponse } from '@/types/article';

export type FetchArticlesListResult =
  | { ok: true; data: ArticlesListResponse }
  | { ok: false; status: number; message: string };

export async function fetchArticlesList(params: {
  date?: string;
  q?: string;
  cursor?: string | null;
  limit?: number;
}): Promise<FetchArticlesListResult> {
  const search = new URLSearchParams();
  if (params.date) search.set('date', params.date);
  if (params.q?.trim()) search.set('q', params.q.trim());
  if (params.cursor) search.set('cursor', params.cursor);
  if (params.limit != null) search.set('limit', String(params.limit));
  const qs = search.toString();
  const path = qs ? `/api/articles?${qs}` : '/api/articles';
  try {
    const res = await fetch(buildApiUrl(path), { headers: { Accept: 'application/json' } });
    if (!res.ok) {
      return { ok: false, status: res.status, message: `HTTP ${res.status}` };
    }
    const data = (await res.json()) as ArticlesListResponse;
    return { ok: true, data };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Netzwerkfehler';
    return { ok: false, status: 0, message };
  }
}

export type FetchArticleDetailResult =
  | { ok: true; data: ArticleDetail }
  | { ok: false; status: number; message: string };

export async function fetchArticleDetail(id: number): Promise<FetchArticleDetailResult> {
  try {
    const res = await fetch(buildApiUrl(`/api/articles/${id}`), {
      headers: { Accept: 'application/json' },
    });
    if (res.status === 404) {
      return { ok: false, status: 404, message: 'Artikel nicht gefunden' };
    }
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
    const data = (await res.json()) as ArticleDetail;
    return { ok: true, data };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Netzwerkfehler';
    return { ok: false, status: 0, message };
  }
}
