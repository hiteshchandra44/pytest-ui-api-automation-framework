import requests
import pytest

from utilities.config_reader import read_config
from utilities.logger import get_logger


@pytest.fixture(scope="session", autouse=True)
def delete_all_notes_for_test_account():
    """
    One-time cleanup for the shared UI test account used by tests in this module.
    Runs once per session for UI tests only (this conftest is under tests/ui/).
    """
    logger = get_logger("delete_all_notes_for_test_account")
    base_api = "https://practice.expandtesting.com/notes/api/v1"
    email = read_config("api", "username").strip()
    password = read_config("api", "password").strip()

    try:
        login_resp = requests.post(
            f"{base_api}/users/login",
            json={"email": email, "password": password},
            timeout=20,
        )
        body = login_resp.json() or {}
        token = body.get("token") or body.get("access_token") or (body.get("data") or {}).get("token") or ""
        if not token:
            logger.warning("Could not obtain token; skipping UI note cleanup.")
            return

        notes_resp = requests.get(
            f"{base_api}/notes",
            headers={"x-auth-token": token},
            timeout=30,
        )
        try:
            notes_json = notes_resp.json()
        except Exception:
            logger.warning(
                f"Notes cleanup skipped: GET /notes returned non-JSON (status {notes_resp.status_code})."
            )
            return
        notes_list = notes_json if isinstance(notes_json, list) else (notes_json.get("data") or [])

        deleted = 0
        for n in notes_list:
            nid = (n or {}).get("id")
            if not nid:
                continue
            r = requests.delete(
                f"{base_api}/notes/{nid}",
                headers={"x-auth-token": token},
                timeout=20,
            )
            if r.status_code in (200, 204):
                deleted += 1

        logger.info(f"Deleted {deleted} notes for shared UI test account.")
    except Exception as e:
        logger.warning(f"UI note cleanup encountered error: {e.__class__.__name__}: {e}")

