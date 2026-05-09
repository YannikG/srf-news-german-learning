# [P3-I01] SRG OAuth Client Credentials

## Meta

- **Phase:** 3
- **Issue ID:** P3-I01

## Dependencies

- [P1-I02](../../phase-1/issues/P1-I02-flask-venv-health.md)

## Goal

Modul für OAuth2 **Client Credentials** gegen `https://api.srgssr.ch/oauth/v1/accesstoken` mit `grant_type=client_credentials`, Basic-Auth aus Consumer Key/Secret, Token-Cache mit Ablauf (Refresh ca. 60 s vor Ablauf empfohlen).

## Testable acceptance criteria

- [ ] Konfiguration über Umgebungsvariablen (z. B. `SRGSSR_CONSUMER_KEY`, `SRGSSR_CONSUMER_SECRET`) via pydantic-settings oder gleichwertig.
- [ ] `pytest` mit `httpx.MockTransport` oder `respx`: erfolgreicher Token, 401, 429; kein echter Netzwerkpflicht für Standardmarker.
- [ ] User-Agent setzen (Projektname, kein fremder Default-String aus Drittprojekten).

## Dev lifecycle

1. Client implementieren; keine URLs ausser `api.srgssr.ch` für diesen Schritt.
2. Tests.
3. PR.

## Out of scope

- Konkrete Artikel-Endpunkte (P3-I03 nutzt dieses Modul).
