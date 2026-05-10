import { onUnmounted, ref, watch, type Ref } from 'vue';

/** Debounced copy of ``source``; clears the timer on unmount. */
export function useDebouncedRef(source: Ref<string>, delayMs: number): Ref<string> {
  const debounced = ref(source.value);
  let timer: ReturnType<typeof setTimeout> | null = null;

  watch(source, (v) => {
    if (timer != null) clearTimeout(timer);
    timer = setTimeout(() => {
      debounced.value = v;
      timer = null;
    }, delayMs);
  });

  onUnmounted(() => {
    if (timer != null) {
      clearTimeout(timer);
      timer = null;
    }
  });

  return debounced;
}
