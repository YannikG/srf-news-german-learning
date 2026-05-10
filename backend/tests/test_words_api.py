"""Integration tests for the dictionary REST API."""

from __future__ import annotations

import json

from flask.testing import FlaskClient


def _post_json(client: FlaskClient, payload: dict) -> tuple[dict, int]:
    res = client.post(
        "/api/words",
        data=json.dumps(payload),
        content_type="application/json",
    )
    data = res.get_json(silent=True)
    assert isinstance(data, dict)
    return data, res.status_code


def _patch_json(client: FlaskClient, word_id: int, payload: dict) -> tuple[dict, int]:
    res = client.patch(
        f"/api/words/{word_id}",
        data=json.dumps(payload),
        content_type="application/json",
    )
    data = res.get_json(silent=True)
    assert isinstance(data, dict)
    return data, res.status_code


def test_create_list_get_patch_delete_word(client: FlaskClient) -> None:
    created, code = _post_json(
        client,
        {
            "german_label": "  der Fels  ",
            "category": "Nomen",
            "difficulty": "Mittel",
            "translation": "rock",
        },
    )
    assert code == 201
    assert created["german_label"] == "der Fels"
    assert created["category"] == "Nomen"
    assert created["difficulty"] == "Mittel"
    assert created["translation"] == "rock"
    wid = created["id"]

    listed = client.get("/api/words").get_json()
    assert isinstance(listed, list)
    assert len(listed) == 1
    assert listed[0]["id"] == wid

    one = client.get(f"/api/words/{wid}").get_json()
    assert isinstance(one, dict)
    assert one["german_label"] == "der Fels"

    updated, pcode = _patch_json(
        client,
        wid,
        {"translation": "the rock", "difficulty": "Leicht"},
    )
    assert pcode == 200
    assert updated["translation"] == "the rock"
    assert updated["difficulty"] == "Leicht"

    del_res = client.delete(f"/api/words/{wid}")
    assert del_res.status_code == 204
    assert del_res.data == b""

    missing = client.get(f"/api/words/{wid}")
    assert missing.status_code == 404


def test_list_filter_by_cefr_level(client: FlaskClient) -> None:
    _post_json(
        client,
        {
            "german_label": "low",
            "category": "",
            "difficulty": "Neu",
            "translation": "",
            "cefr_level": "A1",
        },
    )
    _post_json(
        client,
        {
            "german_label": "high",
            "category": "",
            "difficulty": "Neu",
            "translation": "",
            "cefr_level": "C2",
        },
    )
    a1 = client.get("/api/words?cefr_level=A1").get_json()
    assert isinstance(a1, list)
    assert len(a1) == 1
    assert a1[0]["german_label"] == "low"


def test_list_filter_cefr_none_matches_null(client: FlaskClient) -> None:
    _post_json(
        client,
        {"german_label": "n", "category": "", "difficulty": "Neu", "translation": ""},
    )
    _post_json(
        client,
        {
            "german_label": "b",
            "category": "",
            "difficulty": "Neu",
            "translation": "",
            "cefr_level": "B1",
        },
    )
    null_only = client.get("/api/words?cefr_level=__none__").get_json()
    assert isinstance(null_only, list)
    assert len(null_only) == 1
    assert null_only[0]["german_label"] == "n"
    assert null_only[0]["cefr_level"] is None


def test_list_filter_category_and_cefr_level(client: FlaskClient) -> None:
    _post_json(
        client,
        {
            "german_label": "x",
            "category": "geo",
            "difficulty": "Neu",
            "translation": "",
            "cefr_level": "A2",
        },
    )
    _post_json(
        client,
        {
            "german_label": "y",
            "category": "geo",
            "difficulty": "Neu",
            "translation": "",
            "cefr_level": "B1",
        },
    )
    _post_json(
        client,
        {
            "german_label": "z",
            "category": "math",
            "difficulty": "Neu",
            "translation": "",
            "cefr_level": "A2",
        },
    )
    rows = client.get("/api/words?category=geo&cefr_level=A2").get_json()
    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0]["german_label"] == "x"


def test_invalid_cefr_level_filter_returns_400(client: FlaskClient) -> None:
    res = client.get("/api/words?cefr_level=B3")
    assert res.status_code == 400


def test_invalid_cefr_level_on_create(client: FlaskClient) -> None:
    data, code = _post_json(
        client,
        {
            "german_label": "x",
            "category": "",
            "difficulty": "Neu",
            "translation": "",
            "cefr_level": "B3",
        },
    )
    assert code == 400
    assert "error" in data


def test_list_filter_by_category(client: FlaskClient) -> None:
    _post_json(
        client,
        {"german_label": "A", "category": "alpha", "difficulty": "Neu", "translation": ""},
    )
    _post_json(
        client,
        {"german_label": "B", "category": "beta", "difficulty": "Neu", "translation": "b"},
    )
    alpha = client.get("/api/words?category=alpha").get_json()
    assert isinstance(alpha, list)
    assert len(alpha) == 1
    assert alpha[0]["german_label"] == "A"


def test_invalid_difficulty_on_create(client: FlaskClient) -> None:
    data, code = _post_json(
        client,
        {
            "german_label": "x",
            "category": "",
            "difficulty": "Unmöglich",
            "translation": "",
        },
    )
    assert code == 400
    assert "error" in data


def test_invalid_cefr_level_on_patch(client: FlaskClient) -> None:
    created, _ = _post_json(
        client,
        {"german_label": "x", "category": "", "difficulty": "Neu", "translation": ""},
    )
    wid = created["id"]
    data, code = _patch_json(client, wid, {"cefr_level": "X9"})
    assert code == 400
    assert "error" in data


def test_invalid_difficulty_on_patch(client: FlaskClient) -> None:
    created, _ = _post_json(
        client,
        {"german_label": "x", "category": "", "difficulty": "Neu", "translation": ""},
    )
    wid = created["id"]
    data, code = _patch_json(client, wid, {"difficulty": "Hard"})
    assert code == 400
    assert "error" in data


def test_empty_german_label_rejected_on_create(client: FlaskClient) -> None:
    data, code = _post_json(
        client,
        {"german_label": "   ", "category": "x", "difficulty": "Neu", "translation": "y"},
    )
    assert code == 400
    assert "error" in data


def test_empty_german_label_rejected_on_patch(client: FlaskClient) -> None:
    created, _ = _post_json(
        client,
        {"german_label": "ok", "category": "", "difficulty": "Neu", "translation": ""},
    )
    wid = created["id"]
    data, code = _patch_json(client, wid, {"german_label": ""})
    assert code == 400
    assert "error" in data


def test_empty_category_and_translation_allowed(client: FlaskClient) -> None:
    data, code = _post_json(
        client,
        {"german_label": "Haus", "category": "", "difficulty": "Schwer", "translation": ""},
    )
    assert code == 201
    assert data["category"] == ""
    assert data["translation"] == ""


def test_delete_missing_returns_404(client: FlaskClient) -> None:
    res = client.delete("/api/words/999")
    assert res.status_code == 404
    body = res.get_json()
    assert isinstance(body, dict)
    assert "error" in body
