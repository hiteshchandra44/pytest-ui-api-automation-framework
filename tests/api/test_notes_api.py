"""
tests/api/test_notes_api.py

This file contains API tests for Notes endpoints of the Notes API.
Docs: Notes API Swagger (see project config for base URL).
"""

import time
import uuid

import pytest

from utilities.config_reader import read_config
from utilities.logger import get_logger


logger = get_logger(__name__)


def _auth_headers(token: str):
    """Build x-auth-token header from a token string."""
    return {"x-auth-token": token}


def _token_from_fresh_user(api_client):
    """Register a unique user, log in, return token (token / access_token / data.token)."""
    password = read_config("api", "default_password").strip()
    email = f"notes_api_{uuid.uuid4().hex}@example.com"
    api_client.post(
        "users/register",
        payload={"name": "Notes API User", "email": email, "password": password},
    )
    login_resp = api_client.post("users/login", payload={"email": email, "password": password})
    body = login_resp.json() or {}
    token = (
        body.get("token")
        or body.get("access_token")
        or (body.get("data") or {}).get("token")
        or ""
    )
    if not token:
        pytest.skip("Login response did not include a token (token, access_token, or data.token).")
    return token


def _create_note(api_client, token: str, title: str, description: str = "Test description", category: str = "Home"):
    """Create a note and return the response."""
    if len(title) < 4:
        title = title + "_note"
    if len(description) < 4:
        description = description + "_description"
    return api_client.post(
        "notes",
        payload={"title": title, "description": description, "category": category},
        headers=_auth_headers(token),
    )


