/** Minimal types for the backend PONS proxy response. */

export interface PonsTranslation {
  source: string;
  target: string;
}

export interface PonsRom {
  headword: string;
  headword_full: string;
  wordclass: string;
  arabs: PonsArab[];
}

export interface PonsArab {
  header: string;
  translations: PonsTranslation[];
}

export interface PonsHitEntry {
  type: 'entry';
  opendict: boolean;
  roms: PonsRom[];
}

export interface PonsHitTranslation {
  type: 'translation';
  source: string;
  target: string;
}

export type PonsHit = PonsHitEntry | PonsHitTranslation;
