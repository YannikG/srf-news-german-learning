import { describe, expect, it } from 'vitest';
import { flattenLocationQuery, parseIsoDateQueryParam } from './routerQueryDate';

describe('routerQueryDate', () => {
  it('parseIsoDateQueryParam accepts first array entry', () => {
    expect(parseIsoDateQueryParam(['2026-05-10', 'ignored'])).toBe('2026-05-10');
  });

  it('flattenLocationQuery keeps non-empty strings', () => {
    expect(
      flattenLocationQuery({
        d: ['2026-01-01', 'x'],
        empty: '',
        n: null,
        ok: 'yes',
      } as Record<string, string | null | (string | null)[]>)
    ).toEqual({ d: '2026-01-01', ok: 'yes' });
  });
});
