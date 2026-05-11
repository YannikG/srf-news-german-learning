/** CEFR levels accepted by ``PATCH /api/settings`` (``default_cefr``). */
export const CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] as const;
export type CefrLevel = (typeof CEFR_LEVELS)[number];

/** Translation targets accepted by the backend. */
export const TRANSLATION_LANGUAGES = ['en', 'uk'] as const;
export type TranslationLanguage = (typeof TRANSLATION_LANGUAGES)[number];

/** Public row returned by ``GET`` / ``PATCH`` ``/api/settings``. */
export type AppSettings = {
  default_cefr: CefrLevel;
  translation_language: TranslationLanguage;
  retrieval_top_k: number | null;
  retrieval_context_max_chars: number | null;
  /** Read-only: configured ingest slug (e.g. srgssr); not persisted in DB. */
  active_ingest_provider: string;
};

/** Partial body for ``PATCH /api/settings`` from the settings screen. */
export type PatchAppSettings = Partial<Pick<AppSettings, 'default_cefr' | 'translation_language'>>;
