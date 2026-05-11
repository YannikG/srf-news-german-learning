import { onMounted, ref } from 'vue';
import { fetchHealth } from '@/api/fetchHealth';
import { lookupPons, type PonsLookupResult } from '@/api/ponsApi';
import type { PonsHit } from '@/types/pons';

export interface PonsWordState {
  loading: boolean;
  hits: PonsHit[] | null;
  error: string | null;
}

/**
 * Manages on-demand PONS lookups for dictionary rows. Checks ``GET /api/health``
 * once on mount to determine whether the PONS feature is available. Per-word
 * results are cached in a session-level ``Map`` so repeated clicks don't
 * fire duplicate requests.
 */
export function usePonsLookup() {
  const ponsAvailable = ref(false);
  const wordStates = ref(new Map<string, PonsWordState>());

  onMounted(async () => {
    const result = await fetchHealth(5_000);
    if (result.success && result.payload.pons?.available) {
      ponsAvailable.value = true;
    }
  });

  function getState(germanLabel: string): PonsWordState | undefined {
    return wordStates.value.get(germanLabel);
  }

  async function lookup(germanLabel: string, dictionary?: string): Promise<PonsLookupResult> {
    const existing = wordStates.value.get(germanLabel);
    if (existing?.hits !== null && existing?.error === null && existing?.loading === false) {
      return { ok: true, hits: existing.hits };
    }

    const state: PonsWordState = { loading: true, hits: null, error: null };
    wordStates.value.set(germanLabel, state);
    triggerReactivity();

    const result = await lookupPons(germanLabel, dictionary);

    if (result.ok) {
      wordStates.value.set(germanLabel, { loading: false, hits: result.hits, error: null });
    } else {
      wordStates.value.set(germanLabel, { loading: false, hits: null, error: result.message });
    }
    triggerReactivity();
    return result;
  }

  function triggerReactivity() {
    wordStates.value = new Map(wordStates.value);
  }

  return {
    ponsAvailable,
    wordStates,
    getState,
    lookup,
  };
}
