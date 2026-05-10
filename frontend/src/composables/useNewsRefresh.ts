import { computed, ref, watch } from 'vue';
import { postNewsRefresh, type PostNewsRefreshResult } from '@/api/postNewsRefresh';

function parseUtcMs(iso: string): number {
  const t = Date.parse(iso);
  return Number.isNaN(t) ? 0 : t;
}

/** Cooldown is shared across the SPA session so it survives route changes. */
const nextAllowedFetchAtIso = ref<string | null>(null);
const nowTick = ref(Date.now());
let tickTimer: ReturnType<typeof setInterval> | null = null;

function startTick(): void {
  if (tickTimer != null) return;
  tickTimer = setInterval(() => {
    nowTick.value = Date.now();
  }, 1000);
}

function stopTick(): void {
  if (tickTimer != null) {
    clearInterval(tickTimer);
    tickTimer = null;
  }
}

const cooldownActive = computed(() => {
  const iso = nextAllowedFetchAtIso.value;
  if (!iso) return false;
  return parseUtcMs(iso) > nowTick.value;
});

watch(cooldownActive, (on) => {
  if (on) startTick();
  else stopTick();
});

export function useNewsRefresh() {
  const loading = ref(false);

  async function refresh(): Promise<PostNewsRefreshResult> {
    loading.value = true;
    try {
      const r = await postNewsRefresh();
      if (r.ok) {
        nextAllowedFetchAtIso.value = r.data.next_allowed_fetch_at;
      }
      return r;
    } finally {
      loading.value = false;
    }
  }

  return { nextAllowedFetchAtIso, loading, refresh, cooldownActive };
}
