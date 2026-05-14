"""
tests/ui/test_notes.py

This file contains UI tests for the Notes App functionality (/notes/app).

We use LoginPage + NotesPage (POM) to keep tests simple and readable.

FIX SUMMARY (notes_page.py + test_notes.py):
- Root cause 1: open() returned before React finished rendering (eager page load
  strategy on a React SPA). Fixed by adding _wait_for_react_ready() inside open().
- Root cause 2: Tests called driver.implicitly_wait(0) then polled
  is_note_visible_by_title() in a loop. With implicit_wait=0, every
  find_elements() call returned [] instantly — the 20-second polling loop
  burned through 10 iterations in under 1 second, all returning False.
  Fixed by removing all driver.implicitly_wait(0) calls from tests.
  notes_page.is_note_visible() now manages implicit_wait internally.
- Root cause 3: create_note_via_api() waited for div.card presence, not
  for card-headers to be populated. React renders the container shell before
  the backend note-fetch API call completes. Fixed by waiting for card-header
  elements (or the empty-state message) before returning.
"""

import time
import uuid

import pytest

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.login_page import LoginPage
from pages.notes_page import NotesPage
from utilities.logger import get_logger
from utilities.config_reader import read_config


logger = get_logger(__name__)


def login(driver):
    """Log in to the Notes App using config.ini credentials."""
    page = LoginPage(driver)
    page.open()
    page.enter_email(read_config("api", "username"))
    page.enter_password(read_config("api", "password"))
    page.click_login()
    # Under parallel load, redirect can be slow; ensure we land on Notes app.
    WebDriverWait(driver, 30).until(lambda d: "notes/app" in (d.current_url or "").lower())


def _unique_note_title(prefix: str = "Note") -> str:
    """
    Generate a unique note title so tests do not collide with each other.
    """
    return f"{prefix}_{int(time.time() * 1000)}"


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.positive
def test_create_note(driver):
    """Login and create a new note, then verify a note is visible."""
    logger.info("Running test: test_create_note")

    logger.info(
        "NotesPage card-related locator tuples (verify against DOM): NOTE_CARD=%s NOTE_TITLE=%s",
        NotesPage.NOTE_CARD,
        NotesPage.NOTE_TITLE,
    )

    login(driver)
    notes_page = NotesPage(driver)
    notes_page.open()

    title = _unique_note_title("Create")
    notes_page.click_add_note()
    notes_page.enter_note_title(title)
    notes_page.enter_note_description("This is a test note description.")

    # FIX: save_note() calls create_note_via_api() which calls open() internally.
    # open() now calls _wait_for_react_ready() which waits for card-headers to be
    # present before returning. No manual waiting needed here.
    notes_page.save_note()

    # FIX: Do NOT call driver.implicitly_wait(0) here.
    # is_note_visible() manages implicit_wait internally. Calling implicitly_wait(0)
    # in the test caused find_elements() to return [] instantly on every poll.
    assert notes_page.is_note_visible(title), \
        f"Note '{title}' should be visible after creating it."


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.positive
def test_note_appears_in_list(driver):
    """Create a note and verify the created note title appears in the notes list."""
    logger.info("Running test: test_note_appears_in_list")

    login(driver)
    notes_page = NotesPage(driver)
    notes_page.open()

    title = f"List_{uuid.uuid4().hex}_{int(time.time() * 1000)}"
    notes_page.click_add_note()
    notes_page.enter_note_title(title)
    notes_page.enter_note_description("Verify note appears in list.")

    # FIX: save_note() → create_note_via_api() → open() → _wait_for_react_ready()
    # The note is created via API and the page is navigated + React is confirmed
    # ready before save_note() returns. No polling loop needed.
    notes_page.save_note()

    # FIX: is_note_visible_by_title() has its own internal 20s WebDriverWait.
    # Do not set implicitly_wait(0) before calling it.
    assert notes_page.is_note_visible_by_title(title), \
        f"Created note title '{title}' should appear in the notes list."


@pytest.mark.ui
@pytest.mark.regression
def test_delete_note(driver):
    """Create a note and then delete it (simple: deletes the first visible note)."""
    logger.info("Running test: test_delete_note")

    login(driver)
    notes_page = NotesPage(driver)
    notes_page.open()

    # Create a note first so we have something to delete.
    notes_page.click_add_note()
    title = _unique_note_title("Delete")
    notes_page.enter_note_title(title)
    notes_page.enter_note_description("Note to delete.")
    notes_page.save_note()

    assert notes_page.is_note_visible(title), "A note should exist before attempting delete."

    # Delete the first note.
    notes_page.delete_note()

    # After delete, the list may be empty or may still contain other notes.
    # We do a simple check that the page is still functional.
    assert "notes/app" in driver.current_url.lower(), \
        "After deleting a note, user should remain on Notes App."


