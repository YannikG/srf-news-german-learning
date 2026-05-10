# Backend tests (pytest)

This document supports [P7-I01](roadmap/phase-7/issues/P7-I01-pytest-suite.md): how to run the suite, optional coverage, and where edge cases from that spec are covered.

## Commands

From the repository root:

```bash
cd backend
pytest
```

CI runs the same command in [`.github/workflows/quality.yml`](../.github/workflows/quality.yml) (job **Backend (pytest)**) after `pip install -r requirements.txt` and `requirements-dev.txt`.

### Without integration-marked tests

A small number of tests start a threaded `werkzeug` server on `127.0.0.1` (see marker `integration` in `backend/pyproject.toml`). They do not call the public internet. To skip them (for example in a sandbox that disallows binding ports):

```bash
cd backend
pytest -m "not integration"
```

## Coverage (optional, report only)

`pytest-cov` is listed in `backend/requirements-dev.txt`. There is **no** `fail-under` threshold; coverage is for local inspection only unless the team adds a policy later.

Example:

```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

## Edge cases vs. P7-I01 goal list

Spec themes from P7-I01 and where they are exercised in `backend/tests/`:

| Theme | Tests (indicative) |
|-------|-------------------|
| Refresh cooldown and boundaries, skip second upstream call within window | `test_news_refresh.py` (`test_second_refresh_within_cooldown_skips_articles_http`, `test_cooldown_allows_fetch_at_exactly_900_seconds`, corrupt metadata) |
| Duplicate refresh / idempotent upsert | `test_news_refresh.py` (`test_duplicate_external_id_is_idempotent`) |
| SRG OAuth and HTTP edge cases | `test_srg_oauth_client.py`, `test_news_refresh.py` (401, 429 on articles) |
| Ollama idle timer, warning, cancel | `test_ollama_idle.py` |
| SSE stream and cancel reflected in events | `test_events_stream.py` (tests marked `integration` use a live local server) |
| Empty or minimal data paths | `test_lexicon_retrieval.py` (empty lexicon), `test_articles_api.py` (empty list by date), `test_words_api.py` (empty label validation, empty optional fields) |
| Bad or failing LLM / embed HTTP responses | `test_lexicon_retrieval.py` (HTTP 500), `test_ollama_embed_client.py`, `test_srg_oauth_client.py` (malformed token JSON) |
| FTS search, no hits, umlaut-style query | `test_articles_api.py` (`test_search_no_hits_and_umlaut_prefix`) |
| Schema, migrations, vectors, settings API, health, static SPA wiring | `test_db_schema.py`, `test_migration_runner.py`, `test_vectors_repository.py`, `test_settings_api.py`, `test_health.py`, `test_health_sidecar.py`, `test_spa_static.py`, … |

When you add behavior for a new edge case, extend this table (or the PR description) in the same spirit.
