# Frontend

Vue 3, Vite, TypeScript, Tailwind 4, PrimeVue mit Aura-Preset aus `@primeuix/themes`. Router-Grundgerüst und mobile-first App-Shell; News-Logik folgt in späteren Issues.

## Voraussetzungen

- Node 20+ (siehe GitHub Actions `quality.yml`)
- Für API-Aufrufe im Dev-Modus: laufendes Backend auf Port 8000 (oder `VITE_DEV_API_PROXY_TARGET` setzen)

## Befehle

```bash
npm ci
npm run dev
npm run build
npm test
```

`npm run build` führt `vue-tsc --noEmit` und `vite build` aus; Ausgabe liegt in `dist/`.

## Konfiguration

Siehe [`.env.example`](.env.example). `VITE_API_BASE_URL` ist optional (leer = gleiche Origin, z. B. im `web`-Container mit eingebettetem `dist`).

## Docker

Das `web`-Image baut den Client im Multi-Stage-Build und legt die Dateien unter `app/static/spa` im Backend-Paket ab. Details: [`../backend/README.md`](../backend/README.md) (Abschnitt Docker).
