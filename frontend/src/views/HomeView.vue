<script setup lang="ts">
import Button from 'primevue/button';
import { getApiBaseUrl } from '@/config/apiBase';

const apiBase = getApiBaseUrl();
const healthUrl = `${apiBase || ''}/api/health`;
</script>

<template>
  <section class="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6 sm:px-6">
    <h2 class="text-lg font-semibold text-slate-800 sm:text-xl">Start</h2>
    <p class="text-sm text-slate-600 sm:text-base">
      App-Shell bereit. API-Basis:
      <code class="rounded bg-slate-100 px-1 py-0.5 text-xs sm:text-sm">{{
        apiBase || '(gleiche Origin)'
      }}</code>
    </p>
    <p class="text-xs text-slate-500 sm:text-sm">Health-URL (Beispiel): {{ healthUrl }}</p>
    <RouterLink to="/stub" class="inline-flex">
      <Button label="Zum Platzhalter" severity="secondary" outlined />
    </RouterLink>
  </section>
</template>
