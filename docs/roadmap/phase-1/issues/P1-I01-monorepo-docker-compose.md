# [P1-I01] Monorepo-Layout und Docker Compose

## Meta

- **Phase:** 1
- **Issue ID:** P1-I01

## Dependencies

- none

## Goal

Ein klares Verzeichnislayout (mindestens Backend-Pfad und Frontend-Pfad oder Platzhalter) und eine funktionierende Compose-Datei im **Projektroot**, mit den Services `web`, `ollama` und Sidecar-Stubs oder fertigen Images, sodass der Stack einheitlich startbar ist.

## Testable acceptance criteria

- [ ] Datei `docker-compose.yml` oder `compose.yaml` liegt im Repository-Root; `docker compose config` exit code 0.
- [ ] Services `web`, `ollama` und ein Sidecar-Service sind deklariert; Volumes für `/data/app.db` und `/data/vectors.db` vorgesehen (Dateien dürfen in P1-I02 noch leer sein).
- [ ] Dokumentierter Befehl `docker compose up` und `docker compose up -d` im README oder in Phase-1 README verweist auf denselben Root-Pfad ohne zusätzliches `cd`.

## Dev lifecycle

1. Layout und Compose implementieren.
2. Lokal verifizieren: `docker compose config`, einmal `up` und `down`.
3. PR mit Verweis auf diese Spec.
4. Review gegen diese Datei.
5. Merge; Tracker-Issue schliessen falls verwendet.

## Out of scope

- Vollständiges Produktions-Hardening (Rate Limits, TLS).
- Fertige Ollama-Modelle in CI; Pull kann manuell dokumentiert bleiben.
