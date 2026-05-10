<script setup lang="ts">
import Button from 'primevue/button';
</script>

<template>
  <section class="mx-auto max-w-3xl px-4 py-6 sm:px-6">
    <h2 class="text-lg font-semibold text-slate-800 sm:text-xl">Platzhalter-Route</h2>
    <p class="mt-2 text-sm text-slate-600 sm:text-base">Router-Grundgerüst, ohne News-Logik.</p>
    <RouterLink to="/" class="mt-4 inline-flex">
      <Button label="Zurück" />
    </RouterLink>
  </section>
</template>