def _note_id(resp):
    """Extract note id from a create/get note response."""
    try:
        body = resp.json()
        nid = (body.get("data") or {}).get("id")
        if nid:
            return nid
        nid = body.get("id")
        if nid:
            return nid
    except Exception:
        pass
    return ""


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.positive
def test_create_note_success(api_client):
    """POST /notes with title+desc returns 200."""
    logger.info("Running test: test_create_note_success")
    auth_token = _token_from_fresh_user(api_client)
    resp = _create_note(api_client, auth_token, f"T{int(time.time())}", "Desc")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    assert _note_id(resp), "Create note response should include note id."


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_create_note_missing_title(api_client, auth_token):
    """POST /notes without title returns 400."""
    logger.info("Running test: test_create_note_missing_title")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    resp = api_client.post("notes", payload={"description": "Desc"}, headers=_auth_headers(auth_token))
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_create_note_missing_description(api_client):
    """POST /notes without description returns 400."""
    logger.info("Running test: test_create_note_missing_description")
    auth_token = _token_from_fresh_user(api_client)
    resp = api_client.post("notes", payload={"title": "Title"}, headers=_auth_headers(auth_token))
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_create_note_no_auth(api_client):
    """POST /notes without token returns 401."""
    logger.info("Running test: test_create_note_no_auth")
    resp = api_client.post("notes", payload={"title": "Title", "description": "Desc"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_get_all_notes(api_client):
    """GET /notes returns 200 and a list."""
    logger.info("Running test: test_get_all_notes")
    auth_token = _token_from_fresh_user(api_client)
    created = _create_note(api_client, auth_token, f"AllNotes_{uuid.uuid4().hex}", "Desc")
    if created.status_code != 200:
        pytest.skip(f"Note creation failed with status {created.status_code}: {created.text}")
    resp = api_client.get("notes", headers=_auth_headers(auth_token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    assert isinstance(resp.json(), (list, dict)), "Expected notes response to be list/dict JSON."


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_get_all_notes_no_auth(api_client):
    """GET /notes without token returns 401."""
    logger.info("Running test: test_get_all_notes_no_auth")
    resp = api_client.get("notes")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_get_note_by_id(api_client):
    """GET /notes/{id} returns 200."""
    logger.info("Running test: test_get_note_by_id")
    auth_token = _token_from_fresh_user(api_client)
    created = _create_note(api_client, auth_token, f"GetById_{uuid.uuid4().hex}", "Desc")
    if created.status_code != 200:
        pytest.skip(f"Note creation failed with status {created.status_code}: {created.text}")
    note_id = _note_id(created)
    if not note_id:
        pytest.skip("Note creation returned no id in response JSON.")
    resp = api_client.get(f"notes/{note_id}", headers=_auth_headers(auth_token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_get_note_invalid_id(api_client, auth_token):
    """GET /notes/invalidid returns 400 or 404."""
    logger.info("Running test: test_get_note_invalid_id")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    resp = api_client.get("notes/invalidid", headers=_auth_headers(auth_token))
    assert resp.status_code in (400, 404), f"Expected 400/404, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_get_note_no_auth(api_client, auth_token):
    """GET /notes/{id} without token returns 401."""
    logger.info("Running test: test_get_note_no_auth")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    created = _create_note(api_client, auth_token, "NoAuth", "Desc")
    resp = api_client.get(f"notes/{_note_id(created)}")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_update_note_success(api_client, auth_token):
    """PUT /notes/{id} with new title returns 200."""
    logger.info("Running test: test_update_note_success")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    created = _create_note(api_client, auth_token, "Old", "Desc")
    note_id = _note_id(created)
    resp = api_client.put(
        f"notes/{note_id}",
        payload={"title": "New_title", "description": "Desc_updated", "category": "Home", "completed": False},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_update_note_missing_title(api_client):
    """PUT /notes/{id} without title returns 400."""
    logger.info("Running test: test_update_note_missing_title")
    auth_token = _token_from_fresh_user(api_client)
    created = _create_note(api_client, auth_token, f"UpdateMissing{uuid.uuid4().hex}", "D")
    if created.status_code != 200:
        pytest.skip(f"Note creation failed with status {created.status_code}: {created.text}")
    note_id = _note_id(created)
    if not note_id:
        pytest.skip("Note creation returned no id in response JSON.")
    resp = api_client.put(f"notes/{note_id}", payload={"description": "OnlyDesc"}, headers=_auth_headers(auth_token))
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_update_note_no_auth(api_client, auth_token):
    """PUT /notes/{id} without token returns 401."""
    logger.info("Running test: test_update_note_no_auth")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    created = _create_note(api_client, auth_token, "T", "D")
    resp = api_client.put(f"notes/{_note_id(created)}", payload={"title": "X", "description": "D"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_update_note_invalid_id(api_client, auth_token):
    """PUT /notes/{id} with non-existent id returns 404."""
    logger.info("Running test: test_update_note_invalid_id")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    resp = api_client.put(
        "notes/000000000000000000000000",
        payload={"title": "Valid title", "description": "Valid description", "category": "Home"},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code in (400, 404), f"Expected 400 or 404, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_delete_note_success(api_client, auth_token):
    """DELETE /notes/{id} returns 200."""
    logger.info("Running test: test_delete_note_success")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    created = _create_note(api_client, auth_token, "Del", "D")
    resp = api_client.delete(f"notes/{_note_id(created)}", headers=_auth_headers(auth_token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_delete_note_no_auth(api_client, auth_token):
    """DELETE /notes/{id} without token returns 401."""
    logger.info("Running test: test_delete_note_no_auth")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    created = _create_note(api_client, auth_token, "DelNA", "D")
    resp = api_client.delete(f"notes/{_note_id(created)}")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_delete_note_invalid_id(api_client, auth_token):
    """DELETE /notes/badid returns 400 or 404."""
    logger.info("Running test: test_delete_note_invalid_id")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    resp = api_client.delete("notes/badid", headers=_auth_headers(auth_token))
    assert resp.status_code in (400, 404), f"Expected 400/404, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_create_multiple_notes(api_client):
    """Create 3 notes and verify list count increases."""
    logger.info("Running test: test_create_multiple_notes")

    # Create fresh user to avoid count interference from other tests
    email = f"api_user_{int(time.time() * 1000)}@example.com"
    password = read_config("api", "default_password").strip()
    api_client.post(
        "users/register",
        payload={"name": "Multi Note User", "email": email, "password": password},
    )
    login_body = api_client.post(
        "users/login",
        payload={"email": email, "password": password},
    ).json()
    token = (login_body.get("data") or {}).get("token") or login_body.get("token") or ""

    before_resp = api_client.get("notes", headers=_auth_headers(token))
    before_json = before_resp.json()
    before_list = before_json if isinstance(before_json, list) else (before_json.get("data") or [])
    for i in range(3):
        _create_note(api_client, token, f"Multi{i}_{int(time.time())}", "Test description")

    after_resp = api_client.get("notes", headers=_auth_headers(token))
    after_json = after_resp.json()
    after_list = after_json if isinstance(after_json, list) else (after_json.get("data") or [])

    assert len(after_list) >= len(before_list) + 3, "Notes count should increase after creating 3 notes."


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_note_category_home(api_client, auth_token):
    """Create note with category=Home."""
    logger.info("Running test: test_note_category_home")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    resp = _create_note(api_client, auth_token, "Home", "D", category="Home")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_note_category_work(api_client, auth_token):
    """Create note with category=Work."""
    logger.info("Running test: test_note_category_work")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    resp = _create_note(api_client, auth_token, "Work", "D", category="Work")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_note_category_personal(api_client, auth_token):
    """Create note with category=Personal."""
    logger.info("Running test: test_note_category_personal")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    resp = _create_note(api_client, auth_token, "Personal", "D", category="Personal")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_toggle_note_complete(api_client):
    """PATCH /notes/{id} to completed=true returns 200."""
    logger.info("Running test: test_toggle_note_complete")
    auth_token = _token_from_fresh_user(api_client)
    title = f"Toggle_{uuid.uuid4().hex}"
    created = _create_note(api_client, auth_token, title, "D")
    if created.status_code != 200:
        pytest.skip(f"Note creation failed with status {created.status_code}: {created.text}")
    note_id = _note_id(created)
    if not note_id:
        pytest.skip("Note creation returned no id in response JSON.")
    resp = api_client.patch(f"notes/{note_id}", payload={"completed": True}, headers=_auth_headers(auth_token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_toggle_note_incomplete(api_client):
    """PATCH /notes/{id} to completed=false returns 200."""
    logger.info("Running test: test_toggle_note_incomplete")
    auth_token = _token_from_fresh_user(api_client)
    title = f"ToggleIncomplete{uuid.uuid4().hex}"
    created = _create_note(api_client, auth_token, title, "D")
    if created.status_code != 200:
        pytest.skip(f"Note creation failed with status {created.status_code}: {created.text}")
    note_id = _note_id(created)
    if not note_id:
        pytest.skip("Note creation returned no id in response JSON.")
    api_client.patch(
        f"notes/{note_id}",
        payload={"completed": True},
        headers=_auth_headers(auth_token),
    )
    resp = api_client.patch(
        f"notes/{note_id}",
        payload={"completed": False},
        headers=_auth_headers(auth_token),
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_note_title_max_length(api_client, auth_token):
    """Send a note with a very long title and verify server handles it gracefully."""
    logger.info("Running test: test_note_title_max_length")
    long_title = "A" * 500  # 500 character title
    payload = {"title": long_title, "description": "Test description", "category": "Home"}
    headers = {"x-auth-token": auth_token}
    resp = api_client.post("/notes", payload=payload, headers=headers)
    # Accept either 200 (allowed) or 400 (rejected) — both are valid server behaviors
    assert resp.status_code in [200, 400], f"Unexpected status: {resp.status_code}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_update_only_description(api_client, auth_token):
    """Update only the description of a note, keeping title unchanged."""
    logger.info("Running test: test_update_only_description")
    headers = {"x-auth-token": auth_token}
    # First create a note to update
    create_resp = api_client.post("/notes",
                   payload={"title": "Title stays same",
                            "description": "Original desc",
                            "category": "Work"},
                   headers=headers)
    assert create_resp.status_code == 200, "Setup note creation failed"
    note_id = create_resp.json()["data"]["id"]
    # Now update only description
    update_resp = api_client.put(f"/notes/{note_id}",
                   payload={"title": "Title stays same",
                            "description": "Updated desc only",
                            "category": "Work",
                            "completed": False},
                   headers=headers)
    assert update_resp.status_code == 200, "Update description failed"
    assert update_resp.json()["data"]["description"] == "Updated desc only"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_delete_all_notes(api_client, auth_token):
    """Delete each note returned by GET /notes individually."""
    logger.info("Running test: test_delete_all_notes")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    notes = api_client.get("notes", headers=_auth_headers(auth_token)).json()
    for n in notes if isinstance(notes, list) else notes.get("data", []):
        api_client.delete(f"notes/{n.get('id')}", headers=_auth_headers(auth_token))
    assert api_client.get("notes", headers=_auth_headers(auth_token)).status_code == 200, "Notes list should still be accessible."

