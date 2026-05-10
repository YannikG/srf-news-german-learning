import type { PostNewsRefreshResult } from '@/api/postNewsRefresh';

type ToastPayload = {
  severity: 'success' | 'info' | 'warn' | 'error' | 'secondary' | 'contrast';
  summary: string;
  detail: string;
  life?: number;
};

type ToastAdd = (message: ToastPayload) => void;

export type PostNewsRefreshNotifyOutcome = 'reload_list' | 'done';

/** Maps refresh API outcome to PrimeVue toast messages (German UI copy). */
export function notifyPostNewsRefresh(
  add: ToastAdd,
  result: PostNewsRefreshResult,
  cooldownLabel: string
): PostNewsRefreshNotifyOutcome {
  if (!result.ok) {
    if (result.code === 'oauth_not_configured') {
      add({
        severity: 'warn',
        summary: 'SRG nicht konfiguriert',
        detail: result.message,
        life: 12000,
      });
      return 'done';
    }
    const summary =
      result.status === 429 || result.code === 'upstream_rate_limited'
        ? 'SRG Rate-Limit (429)'
        : 'Refresh fehlgeschlagen';
    add({
      severity: result.status === 429 ? 'warn' : 'error',
      summary,
      detail: result.message,
      life: 8000,
    });
    return 'done';
  }
  if (result.data.fetched) {
    add({
      severity: 'success',
      summary: 'News aktualisiert',
      detail: `${result.data.articles_upserted} Artikel verarbeitet.`,
      life: 4000,
    });
    return 'reload_list';
  }
  add({
    severity: 'info',
    summary: 'Cooldown',
    detail: `Nächster Abruf ab ${cooldownLabel || result.data.next_allowed_fetch_at}.`,
    life: 5000,
  });
  return 'done';
}
