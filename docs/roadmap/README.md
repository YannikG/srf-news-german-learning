# Roadmap (Hub)

**Status:** Phase 1–7 finalisiert (Review 2026-05-09); **Phase 8** als reine Spec-Dokumentation ergänzt (2026-05-10). Änderungen an Phasen oder Issue-Specs nur bewusst und mit Anpassung der Abhängigkeiten.

| Dokument | Zweck |
|----------|--------|
| [overview.md](./overview.md) | Master-Reihenfolge aller Phasen und Phasen-Abhängigkeiten |
| [phase-1/README.md](./phase-1/README.md) … [phase-8](./phase-8/README.md) | Pro Phase: Endzustand, DoD, Issue-Liste, Issue-Graph |
| [../agents-docs/collaboration.md](../agents-docs/collaboration.md) | Wo die Spec gilt vs. Tracker |

## Kurz: kritischer Pfad

1. **Phase 1** zuerst (Compose + Flask + Health + Quality Gates: Ruff, Prettier, GitHub Actions auf PR und Push).  
2. **Phase 2** danach (`app.db`, APIs ohne SRG/Ollama).  
3. **Phase 3** und **Phase 4** können parallel arbeiten, sobald Phase 1 steht (unterschiedliche Artefakte).  
4. **Phase 5** erst, wenn **Phase 2 und Phase 4** die benötigten Schnittstellen haben (DB + Ollama-Lifecycle/SSE-Basis).  
5. **Phase 6** baut auf den APIs von 3–5 auf; Shell (**P6-I01**) früh nach Phase 1 möglich.  
6. **Phase 7** konsolidiert Tests, Lint und README nach dominiert fertiger Feature-Basis.  
7. **Phase 8** erweitert News-Ingest (Multi-Provider, NewsAPI.org), UI-Herkunft, LLM-Übersetzung und abschliessenden Projekt-Rename; Details [phase-8/README.md](./phase-8/README.md). Die zugehörigen Specs können in eigenen PRs ohne Anwendungscode gemergt werden.

## Tracker

GitHub-Issues (oder anderes Tool) mit **Permalink** zur jeweiligen Datei unter `docs/roadmap/phase-N/issues/` im Issue-Body; Spec-Dateien enthalten keine Tracker-Befehle.