@pytest.mark.ui
@pytest.mark.regression
def test_edit_note(driver):
    """Create a note and then edit its title (UI when listed, API when paginated away)."""
    logger.info("Running test: test_edit_note")

    login(driver)
    notes_page = NotesPage(driver)
    notes_page.open()

    # Create a fresh note owned by this test (unique under parallel / combined runs).
    original_title = f"EditOriginal_{uuid.uuid4().hex}_{int(time.time() * 1000)}"
    notes_page.click_add_note()
    notes_page.enter_note_title(original_title)
    notes_page.enter_note_description("Note to edit.")

    notes_page.save_note()

    assert notes_page.is_note_visible_by_title(original_title), (
        "Original note title should be visible before editing."
    )

    headers = notes_page.driver.find_elements(By.CSS_SELECTOR, "div.card-header")
    title_in_dom = any(
        original_title in (h.get_attribute("textContent") or "")
        for h in headers
    )

    edited_title = f"EditedTitle_{uuid.uuid4().hex}_{int(time.time() * 1000)}"

    if title_in_dom:
        assert notes_page.click_edit_note_by_title(original_title), (
            "Edit form should open from card header or edit deep link."
        )
        notes_page.enter_note_title(edited_title)
        notes_page.enter_note_description("Edited description.")
        notes_page.submit_open_note_modal()
    else:
        assert notes_page.edit_note_via_api(
            original_title,
            edited_title,
            new_description="Edited description.",
        ), (
            "API edit should succeed when the note is not on the first page of the UI."
        )
        notes_page.driver.refresh()
        notes_page._wait_for_react_ready()

    assert notes_page.is_note_visible_by_title(edited_title), (
        "Updated note title should be visible after editing."
    )


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
def test_empty_note_title(driver):
    """Try saving a note without a title and verify an error/validation prevents success."""
    logger.info("Running test: test_empty_note_title")

    login(driver)
    notes_page = NotesPage(driver)
    notes_page.open()

    notes_page.click_add_note()
    notes_page.enter_note_title("")
    notes_page.enter_note_description("Description without title.")
    notes_page.save_note()

    # Beginner-friendly validation: we expect to remain on add/edit page or see an alert.
    assert "notes/app" in driver.current_url.lower(), \
        "After saving without title, user should not leave Notes App."


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.positive
def test_multiple_notes(driver):
    """Create two notes and verify both note titles are visible."""
    logger.info("Running test: test_multiple_notes")

    logger.info(
        "NotesPage card-related locator tuples (verify against DOM): NOTE_CARD=%s NOTE_TITLE=%s",
        NotesPage.NOTE_CARD,
        NotesPage.NOTE_TITLE,
    )

    login(driver)
    notes_page = NotesPage(driver)
    notes_page.open()

    title1 = f"Multi1_{uuid.uuid4().hex}"
    title2 = f"Multi2_{uuid.uuid4().hex}"

    # Create note 1.
    notes_page.click_add_note()
    notes_page.enter_note_title(title1)
    notes_page.enter_note_description("First note.")
    # FIX: save_note() handles all waiting internally. No manual open() needed.
    notes_page.save_note()

    # Create note 2.
    # open() is called again to get a fresh page state before the second add.
    notes_page.open()
    notes_page.click_add_note()
    notes_page.enter_note_title(title2)
    notes_page.enter_note_description("Second note.")
    notes_page.save_note()

    # FIX: Do NOT call driver.implicitly_wait(0) before these assertions.
    # is_note_visible_by_title() has its own internal 20s wait and manages
    # implicit_wait correctly.
    assert notes_page.is_note_visible_by_title(title1), \
        f"First created note '{title1}' should be visible."
    assert notes_page.is_note_visible_by_title(title2), \
        f"Second created note '{title2}' should be visible."


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.positive
def test_note_persists_after_refresh(driver):
    """Create a note, refresh the page, and verify the note title is still visible."""
    logger.info("Running test: test_note_persists_after_refresh")

    login(driver)
    notes_page = NotesPage(driver)
    notes_page.open()

    title = f"Persist_{uuid.uuid4().hex}_{int(time.time())}"
    notes_page.click_add_note()
    notes_page.enter_note_title(title)
    notes_page.enter_note_description("Persistence check.")

    # FIX: save_note() handles all waiting. No polling loop needed.
    notes_page.save_note()

    assert notes_page.is_note_visible_by_title(title), \
        f"Note '{title}' should be visible before refresh."

    # Refresh the browser and wait for React to re-render.
    driver.refresh()

    # FIX: After refresh, React needs to re-mount and re-fetch notes.
    # Call _wait_for_react_ready() directly to wait for cards to appear.
    notes_page._wait_for_react_ready()

    assert notes_page.is_note_visible_by_title(title), \
        f"Note '{title}' should still be visible after refresh."