import { buildApiUrl } from '@/api/buildApiUrl';
import type { NewsRefreshSuccess } from '@/types/article';

export type PostNewsRefreshResult =
  | { ok: true; data: NewsRefreshSuccess }
  | { ok: false; status: number; message: string; code?: string };

export async function postNewsRefresh(): Promise<PostNewsRefreshResult> {
  try {
    const res = await fetch(buildApiUrl('/api/news/refresh'), {
      method: 'POST',
      headers: { Accept: 'application/json' },
    });
    let body: NewsRefreshSuccess & { error?: string; code?: string } = {
      fetched: false,
      articles_upserted: 0,
      next_allowed_fetch_at: '',
    };
    try {
      body = { ...body, ...(await res.json()) };
    } catch {
      /* non-JSON error body */
    }
    if (!res.ok) {
      return {
        ok: false,
        status: res.status,
        message: body.error ?? `HTTP ${res.status}`,
        code: typeof body.code === 'string' ? body.code : undefined,
      };
    }
    return {
      ok: true,
      data: {
        fetched: body.fetched,
        articles_upserted: body.articles_upserted,
        next_allowed_fetch_at: body.next_allowed_fetch_at,
      },
    };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Netzwerkfehler';
    return { ok: false, status: 0, message };
  }
}
