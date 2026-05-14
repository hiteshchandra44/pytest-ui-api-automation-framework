"""
tests/api/test_auth_api.py

This file contains API tests for user authentication endpoints of the Notes API.
Docs: Notes API Swagger (see project config for base URL).
"""

import time
import uuid

import pytest

from utilities.logger import get_logger
from utilities.config_reader import read_config


logger = get_logger(__name__)


def _unique_email():
    """Generate a unique email for registration tests."""
    return f"api_user_{int(time.time() * 1000)}@example.com"


def _auth_headers(token: str):
    """Build x-auth-token header from a token string."""
    return {"x-auth-token": token}


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_register_user_success(api_client):
    """POST /users/register with valid data returns 201."""
    logger.info("Running test: test_register_user_success")
    password = read_config("api", "default_password").strip()
    email = f"api_user_{uuid.uuid4().hex}@example.com"
    payload = {"name": "API User", "email": email, "password": password}
    resp = api_client.post("users/register", payload=payload)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_register_duplicate_email(api_client):
    """POST /users/register with existing email returns 409."""
    logger.info("Running test: test_register_duplicate_email")
    password = read_config("api", "default_password").strip()
    email = _unique_email()
    api_client.post("users/register", payload={"name": "API User", "email": email, "password": password})
    resp = api_client.post("users/register", payload={"name": "API User", "email": email, "password": password})
    assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_register_missing_email(api_client):
    """POST /users/register without email returns 400."""
    logger.info("Running test: test_register_missing_email")
    password = read_config("api", "default_password").strip()
    resp = api_client.post("users/register", payload={"name": "API User", "password": password})
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_register_missing_password(api_client):
    """POST /users/register without password returns 400."""
    logger.info("Running test: test_register_missing_password")
    resp = api_client.post("users/register", payload={"name": "API User", "email": _unique_email()})
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.positive
def test_login_success(api_client):
    """POST /users/login with valid creds returns 200 and token."""
    logger.info("Running test: test_login_success")
    password = read_config("api", "default_password").strip()
    email = _unique_email()
    api_client.post("users/register", payload={"name": "API User", "email": email, "password": password})
    resp = api_client.post("users/login", payload={"email": email, "password": password})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    assert (resp.json().get("token") or resp.json().get("access_token")), "Token should be present in login response."


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_login_wrong_password(api_client):
    """POST /users/login with wrong password returns 401."""
    logger.info("Running test: test_login_wrong_password")
    password = read_config("api", "default_password").strip()
    wrong_password = read_config("api", "wrong_password").strip()
    email = _unique_email()
    api_client.post("users/register", payload={"name": "API User", "email": email, "password": password})
    resp = api_client.post("users/login", payload={"email": email, "password": wrong_password})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_login_invalid_email(api_client):
    """POST /users/login with bad email format returns 400."""
    logger.info("Running test: test_login_invalid_email")
    password = read_config("api", "default_password").strip()
    resp = api_client.post("users/login", payload={"email": "notanemail", "password": password})
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_get_profile_success(api_client):
    """GET /users/profile with valid token returns 200."""
    logger.info("Running test: test_get_profile_success")
    password = read_config("api", "default_password").strip()
    email = _unique_email()
    reg = api_client.post("users/register", payload={"name": "API User", "email": email, "password": password})
    assert reg.status_code in (200, 201), f"Expected 200/201 from register, got {reg.status_code}: {reg.text}"
    login_resp = api_client.post("users/login", payload={"email": email, "password": password})
    assert login_resp.status_code == 200, f"Expected 200 from login, got {login_resp.status_code}: {login_resp.text}"
    body = login_resp.json()
    token = body.get("token") or body.get("access_token") or (body.get("data") or {}).get("token")
    if token is None or token == "":
        pytest.skip("Login response did not include a token.")
    resp = api_client.get("users/profile", headers=_auth_headers(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    assert resp.json().get("email"), "Profile response should include email."


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_get_profile_no_token(api_client):
    """GET /users/profile without token returns 401."""
    logger.info("Running test: test_get_profile_no_token")
    resp = api_client.get("users/profile")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_get_profile_invalid_token(api_client):
    """GET /users/profile with an invalid token returns 401."""
    logger.info("Running test: test_get_profile_invalid_token")
    resp = api_client.get("users/profile", headers=_auth_headers("invalid.token.value"))
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
    try:
        data = resp.json()
    except Exception:
        data = {}
    assert data.get("message") or data.get("error") or resp.text, "Error message should be present for invalid token."


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.positive
def test_logout_success(api_client, auth_token):
    """DELETE /users/logout with token returns 200."""
    logger.info("Running test: test_logout_success")
    if not auth_token:
        pytest.skip("auth_token fixture returned empty token.")
    resp = api_client.delete("users/logout", headers=_auth_headers(auth_token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.negative
def test_logout_no_token(api_client):
    """DELETE /users/logout without token returns 401."""
    logger.info("Running test: test_logout_no_token")
    resp = api_client.delete("users/logout")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
    try:
        data = resp.json()
    except Exception:
        data = {}
    assert data.get("message") or data.get("error") or resp.text, "Error message should be present when token is missing."

