export type WordDifficulty = 'Neu' | 'Schwer' | 'Mittel' | 'Leicht';

export const WORD_DIFFICULTIES: readonly WordDifficulty[] = [
  'Neu',
  'Schwer',
  'Mittel',
  'Leicht',
] as const;

export interface Word {
  id: number;
  german_label: string;
  category: string;
  difficulty: WordDifficulty;
  translation: string;
  cefr_level: string | null;
  created_at: string;
  updated_at: string;
}

export interface WordCreatePayload {
  german_label: string;
  category: string;
  difficulty: WordDifficulty;
  translation: string;
  cefr_level: string | null;
}

export type WordPatchPayload = Partial<WordCreatePayload>;
