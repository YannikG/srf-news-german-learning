import { computed, onMounted, onUnmounted, ref } from 'vue';
import { fetchHealth } from '@/api/fetchHealth';
import { formatHealthFooterLine } from '@/api/formatHealthFooterLine';
import type { HealthState } from '@/api/healthTypes';

const DEFAULT_POLL_MS = 30_000;

/**
 * Polls ``GET /api/health`` on mount and on an interval; exposes reactive footer text.
 * Lifecycle and scheduling only; HTTP lives in ``fetchHealth``, copy in ``formatHealthFooterLine``.
 */
export function useApiHealthPoll(pollMs: number = DEFAULT_POLL_MS) {
  const health = ref<HealthState>({ kind: 'loading' });
  let pollTimer: ReturnType<typeof setInterval> | undefined;

  async function refresh(): Promise<void> {
    const result = await fetchHealth();
    if (result.success) {
      health.value = { kind: 'ok', payload: result.payload };
    } else {
      health.value = { kind: 'error', message: result.message };
    }
  }

  onMounted(() => {
    void refresh();
    pollTimer = setInterval(() => void refresh(), pollMs);
  });

  onUnmounted(() => {
    if (pollTimer !== undefined) {
      clearInterval(pollTimer);
    }
  });

  const statusLine = computed(() => formatHealthFooterLine(health.value));

  return { health, statusLine, refresh };
}
