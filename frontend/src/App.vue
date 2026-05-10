<script setup lang="ts">
import { useRoute } from 'vue-router';

const route = useRoute();
</script>

<template>
  <div class="flex min-h-screen flex-col bg-slate-50">
    <header class="border-b border-slate-200 bg-white shadow-sm">
      <div
        class="mx-auto flex max-w-5xl flex-col gap-3 px-3 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:px-4"
      >
        <div>
          <h1 class="text-base font-bold tracking-tight text-slate-900 sm:text-lg">
            SRF News Lernen
          </h1>
          <p class="text-xs text-slate-500 sm:text-sm">Mobile-first App-Shell</p>
        </div>
        <nav class="flex flex-wrap gap-2 text-sm sm:justify-end" aria-label="Hauptnavigation">
          <RouterLink
            to="/"
            class="rounded-md px-3 py-2 font-medium text-slate-700 hover:bg-slate-100"
            active-class="bg-slate-200 text-slate-900"
          >
            Start
          </RouterLink>
          <RouterLink
            to="/stub"
            class="rounded-md px-3 py-2 font-medium text-slate-700 hover:bg-slate-100"
            active-class="bg-slate-200 text-slate-900"
          >
            Platzhalter
          </RouterLink>
        </nav>
      </div>
    </header>
    <main class="flex-1">
      <RouterView :key="route.fullPath" />
    </main>
    <footer
      class="border-t border-slate-200 bg-white py-3 text-center text-xs text-slate-500 sm:text-sm"
    >
      Phase 6 Shell
    </footer>
  </div>
</template>
