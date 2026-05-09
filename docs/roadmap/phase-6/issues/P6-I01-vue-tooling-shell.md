# [P6-I01] Vue Tooling und App Shell

## Meta

- **Phase:** 6
- **Issue ID:** P6-I01

## Dependencies

- [P1-I02](../../phase-1/issues/P1-I02-flask-venv-health.md)

## Goal

Vue 3, Vite, TypeScript, Tailwind 4, PrimeVue **Aura**; Router-Grundgerüst; API-Base-URL aus Konfig; Layout mit Mobile-First; Build-Artefakt in `web`-Image integrierbar.

## Testable acceptance criteria

- [ ] `npm run build` (oder `pnpm build`) exit 0 ohne Fehler.
- [ ] Mindestens eine Vitest-Spec läuft (Smoke: mount App Shell).
- [ ] README-Abschnitt Frontend: install, dev, build.

## Dev lifecycle

1. Projekt scaffold; Theme Aura.
2. Vitest konfigurieren.
3. PR.

## Out of scope

- Vollständige News-Logik (P6-I02).
