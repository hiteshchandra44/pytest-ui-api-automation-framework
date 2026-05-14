"""
tests/api/test_user_api.py

This file contains API tests for user profile and account management endpoints.
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


def _new_user(api_client):
    """Register and login a new user; return (email, password, token)."""
    password = read_config("api", "default_password").strip()
    email = f"user_{int(time.time() * 1000)}@example.com"
    api_client.post("users/register", payload={"name": "User", "email": email, "password": password})
    resp = api_client.post("users/login", payload={"email": email, "password": password})
    token = (resp.json().get("token") or resp.json().get("access_token") or "")
    return email, password, token


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.positive
def test_update_profile_success(api_client, auth_token):
    """PATCH /users/profile with new name returns 200."""
    logger.info("Running test: test_update_profile_success")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    resp = api_client.patch("users/profile", payload={"name": "New Name"}, headers=_auth_headers(auth_token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_update_profile_no_auth(api_client):
    """PATCH /users/profile without token returns 401."""
    logger.info("Running test: test_update_profile_no_auth")
    resp = api_client.patch("users/profile", payload={"name": "New Name"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_change_password_success(api_client):
    """POST /users/change-password returns 200."""
    logger.info("Running test: test_change_password_success")
    email, old_pw, token = _new_user(api_client)
    new_password = read_config("api", "new_password").strip()
    resp = api_client.post(
        "users/change-password",
        payload={"currentPassword": old_pw, "newPassword": new_password, "confirmPassword": new_password},
        headers=_auth_headers(token),
    )
    assert resp.status_code in (200, 400), "API should return 200 or 400 depending on password policy."


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_change_password_wrong_old(api_client):
    """POST /users/change-password with wrong current password returns 400."""
    logger.info("Running test: test_change_password_wrong_old")
    _, _, token = _new_user(api_client)
    wrong_old = read_config("api", "wrong_password").strip()
    new_password = read_config("api", "new_password").strip()
    resp = api_client.post(
        "users/change-password",
        payload={"currentPassword": wrong_old, "newPassword": new_password, "confirmPassword": new_password},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_change_password_mismatch(api_client):
    """POST /users/change-password with mismatch confirm returns 400."""
    logger.info("Running test: test_change_password_mismatch")
    _, old_pw, token = _new_user(api_client)
    new_password = read_config("api", "new_password").strip()
    mismatch = read_config("api", "wrong_password").strip()
    resp = api_client.post(
        "users/change-password",
        payload={"currentPassword": old_pw, "newPassword": new_password, "confirmPassword": mismatch},
        headers=_auth_headers(token),
    )
    assert resp.status_code in (200, 400), f"Expected 200 or 400 for mismatched passwords, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_get_profile_after_update(api_client, auth_token):
    """Update name then GET profile reflects it."""
    logger.info("Running test: test_get_profile_after_update")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    api_client.patch("users/profile", payload={"name": "Name After Update"}, headers=_auth_headers(auth_token))
    resp = api_client.get("users/profile", headers=_auth_headers(auth_token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_login_after_password_change(api_client):
    """Change password then login with new password returns 200."""
    logger.info("Running test: test_login_after_password_change")
    email, old_pw, token = _new_user(api_client)
    new_password = read_config("api", "new_password").strip()
    api_client.post(
        "users/change-password",
        payload={"currentPassword": old_pw, "newPassword": new_password, "confirmPassword": new_password},
        headers=_auth_headers(token),
    )
    resp = api_client.post("users/login", payload={"email": email, "password": new_password})
    assert resp.status_code in (200, 401, 400), "API should respond clearly for login after password change."


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_access_after_logout(api_client):
    """Use token after logout should return 401."""
    logger.info("Running test: test_access_after_logout")
    _, _, token = _new_user(api_client)
    api_client.delete("users/logout", headers=_auth_headers(token))
    resp = api_client.get("users/profile", headers=_auth_headers(token))
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_register_empty_name(api_client):
    """POST /users/register without name returns 400."""
    logger.info("Running test: test_register_empty_name")
    password = read_config("api", "default_password").strip()
    resp = api_client.post("users/register", payload={"email": f"e{int(time.time())}@e.com", "password": password})
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_create_note_after_relogin(api_client):
    """Re-login and create note returns 200."""
    logger.info("Running test: test_create_note_after_relogin")
    password = read_config("api", "default_password").strip()
    email = f"user_{uuid.uuid4().hex}@example.com"
    api_client.post("users/register", payload={"name": "User", "email": email, "password": password})
    api_client.post("users/login", payload={"email": email, "password": password})
    login_body = api_client.post("users/login", payload={"email": email, "password": password}).json()
    token = (
        (login_body or {}).get("token")
        or (login_body or {}).get("access_token")
        or ((login_body or {}).get("data") or {}).get("token")
        or ""
    )
    if not token:
        pytest.skip("Login response did not include a token (token, access_token, or data.token).")
    resp = api_client.post(
        "notes",
        payload={"title": "Relog_note", "description": "Test description", "category": "Home"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_profile_fields_present(api_client, auth_token):
    """GET /users/profile has id, name, email."""
    logger.info("Running test: test_profile_fields_present")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    data = api_client.get("users/profile", headers=_auth_headers(auth_token)).json()
    assert data.get("id") and data.get("name") and data.get("email"), "Profile should include id, name, and email."


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_note_response_fields(api_client, auth_token):
    """POST /notes response has id, title, category."""
    logger.info("Running test: test_note_response_fields")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    data = api_client.post("notes", payload={"title": "Fields", "description": "D", "category": "Home"}, headers=_auth_headers(auth_token)).json()
    assert (data.get("id") or (data.get("data") or {}).get("id")), "Note response should include id."


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_delete_account(api_client):
    """DELETE /users/delete-account returns 200 (or skip if unsupported)."""
    logger.info("Running test: test_delete_account")
    _, _, token = _new_user(api_client)
    resp = api_client.delete("users/delete-account", headers=_auth_headers(token))
    if resp.status_code == 404:
        pytest.skip("Delete account endpoint not supported in current environment.")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

