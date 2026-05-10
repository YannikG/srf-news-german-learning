/** Short display labels for article ingest slugs (UI copy, Swiss German context). */
const LABELS: Record<string, string> = {
  srgssr: 'SRG SSR',
  newsapi: 'NewsAPI.org',
};

export function newsProviderLabel(slug: string): string {
  const key = slug.trim().toLowerCase();
  return LABELS[key] ?? slug;
}
