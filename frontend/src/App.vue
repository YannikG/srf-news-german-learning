<script setup lang="ts">
import ConfirmDialog from 'primevue/confirmdialog';
import Toast from 'primevue/toast';
import { useRoute } from 'vue-router';
import { useApiHealthPoll } from '@/composables/useApiHealthPoll';

const route = useRoute();
const { health, statusLine } = useApiHealthPoll();
</script>

<template>
  <Toast position="top-center" />
  <ConfirmDialog />
  <div class="flex min-h-screen flex-col bg-slate-50">
    <header class="border-b border-slate-200 bg-white shadow-sm">
      <div
        class="mx-auto flex max-w-5xl flex-col gap-3 px-3 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:px-4"
      >
        <div>
          <h1 class="text-base font-bold tracking-tight text-slate-900 sm:text-lg">
            SRF News Lernen
          </h1>
          <p class="text-xs text-slate-500 sm:text-sm">News und Lernmodus</p>
        </div>
        <nav class="flex flex-wrap gap-2 text-sm sm:justify-end" aria-label="Hauptnavigation">
          <RouterLink
            to="/"
            class="rounded-md px-3 py-2 font-medium text-slate-700 hover:bg-slate-100"
            active-class="bg-slate-200 text-slate-900"
          >
            News
          </RouterLink>
          <RouterLink
            to="/woerterbuch"
            class="rounded-md px-3 py-2 font-medium text-slate-700 hover:bg-slate-100"
            active-class="bg-slate-200 text-slate-900"
          >
            Wörterbuch
          </RouterLink>
        </nav>
      </div>
    </header>
    <main class="flex-1">
      <RouterView :key="route.fullPath" />
    </main>
    <footer class="border-t border-slate-200 bg-white py-3 text-slate-600">
      <div
        class="mx-auto flex max-w-5xl flex-col gap-1 px-3 text-center text-xs sm:px-4 sm:text-sm"
      >
        <p class="font-medium text-slate-800">SRF News Lernen</p>
        <p
          class="break-words text-slate-500"
          role="status"
          :aria-busy="health.kind === 'loading'"
          :data-state="health.kind"
        >
          {{ statusLine }}
        </p>
      </div>
    </footer>
  </div>
</template>
