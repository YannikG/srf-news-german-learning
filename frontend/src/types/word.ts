export type WordDifficulty = 'Neu' | 'Schwer' | 'Mittel' | 'Leicht';

export const WORD_DIFFICULTIES: readonly WordDifficulty[] = [
  'Neu',
  'Schwer',
  'Mittel',
  'Leicht',
] as const;

/** CEFR codes accepted by the API for dictionary entries. */
export const CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] as const;

export type CefrLevel = (typeof CEFR_LEVELS)[number];

/** Query value for ``GET /api/words?cefr_level=…`` meaning rows without a level. */
export const CEFR_LEVEL_FILTER_NONE = '__none__';

export interface Word {
  id: number;
  german_label: string;
  category: string;
  difficulty: WordDifficulty;
  translation: string;
  cefr_level: CefrLevel | null;
  created_at: string;
  updated_at: string;
}

export interface WordCreatePayload {
  german_label: string;
  category: string;
  difficulty: WordDifficulty;
  translation: string;
  cefr_level: CefrLevel | null;
}

export type WordPatchPayload = Partial<WordCreatePayload>;
