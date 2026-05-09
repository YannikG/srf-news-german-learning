# Zusammenarbeit: Spec vs. Tracker

## Single Source of Truth (SSOT)

| Ort | Rolle |
|-----|--------|
| `docs/roadmap/README.md` | Hub, kritischer Pfad, Finalisierungshinweis |
| `docs/roadmap/phase-N/issues/*.md` | Kanonische Spec: Ziel, Abhängigkeiten, testbare Akzeptanzkriterien, Out-of-Scope, Dev-Lifecycle |
| Tracker-Issue (GitHub o. ä.) | Status, Board, kurze Notizen; **Body enthält Permalink** auf die Spec-Datei im Repo |

## Regeln

- Diskussion, die das Verhalten ändert, endet in der **kanonischen Spec** (oder explizit „Out of scope“ dort).
- Spec-Dateien enthalten **keine** Tracker-Befehle, keine GitHub-UI-Anleitungen, keine Permalink-Meta über den Tracker.

## Wann Spec und Code zusammen ändern

- Nur wenn das in der Phase oder im Issue **explizit** vorgesehen ist (z. B. Research-Issue schreibt API-Felder fest und implementiert sie im gleichen PR).
