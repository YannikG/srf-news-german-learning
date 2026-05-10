import { computed, onUnmounted, ref, watch } from 'vue';
import { postNewsRefresh, type PostNewsRefreshResult } from '@/api/postNewsRefresh';

function parseUtcMs(iso: string): number {
  const t = Date.parse(iso);
  return Number.isNaN(t) ? 0 : t;
}

export function useNewsRefresh() {
  const nextAllowedFetchAtIso = ref<string | null>(null);
  const loading = ref(false);
  const nowTick = ref(Date.now());
  let timer: ReturnType<typeof setInterval> | null = null;

  function startTick() {
    if (timer != null) return;
    timer = setInterval(() => {
      nowTick.value = Date.now();
    }, 1000);
  }

  function stopTick() {
    if (timer != null) {
      clearInterval(timer);
      timer = null;
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

  onUnmounted(stopTick);

  return { nextAllowedFetchAtIso, loading, refresh, cooldownActive };
}
