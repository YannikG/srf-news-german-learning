import { ref, watch, type Ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  flattenLocationQuery,
  localIsoDate,
  parseIsoDateQueryParam,
} from '@/utils/routerQueryDate';

/** Keeps ``selectedDate`` in sync with ``?d=`` and writes the query when the user picks a date. */
export function useNewsDateRouteSync(): Ref<string> {
  const route = useRoute();
  const router = useRouter();

  const selectedDate = ref(parseIsoDateQueryParam(route.query.d) ?? localIsoDate(new Date()));

  watch(
    () => route.query.d,
    () => {
      const p = parseIsoDateQueryParam(route.query.d);
      if (p) {
        selectedDate.value = p;
      } else if (route.path === '/') {
        selectedDate.value = localIsoDate(new Date());
      }
    }
  );

  watch(selectedDate, (d) => {
    const cur = parseIsoDateQueryParam(route.query.d);
    if (cur === d) return;
    void router.replace({
      path: '/',
      query: { ...flattenLocationQuery(route.query), d },
    });
  });

  return selectedDate;
}
