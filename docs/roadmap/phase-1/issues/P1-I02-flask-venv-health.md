# [P1-I02] Flask App Factory und Health

## Meta

- **Phase:** 1
- **Issue ID:** P1-I02

## Dependencies

- [P1-I01](./P1-I01-monorepo-docker-compose.md)

## Goal

Backend als Flask **Application Factory** mit klarer Paketstruktur; `requirements.txt` im Backend-Verzeichnis; `GET /api/health` liefert JSON mit Status 200 im Container.

## Testable acceptance criteria

- [ ] `python -m venv .venv` und `pip install -r requirements.txt` sind im README beschrieben (Pfad relativ zu Repo-Root angeben).
- [ ] `GET /api/health` antwortet mit `200` und JSON, das mindestens `ok: true` oder gleichwertiges enthält.
- [ ] `pytest` enthält mindestens einen Test, der die Health-Route mit Test-Client aufruft (ohne laufenden Docker nötig).
- [ ] Docker-Image `web` baut und startet; Health von aussen gegen gemappten Port erreichbar (manuell oder Skript).

## Dev lifecycle

1. Factory, Blueprint oder Router-Modul anlegen; Health-Route implementieren.
2. `requirements.txt` und optional `requirements-dev.txt` mit pytest.
3. Dockerfile `web` anpassen.
4. PR verlinkt diese Spec.

## Out of scope

- Geschäftslogik aus späteren Phasen.
- Authentisierung.
