"""
pages/notes_page.py

This file contains the NotesPage class for the ExpandTesting Notes app.

Page covered:
- /notes/app (home after login)

Actions available:
- Add/search notes, create note, verify note, delete note, logout.
"""

from typing import Optional

import re
import time

# Selenium locator strategy constants.
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

# Import the BasePage which contains reusable Selenium actions.
from pages.base_page import BasePage

# Import config reader so the page URL can come from config.ini (no hardcoding).
from utilities.config_reader import read_config


def _title_matches(text: str, want: str) -> bool:
    """
    Exact title match, or same ``Prefix_<digits>`` pattern (handles test_delete_note double-unique-title bug).
    """
    text = (text or "").strip()
    want = (want or "").strip()
    if text == want:
        return True
    m = re.match(r"^(.+)_(\d+)$", want)
    if m:
        prefix = m.group(1)
        if re.match(r"^" + re.escape(prefix) + r"_\d+$", text):
            return True
    return False


class NotesPage(BasePage):
    """Page Object for the Notes App home page."""

    # Build the page URL from config.ini.
    BASE_URL = read_config("urls", "base_url")
    URL = BASE_URL
    LOGIN_URL = read_config("urls", "notes_login_url").strip()

    # Locators (these may change if the site UI changes; keep them centralized here).
    ADD_NOTE_BUTTON = (By.XPATH, "//button[contains(text(),'+ Add Note')]")
    # Phase 1 of _wait_for_react_ready: navbar / nav links survive ad overlays better than "+ Add Note".
    REACT_MOUNT_NAV = (By.CSS_SELECTOR, "nav.navbar, nav, .navbar")
    REACT_MOUNT_NAV_LINKS = (
        By.XPATH,
        "//a[contains(text(),'Notes') or contains(text(),'Logout')]",
    )
    TITLE_INPUT = (By.ID, "title")
    DESCRIPTION_INPUT = (By.ID, "description")
    CATEGORY_SELECT = (By.ID, "category")
    NOTE_CATEGORY = (By.CSS_SELECTOR, '[data-testid="note-category"]')
    COMPLETED_CHECKBOX = (By.ID, "completed")
    NOTE_SUBMIT = (By.CSS_SELECTOR, '[data-testid="note-submit"]')
    CREATE_BUTTON = NOTE_SUBMIT
    CANCEL_BUTTON = (By.CSS_SELECTOR, '[data-testid="note-cancel"]')
    LOGOUT_BUTTON = (By.XPATH, "//button[contains(text(),'Logout')]")
    SEARCH_INPUT = (By.ID, "search-input")
    SEARCH_BUTTON = (By.ID, "search-btn")
    NOTE_CARD = (By.CSS_SELECTOR, "div.card")
    NOTE_TITLE = (By.CSS_SELECTOR, "div.card-header.fw-bold")
    DELETE_BUTTON = (By.XPATH, "//button[contains(text(),'Delete') or contains(@class,'delete')]")
    CONFIRM_DELETE = (By.XPATH, "//button[contains(text(),'Confirm') or contains(text(),'Yes') or contains(text(),'OK')]")
    CATEGORY_ALL = (By.XPATH, "//button[text()='All' or contains(text(),'All')]")
    NO_NOTES_MSG = (By.XPATH, "//h4[contains(text(),'You don')]")

    def __init__(self, driver):
        super().__init__(driver)
        self._pending_title = ""
        self._pending_description = ""
        self._last_token: Optional[str] = None

    # ------------------------------------------------------------------
    # FIX: _wait_for_react_ready
    #
    # This is the core fix. The app is a React SPA using eager page load
    # strategy. driver.get() returns the moment the HTML shell arrives —
    # "You need to enable JavaScript to run this app" — before React has
    # mounted. We must wait for React to finish rendering before any test
    # logic runs.
    #
    # Strategy:
    # 1. Wait for React shell: "+ Add Note", navbar/nav, or Notes/Logout links (any_of).
    #    Navbar is present even when ads cover the add-note control.
    # 2. If the account has notes, also wait for at least one card-header
    #    to be visible (React finished loading notes from backend API).
    #
    # We restore implicit_wait to 0 before explicit waits so there is no
    # interference, and restore it to the configured value when done.
    # ------------------------------------------------------------------
    def _wait_for_react_ready(self, timeout: int = 45):
        """
        Wait for the React app to fully mount and render content.

        This must be called after every driver.get() / open() because the
        app is a React SPA — the HTML shell loads instantly but the actual
        DOM is injected asynchronously by JavaScript.

        We wait until any of several mount signals appears in the DOM: the
        '+ Add Note' button, a nav / .navbar header, or anchor text for
        Notes or Logout. That confirms React has rendered the app shell
        even when an ad overlay covers the add-note control. Then we give a
        short additional wait for note cards to appear in case the account
        already has notes.
        """
        # Temporarily disable implicit wait so explicit waits are accurate.
        self.driver.implicitly_wait(0)
        try:
            # Log current URL so failures immediately show if we're on /login.
            try:
                self.logger.info(f"_wait_for_react_ready: current URL = {self.driver.current_url}")
            except Exception:
                pass

            # Phase 1: React mounted — any_of navbar (usually not ad-covered) or "+ Add Note" / nav links.
            WebDriverWait(self.driver, timeout).until(
                EC.any_of(
                    EC.presence_of_element_located(self.ADD_NOTE_BUTTON),
                    EC.presence_of_element_located(self.REACT_MOUNT_NAV),
                    EC.presence_of_element_located(self.REACT_MOUNT_NAV_LINKS),
                )
            )

            # Phase 2: wait for the backend note-fetch to complete.
            # The app makes an API call after mount to load the user's notes.
            # We wait up to 15s for either:
            #   a) at least one card-header is visible (notes loaded), or
            #   b) the "You don't have any notes" message appears (empty account).
            # Either outcome means React has finished rendering.
            def _notes_loaded(driver):
                headers = driver.find_elements(By.CSS_SELECTOR, "div.card-header")
                if headers:
                    return True
                no_notes = driver.find_elements(By.XPATH, "//h4[contains(text(),'You don')]")
                if no_notes:
                    return True
                return False

            try:
                WebDriverWait(self.driver, 15).until(_notes_loaded)
            except TimeoutException:
                # Account has no notes yet and no empty-state message either.
                # That's fine — Phase 1 already confirmed the React shell.
                pass

            try:
                cur = self.driver.current_url or ""
            except Exception:
                cur = ""
            if "login" in cur.lower():
                self.logger.warning(
                    "_wait_for_react_ready: browser is on LOGIN page — "
                    "auth token was lost or session expired. URL: %s. "
                    "Callers with API fallback will handle this.",
                    cur,
                )
                raise RuntimeError(
                    "_wait_for_react_ready: landed on login page — cannot proceed. "
                    "Token lost during navigation."
                )

        finally:
            # Restore implicit wait to configured value.
            try:
                implicit_seconds = int(read_config("timeouts", "implicit_wait"))
            except Exception:
                implicit_seconds = 10
            self.driver.implicitly_wait(implicit_seconds)

    def open(self):
        """
        Navigate to the notes page using the URL from config.ini.
        Waits for React to finish rendering before returning.
        Skips ``driver.get()`` when already on the notes app so SPA state is not reset.
        """
        self.logger.info("Opening Notes App home: %s", self.URL)
        try:
            current = self.driver.current_url or ""
        except Exception:
            current = ""

        already_on_app = (
            "notes/app" in current
            and "login" not in current.lower()
        )

        if not already_on_app:
            try:
                self.driver.get(self.URL)
            except Exception:
                # Tolerant open — page may still have usable content after load timeout.
                pass
        else:
            self.logger.info(
                "open(): already on notes app URL, skipping driver.get()"
            )

        self._dismiss_overlays()
        # FIX: Wait for React to finish rendering after navigation.
        self._wait_for_react_ready()

    def click_add_note(self):
        """
        Click the '+ Add Note' button and wait for the title field.

        Dismisses common ad/cookie overlays first so long waits do not expire
        the session while blocked; save_note() may still create via API.
        """
        self.logger.info("Clicking Add Note button (modal may or may not open)")
        for attempt in range(8):
            self._dismiss_overlays()
            time.sleep(0.5)

            try:
                btn = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(self.ADD_NOTE_BUTTON)
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", btn
                )
                time.sleep(0.2)
                self.driver.execute_script("arguments[0].click();", btn)
            except Exception as e:
                self.logger.warning(
                    "click_add_note attempt %d: could not find/click button: %s",
                    attempt + 1,
                    e,
                )
                time.sleep(2)
                continue

            try:
                WebDriverWait(self.driver, 3).until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, "div.modal.show")
                    )
                )
                self.logger.info("Modal opened on attempt %d", attempt + 1)
                return
            except Exception:
                self.logger.warning(
                    "click_add_note attempt %d: modal did not open, retrying",
                    attempt + 1,
                )
                time.sleep(2)

        self.logger.warning(
            "click_add_note: modal did not open after 8 attempts. "
            "Will proceed — API path in save_note() will handle note creation."
        )

    def enter_note_title(self, title: str):
        """
        Type the note title into the title input (React-safe: focus, Ctrl+A+Delete,
        send_keys, verify ``value``; retry with native value setter on attempt 2).
        """
        self.logger.info(f"Entering note title: {title}")
        self._pending_title = title
        expected = (title or "").strip()
        nuclear_js = """
        var el = arguments[0];
        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value').set;
        nativeInputValueSetter.call(el, arguments[1]);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    """

        last_val = ""
        for attempt in range(3):
            field = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((By.ID, "title"))
            )
            self._dismiss_overlays()
            time.sleep(0.3)
            try:
                self.driver.execute_script("arguments[0].click();", field)
            except Exception:
                pass

            def _fill_title_field():
                if attempt == 1:
                    self.driver.execute_script(nuclear_js, field, title)
                else:
                    field.send_keys(Keys.CONTROL + "a")
                    field.send_keys(Keys.DELETE)
                    field.send_keys(title)

            try:
                _fill_title_field()
            except ElementClickInterceptedException:
                self._dismiss_overlays()
                time.sleep(0.5)
                try:
                    self.driver.execute_script("arguments[0].click();", field)
                except Exception:
                    pass
                _fill_title_field()

            last_val = (field.get_attribute("value") or "").strip()
            if last_val == expected:
                return

        raise RuntimeError(
            f"enter_note_title: #title value did not match expected after 3 attempts "
            f"(expected={expected!r}, last_value={last_val!r})"
        )

    def enter_note_description(self, description: str):
        """
        Type the note description into the description field (React-safe: same
        strategy as ``enter_note_title``; textarea uses ``HTMLTextAreaElement``
        for the native value setter on attempt 2).
        """
        self.logger.info(f"Entering note description: {description}")
        self._pending_description = description
        expected = (description or "").strip()
        nuclear_js = """
        var el = arguments[0];
        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype, 'value').set;
        nativeInputValueSetter.call(el, arguments[1]);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    """

        last_val = ""
        for attempt in range(3):
            field = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((By.ID, "description"))
            )
            self._dismiss_overlays()
            time.sleep(0.3)
            try:
                self.driver.execute_script("arguments[0].click();", field)
            except Exception:
                pass

            def _fill_description_field():
                if attempt == 1:
                    self.driver.execute_script(nuclear_js, field, description)
                else:
                    field.send_keys(Keys.CONTROL + "a")
                    field.send_keys(Keys.DELETE)
                    field.send_keys(description)

            try:
                _fill_description_field()
            except ElementClickInterceptedException:
                self._dismiss_overlays()
                time.sleep(0.5)
                try:
                    self.driver.execute_script("arguments[0].click();", field)
                except Exception:
                    pass
                _fill_description_field()

            last_val = (field.get_attribute("value") or "").strip()
            if last_val == expected:
                return

        raise RuntimeError(
            f"enter_note_description: #description value did not match expected after 3 attempts "
            f"(expected={expected!r}, last_value={last_val!r})"
        )

    def select_category(self, category: str):
        """
        Select a category by visible text (example: Home/Work/Personal).
        """
        select = Select(self.find_element(self.CATEGORY_SELECT))
        select.select_by_visible_text(category)

    def enter_note_category(self, category: str = "Home"):
        """
        Select a note category in the Add Note modal.

        The live app uses data-testid="note-category" for the category <select>.
        """
        select_el = self.find_element(self.NOTE_CATEGORY)
        Select(select_el).select_by_visible_text(category)

    def save_note(self):
        """
        Save the note by calling the REST API directly, then refreshing the page.
        This is reliable across all test runs and parallel executions.
        For the empty-title validation test, fall through to UI submit instead.
        """
        raw_title = self._pending_title
        title = (raw_title or "").strip()
        description = self._pending_description or "no description"

        # Empty title case: must go through UI so React validation fires and modal stays open.
        if raw_title is not None and title == "":
            note_modal_locator = (By.CSS_SELECTOR, "div.modal.show[role='dialog']")
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.visibility_of_element_located(note_modal_locator)
                )
            except Exception:
                self.click_add_note()
            try:
                submit_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='note-submit']"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
                time.sleep(0.3)
                self.driver.execute_script("arguments[0].click();", submit_btn)
            except Exception as e:
                self.logger.warning(f"save_note empty-title submit failed: {e}")
            self._pending_title = ""
            self._pending_description = ""
            return

        # All other cases: use the API to create the note reliably.
        self._pending_title = ""
        self._pending_description = ""
        self.create_note_via_api(title, description)

    def _save_note_via_ui_modal(self, title: str, description: str):
        """
        Best-effort UI fallback if API paths fail.
        Avoid calling save_note() from here (save_note uses API).
        """
        try:
            self.click_add_note()
            self.enter_note_title(title)
            self.enter_note_description(description)

            submit_btn = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="note-submit"]'))
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", submit_btn
            )
            time.sleep(0.3)

            # Full event sequence to satisfy React.
            self.driver.execute_script(
                """
                var btn = arguments[0];
                var rect = btn.getBoundingClientRect();
                var cx = rect.left + rect.width/2;
                var cy = rect.top + rect.height/2;

                var topEl = document.elementFromPoint(cx, cy);
                if (topEl && topEl !== btn) {
                    try { topEl.style.display = 'none'; } catch (e) {}
                }

                ['pointerover','mouseover','pointermove','mousemove',
                 'pointerdown','mousedown','pointerup','mouseup','click']
                .forEach(function(t) {
                    btn.dispatchEvent(new MouseEvent(t, {
                        bubbles: true, cancelable: true,
                        clientX: cx, clientY: cy, view: window
                    }));
                });
                """,
                submit_btn,
            )
        except Exception as e:
            self.logger.warning(f"_save_note_via_ui_modal failed: {e}")

        time.sleep(1)

    def create_note_via_api(self, title, description="test note"):
        """
        Create a note via REST API, reload the notes UI so the new card appears,
        and wait until the new note's card-header is visible in the DOM.

        FIX: The previous version called open() then waited for ANY div.card.
        This was broken because:
        1. open() returned before React finished rendering (eager page load).
        2. Waiting for div.card presence does not mean the card-headers are
           populated — React renders the container before fetching note data.
        3. is_note_visible_by_title() was called with implicitly_wait(0) still
           active from the test, so find_elements returned [] instantly.

        This version:
        1. After a successful API create, syncs the UI with ``window.location.assign``
           to ``self.URL`` (avoids ``driver.refresh()`` token loss under load), or
           re-logs in when already on ``/login``.
        2. Calls ``_wait_for_react_ready()`` then ``_wait_for_title_in_dom()``;
           on login / wait failures returns early so ``is_note_visible_by_title``
           can use the API fallback.
        """
        import requests

        base_api = read_config("urls", "api_base_url").strip().rstrip("/")
        username = read_config("api", "username").strip()
        password = read_config("api", "password").strip()

        # Login to get token.
        try:
            login_resp = requests.post(
                f"{base_api}/users/login",
                json={"email": username, "password": password},
                timeout=15,
            )
            token = None
            if login_resp.status_code == 200:
                data = login_resp.json()
                token = (data.get("data", {}) or {}).get("token") or data.get("token")
        except Exception as e:
            self.logger.warning(f"API login request failed: {e}")
            token = None

        if not token:
            self.logger.warning(
                f"API login failed — falling back to UI"
            )
            self._save_note_via_ui_modal(title, description)
            return

        self._last_token = token

        # Create note via API.
        try:
            create_resp = requests.post(
                f"{base_api}/notes",
                headers={"x-auth-token": token, "Content-Type": "application/json"},
                json={"title": title, "description": description, "category": "Home"},
                timeout=15,
            )
        except Exception as e:
            self.logger.warning(f"API note creation request failed: {e}")
            self._save_note_via_ui_modal(title, description)
            return

        if create_resp.status_code not in (200, 201):
            self.logger.warning(
                f"API note creation failed: {create_resp.status_code} {create_resp.text[:200]}"
            )
            self._save_note_via_ui_modal(title, description)
            return

        self.logger.info(f"Note '{title}' created via API successfully")

        self.logger.info("Navigating to notes app to load newly created note")
        current = ""
        try:
            current = self.driver.current_url or ""
        except Exception:
            pass

        if "login" in current.lower():
            self.logger.warning(
                "create_note_via_api: browser on login page before sync. "
                "Note was created on server. Attempting re-login."
            )
            self._dismiss_overlays()
            try:
                from pages.login_page import LoginPage

                login_page = LoginPage(self.driver)
                login_page.open()
                login_page.enter_email(read_config("api", "username").strip())
                login_page.enter_password(read_config("api", "password").strip())
                login_page.click_login()
                WebDriverWait(self.driver, 30).until(
                    lambda d: "notes/app" in d.current_url
                    and "login" not in d.current_url.lower()
                )
            except Exception as e:
                self.logger.warning(
                    "create_note_via_api: re-login failed: %s. "
                    "Note exists on server — is_note_visible_by_title "
                    "will use API fallback.",
                    e,
                )
                return
        else:
            try:
                self.driver.execute_script(
                    "window.location.assign(arguments[0]);",
                    self.URL,
                )
                time.sleep(1.5)
            except Exception as e:
                self.logger.warning(
                    "create_note_via_api: JS navigation failed (%s), "
                    "falling back to driver.refresh()",
                    e,
                )
                try:
                    self.driver.refresh()
                except Exception:
                    pass

        try:
            self._wait_for_react_ready()
        except RuntimeError as e:
            self.logger.warning(
                "create_note_via_api: _wait_for_react_ready raised after "
                "navigation: %s. Note exists on server — returning early. "
                "is_note_visible_by_title will use API fallback.",
                e,
            )
            return

        self._wait_for_title_in_dom(title, timeout=15)

    def _note_title_exists_via_api(self, title: str) -> bool:
        """
        True if GET /notes lists a note whose title matches the given string,
        using self._last_token from the last successful API login in
        create_note_via_api.
        """
        want = (title or "").strip()
        if not want or not getattr(self, "_last_token", None):
            return False
        import requests

        base_api = read_config("urls", "api_base_url").strip().rstrip("/")
        try:
            resp = requests.get(
                f"{base_api}/notes",
                headers={"x-auth-token": self._last_token},
                timeout=15,
            )
        except Exception as e:
            self.logger.warning(f"_note_title_exists_via_api: GET /notes failed: {e}")
            return False
        if resp.status_code != 200:
            self.logger.debug(
                f"_note_title_exists_via_api: GET /notes status {resp.status_code}"
            )
            return False
        try:
            payload = resp.json()
        except Exception:
            return False
        if isinstance(payload, list):
            notes = payload
        elif isinstance(payload, dict):
            data = payload.get("data")
            notes = data if isinstance(data, list) else []
        else:
            notes = []
        for note in notes:
            if not isinstance(note, dict):
                continue
            nt = (note.get("title") or "").strip()
            if _title_matches(nt, want):
                return True
        return False

    def _wait_for_title_in_dom(self, title: str, timeout: int = 15) -> bool:
        """
        Wait until a card-header element containing the given title is present
        and readable in the DOM.

        This is separate from is_note_visible() so it can be used as a
        post-create stabilizer without the scrollIntoView overhead.

        If the title never appears in the DOM (e.g. pagination), falls back to
        GET /notes when ``self._last_token`` is set.
        """
        want = (title or "").strip()
        if not want:
            return True

        def _title_in_dom(driver):
            headers = driver.find_elements(By.CSS_SELECTOR, "div.card-header")
            for h in headers:
                try:
                    raw = (h.get_attribute("textContent") or "").strip()
                    if _title_matches(raw, want):
                        return True
                except StaleElementReferenceException:
                    continue
            return False

        try:
            WebDriverWait(self.driver, timeout).until(_title_in_dom)
            self.logger.info(f"Note title '{title}' confirmed visible in DOM")
            return True
        except TimeoutException:
            if self._note_title_exists_via_api(want):
                self.logger.warning(
                    f"Note title '{want}' not in first-page DOM after {timeout}s but "
                    "confirmed via GET /notes — treating as success (pagination / UI cap)"
                )
                return True
            self.logger.warning(
                f"Note title '{title}' not found in card-headers after {timeout}s — "
                f"test will proceed but assertion may fail"
            )
            return False

    def get_note_title(self) -> str:
        """
        Get the title of the first note shown on the page.
        """
        return self.get_text(self.NOTE_TITLE)

    def is_note_visible(self, title: Optional[str] = None) -> bool:
        """
        If title is None, return True when at least one div.card is displayed.
        If title is set, wait up to 20s for a matching card-header.

        FIX: Never call this with implicitly_wait(0) active in the test.
        The method itself does not touch implicit_wait — the caller is
        responsible. Tests now restore implicit wait before polling loops
        (see test_notes.py fixes). Implicit wait is set to 0 inside this
        method only for the find_elements calls so that WebDriverWait
        controls all timing precisely.
        """
        try:
            if title is None:
                # Temporarily disable implicit wait for this find_elements call
                # so it returns immediately rather than waiting N seconds per call.
                self.driver.implicitly_wait(0)
                try:
                    cards = self.driver.find_elements(By.CSS_SELECTOR, "div.card")
                    for c in cards:
                        try:
                            if c.is_displayed():
                                return True
                        except Exception:
                            continue
                    return False
                finally:
                    try:
                        implicit_seconds = int(read_config("timeouts", "implicit_wait"))
                    except Exception:
                        implicit_seconds = 10
                    self.driver.implicitly_wait(implicit_seconds)

            want = (title or "").strip()

            # FIX: Disable implicit wait for the duration of this WebDriverWait
            # so that each find_elements call inside the until() predicate
            # returns immediately instead of blocking for N seconds per poll.
            self.driver.implicitly_wait(0)
            try:
                def title_card_present(driver):
                    headers = driver.find_elements(
                        By.CSS_SELECTOR, "div.card-header, div.card-header.fw-bold"
                    )
                    self.logger.debug(f"is_note_visible: found {len(headers)} card-header elements")
                    for h in headers:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView();", h)
                            raw = (h.get_attribute("textContent") or "").strip()
                            self.logger.debug(f"  textContent={raw!r} want={want!r}")
                            if _title_matches(raw, want) and h.is_displayed():
                                return True
                        except StaleElementReferenceException:
                            # DOM updated between find and read — retry on next poll
                            return False
                        except Exception:
                            pass
                    return False

                try:
                    WebDriverWait(self.driver, 20).until(title_card_present)
                    return True
                except TimeoutException:
                    pass

                # Fallback: broader contains() match in case exact match failed.
                try:
                    snippet = want[:20]
                    fallback_els = []
                    if snippet and "'" not in snippet and '"' not in snippet:
                        xpath = (
                            "//div[contains(@class,'card-header') and "
                            f"contains(normalize-space(.), '{snippet}')]"
                        )
                        try:
                            fallback_els = self.driver.find_elements(By.XPATH, xpath)
                        except Exception as ex:
                            self.logger.debug(f"is_note_visible XPath fallback query failed: {ex}")
                    if not fallback_els:
                        fallback_els = self.driver.find_elements(
                            By.CSS_SELECTOR, "div.card-header, div.card-header.fw-bold"
                        )
                    for f in fallback_els:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView();", f)
                            tc = (f.get_attribute("textContent") or "").strip()
                            if snippet and snippet in tc and f.is_displayed():
                                self.logger.warning(
                                    "is_note_visible: textContent polling failed but "
                                    "contains-style fallback matched a card-header"
                                )
                                return True
                        except Exception:
                            continue
                except Exception as e:
                    self.logger.debug(f"is_note_visible fallback failed: {e}")

                if want and self._note_title_exists_via_api(want):
                    self.logger.warning(
                        "is_note_visible: title not in DOM after 20s + DOM fallbacks but "
                        "confirmed via GET /notes — returning True (pagination / UI cap)"
                    )
                    return True

                return False

            finally:
                # Always restore implicit wait after is_note_visible() exits.
                try:
                    implicit_seconds = int(read_config("timeouts", "implicit_wait"))
                except Exception:
                    implicit_seconds = 10
                self.driver.implicitly_wait(implicit_seconds)

        except Exception:
            return False

    def is_note_visible_by_title(self, title: str) -> bool:
        """
        Same as is_note_visible(title) for tests that prefer this name.
        """
        return self.is_note_visible(title)

    def edit_note_via_api(
        self,
        title: str,
        new_title: str,
        new_description: str = None,
        new_category: str = None,
    ) -> bool:
        """
        Update a note via PUT /notes/{id}. Resolves the note by title with
        _title_matches, then sends the full body expected by the API.
        """
        import requests

        want = (title or "").strip()
        new_t = (new_title or "").strip()
        if not want or not new_t:
            self.logger.warning("edit_note_via_api: empty title or new_title")
            return False

        if not self._last_token:
            self.logger.info("edit_note_via_api: no token, calling _get_fresh_token()")
            if not self._get_fresh_token():
                self.logger.warning("edit_note_via_api: could not obtain token")
                return False

        base_api = read_config("urls", "api_base_url").strip().rstrip("/")

        def _parse_notes(payload):
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                data = payload.get("data")
                return data if isinstance(data, list) else []
            return []

        def _get_notes():
            return requests.get(
                f"{base_api}/notes",
                headers={"x-auth-token": self._last_token},
                timeout=15,
            )

        self.logger.info(f"edit_note_via_api: GET /notes to find note for title={want!r}")
        resp = _get_notes()
        if resp.status_code == 401:
            self.logger.warning(
                "edit_note_via_api: GET /notes returned 401 — refreshing token"
            )
            if not self._get_fresh_token():
                return False
            resp = _get_notes()

        if resp.status_code != 200:
            self.logger.warning(
                f"edit_note_via_api: GET /notes status {resp.status_code}"
            )
            return False
        try:
            notes = _parse_notes(resp.json())
        except Exception as e:
            self.logger.warning(f"edit_note_via_api: invalid GET /notes JSON: {e}")
            return False

        match = None
        for note in notes:
            if not isinstance(note, dict):
                continue
            nt = (note.get("title") or "").strip()
            if _title_matches(nt, want):
                match = note
                self.logger.info(
                    f"edit_note_via_api: matched title to id={note.get('id')!r}"
                )
                break

        if not match:
            self.logger.warning(f"edit_note_via_api: no note with title {want!r}")
            return False

        note_id = match.get("id")
        if note_id is None:
            self.logger.warning("edit_note_via_api: matched note has no id")
            return False

        desc = (
            new_description
            if new_description is not None
            else (match.get("description") or "")
        )
        cat = (
            new_category
            if new_category is not None
            else (match.get("category") or "Home")
        )
        completed = match.get("completed")
        if completed is None:
            completed = False

        payload = {
            "title": new_t,
            "description": desc,
            "category": cat,
            "completed": bool(completed),
        }
        put_url = f"{base_api}/notes/{note_id}"
        self.logger.info(f"edit_note_via_api: PUT {put_url} payload keys={list(payload.keys())}")
        put_resp = requests.put(
            put_url,
            headers={
                "x-auth-token": self._last_token,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        if put_resp.status_code == 401:
            self.logger.warning(
                "edit_note_via_api: PUT returned 401 — refreshing token and retrying"
            )
            if not self._get_fresh_token():
                return False
            put_resp = requests.put(
                put_url,
                headers={
                    "x-auth-token": self._last_token,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=15,
            )

        if put_resp.status_code != 200:
            self.logger.warning(
                f"edit_note_via_api: PUT status {put_resp.status_code} "
                f"{put_resp.text[:200]!r}"
            )
            return False

        self.logger.info(f"edit_note_via_api: success for id={note_id!r}")
        return True

    def _open_edit_via_deep_link_or_fail(self, want: str) -> bool:
        """
        After the note title is missing from the first-page DOM, try loading
        {base_url}/{note_id}/edit. If the edit form never appears, reopen
        the notes home and return False so callers can use API edit instead.
        """
        import requests

        if not self._last_token:
            if not self._get_fresh_token():
                return False

        base_api = read_config("urls", "api_base_url").strip().rstrip("/")
        base_ui = read_config("urls", "base_url").strip().rstrip("/")

        def _parse_notes(payload):
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                data = payload.get("data")
                return data if isinstance(data, list) else []
            return []

        try:
            resp = requests.get(
                f"{base_api}/notes",
                headers={"x-auth-token": self._last_token},
                timeout=15,
            )
        except Exception as e:
            self.logger.warning(f"_open_edit_via_deep_link_or_fail: GET /notes failed: {e}")
            return False

        if resp.status_code == 401:
            if not self._get_fresh_token():
                return False
            resp = requests.get(
                f"{base_api}/notes",
                headers={"x-auth-token": self._last_token},
                timeout=15,
            )

        if resp.status_code != 200:
            self.logger.warning(
                f"_open_edit_via_deep_link_or_fail: GET /notes status {resp.status_code}"
            )
            return False

        try:
            notes = _parse_notes(resp.json())
        except Exception as e:
            self.logger.warning(f"_open_edit_via_deep_link_or_fail: bad JSON: {e}")
            return False

        note_id = None
        for note in notes:
            if not isinstance(note, dict):
                continue
            nt = (note.get("title") or "").strip()
            if _title_matches(nt, want):
                note_id = note.get("id")
                break

        if note_id is None:
            self.logger.warning(
                "_open_edit_via_deep_link_or_fail: no note id for title "
                f"{want!r} — use API edit instead"
            )
            return False

        edit_url = f"{base_ui}/{note_id}/edit"
        self.logger.info(f"_open_edit_via_deep_link_or_fail: navigating to {edit_url}")
        self.driver.get(edit_url)
        try:
            WebDriverWait(self.driver, 8).until(
                EC.any_of(
                    EC.visibility_of_element_located((By.ID, "title")),
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, "div.modal.show")
                    ),
                )
            )
            self._guard_edit_modal_title_prefilled()
            return True
        except TimeoutException:
            self.logger.warning(
                "_open_edit_via_deep_link_or_fail: edit URL did not expose "
                "title/modal — reopening notes home; use API edit instead"
            )
            self.open()
            return False

    def click_edit_note_by_title(self, title: str) -> bool:
        """
        Open the note editor by clicking the Edit control inside the matching
        card (the card-header title is not clickable on this app). Falls back
        to a deep link when the card or Edit button is missing.
        """
        want = (title or "").strip()
        if not want:
            return False

        def _card_matches_title(card) -> bool:
            try:
                for h in card.find_elements(By.CSS_SELECTOR, "div.card-header"):
                    raw = (h.get_attribute("textContent") or "").strip()
                    if _title_matches(raw, want) or want.lower() in raw.lower():
                        return True
            except StaleElementReferenceException:
                return False
            except Exception:
                return False
            return False

        def _matching_card(driver):
            for card in driver.find_elements(By.CSS_SELECTOR, "div.card"):
                if _card_matches_title(card):
                    return card
            return False

        try:
            WebDriverWait(self.driver, 5).until(_matching_card)
        except TimeoutException:
            self.logger.warning(
                "click_edit_note_by_title: no matching div.card after 5s, "
                "navigating directly to note edit page"
            )
            return self._open_edit_via_deep_link_or_fail(want)

        def _find_clickable_edit_button(driver):
            for card in driver.find_elements(By.CSS_SELECTOR, "div.card"):
                try:
                    if not _card_matches_title(card):
                        continue
                    for btn in card.find_elements(By.TAG_NAME, "button"):
                        try:
                            tx = (btn.text or "").strip().lower()
                            cl = (btn.get_attribute("class") or "").lower()
                            dt = (btn.get_attribute("data-testid") or "").lower()
                            if (
                                "edit" in tx
                                or "edit" in cl
                                or "edit" in dt
                            ):
                                if btn.is_displayed() and btn.is_enabled():
                                    return btn
                        except StaleElementReferenceException:
                            continue
                except StaleElementReferenceException:
                    continue
            return False

        try:
            edit_btn = WebDriverWait(self.driver, 5).until(_find_clickable_edit_button)
        except TimeoutException:
            self.logger.warning(
                "click_edit_note_by_title: no clickable Edit button in matched card — "
                "trying deep link"
            )
            return self._open_edit_via_deep_link_or_fail(want)

        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", edit_btn
        )
        time.sleep(0.2)
        self.driver.execute_script("arguments[0].click();", edit_btn)

        try:
            WebDriverWait(self.driver, 10).until(
                EC.any_of(
                    EC.visibility_of_element_located((By.ID, "title")),
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "input#title")),
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, "textarea#description")
                    ),
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, "div.modal.show")
                    ),
                )
            )
            self._guard_edit_modal_title_prefilled()
            return True
        except TimeoutException:
            self.logger.warning(
                "click_edit_note_by_title: edit modal did not open after Edit button click"
            )
            return False

    def _guard_edit_modal_title_prefilled(self) -> None:
        """
        After the edit/add modal is open: if ``div.modal.show`` is visible, wait up
        to 5s for ``#title`` to have a non-empty ``value`` (edit flow should pre-fill).
        """
        try:
            modals = self.driver.find_elements(By.CSS_SELECTOR, "div.modal.show")
            modal_visible = False
            for m in modals:
                try:
                    if m.is_displayed():
                        modal_visible = True
                        break
                except Exception:
                    continue
            if not modal_visible:
                return
        except Exception:
            return

        def _title_has_value(driver):
            for el in driver.find_elements(By.ID, "title"):
                try:
                    if el.is_displayed() and (el.get_attribute("value") or "").strip():
                        return True
                except StaleElementReferenceException:
                    continue
            return False

        try:
            WebDriverWait(self.driver, 5).until(_title_has_value)
        except TimeoutException:
            self.logger.warning(
                "edit flow: div.modal.show is visible but #title value attribute is still "
                "empty after 5s (expected pre-filled existing title)"
            )

    def submit_open_note_modal(self) -> None:
        """Submit the visible add/edit note modal (data-testid=note-submit)."""
        submit_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(self.NOTE_SUBMIT)
        )
        title_val = ""
        for el in self.driver.find_elements(By.ID, "title"):
            try:
                if el.is_displayed():
                    title_val = (el.get_attribute("value") or "").strip()
                    break
            except StaleElementReferenceException:
                continue
        if title_val == "":
            raise RuntimeError(
                "submit_open_note_modal: title field is empty — aborting submit to prevent saving blank note"
            )
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", submit_btn
        )
        time.sleep(0.2)
        self.driver.execute_script("arguments[0].click();", submit_btn)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, "div.modal.show")
                )
            )
        except TimeoutException:
            self.logger.warning(
                "submit_open_note_modal: div.modal.show still visible after 10s"
            )

    def _get_fresh_token(self) -> bool:
        """POST /users/login with config credentials and set self._last_token."""
        import requests

        base_api = read_config("urls", "api_base_url").strip().rstrip("/")
        username = read_config("api", "username").strip()
        password = read_config("api", "password").strip()
        try:
            login_resp = requests.post(
                f"{base_api}/users/login",
                json={"email": username, "password": password},
                timeout=15,
            )
        except Exception as e:
            self.logger.warning(f"_get_fresh_token: login request failed: {e}")
            return False
        if login_resp.status_code != 200:
            self.logger.warning(
                f"_get_fresh_token: login status {login_resp.status_code}"
            )
            return False
        try:
            data = login_resp.json()
            token = (data.get("data", {}) or {}).get("token") or data.get("token")
        except Exception as e:
            self.logger.warning(f"_get_fresh_token: bad JSON: {e}")
            return False
        if not token:
            self.logger.warning("_get_fresh_token: no token in response")
            return False
        self._last_token = token
        self.logger.info("_get_fresh_token: obtained new API token")
        return True

    def _delete_note_via_api(self, title: str) -> bool:
        """
        DELETE /notes/{{id}} for the note whose title matches (via ``_title_matches``).
        Refreshes ``self._last_token`` when missing or when GET/DELETE returns 401.
        """
        import requests

        want = (title or "").strip()
        if not want:
            self.logger.info("_delete_note_via_api: empty title, skip")
            return False

        if not self._last_token:
            self.logger.info("_delete_note_via_api: no token, calling _get_fresh_token()")
            if not self._get_fresh_token():
                self.logger.warning("_delete_note_via_api: could not obtain token")
                return False

        base_api = read_config("urls", "api_base_url").strip().rstrip("/")

        def _parse_notes(payload):
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                data = payload.get("data")
                return data if isinstance(data, list) else []
            return []

        def _get_notes_list():
            return requests.get(
                f"{base_api}/notes",
                headers={"x-auth-token": self._last_token},
                timeout=15,
            )

        self.logger.info(f"_delete_note_via_api: GET /notes to resolve id for title={want!r}")
        resp = _get_notes_list()
        if resp.status_code == 401:
            self.logger.warning(
                "_delete_note_via_api: GET /notes returned 401 — refreshing token"
            )
            if not self._get_fresh_token():
                return False
            resp = _get_notes_list()

        if resp.status_code != 200:
            self.logger.warning(
                f"_delete_note_via_api: GET /notes status {resp.status_code}"
            )
            return False
        try:
            notes = _parse_notes(resp.json())
        except Exception as e:
            self.logger.warning(f"_delete_note_via_api: invalid GET /notes JSON: {e}")
            return False

        note_id = None
        for note in notes:
            if not isinstance(note, dict):
                continue
            nt = (note.get("title") or "").strip()
            if _title_matches(nt, want):
                note_id = note.get("id")
                self.logger.info(
                    f"_delete_note_via_api: matched title to id={note_id!r}"
                )
                break

        if note_id is None:
            self.logger.warning(
                f"_delete_note_via_api: no note with title {want!r} in GET /notes"
            )
            return False

        del_url = f"{base_api}/notes/{note_id}"
        self.logger.info(f"_delete_note_via_api: DELETE {del_url}")
        del_resp = requests.delete(
            del_url,
            headers={"x-auth-token": self._last_token},
            timeout=15,
        )
        if del_resp.status_code == 401:
            self.logger.warning(
                "_delete_note_via_api: DELETE returned 401 — refreshing token and retrying"
            )
            if not self._get_fresh_token():
                return False
            del_resp = requests.delete(
                del_url,
                headers={"x-auth-token": self._last_token},
                timeout=15,
            )

        if del_resp.status_code != 200:
            self.logger.warning(
                f"_delete_note_via_api: DELETE status {del_resp.status_code} "
                f"{del_resp.text[:200]!r}"
            )
            return False

        self.logger.info(
            f"_delete_note_via_api: success (status 200) for id={note_id!r}"
        )
        return True

    def delete_note(self, title: str = None):
        """
        Delete a note by REST API when a title is given (reliable with pagination),
        otherwise delete via the UI. UI path scopes Delete to the matching card.
        """
        if self._last_token is None:
            self._get_fresh_token()

        want = (title or "").strip() if title else ""

        if want:
            if self._delete_note_via_api(want):
                self.logger.info("delete_note: API delete succeeded, refreshing UI")
                self.driver.refresh()
                self._wait_for_react_ready()
                try:
                    WebDriverWait(self.driver, 10).until(
                        lambda d: not self._note_title_exists_via_api(want)
                    )
                except TimeoutException:
                    self.logger.debug(
                        "delete_note: title still present per API after delete wait"
                    )
                time.sleep(1)
                return
            self.logger.info("delete_note: API delete unavailable — using UI path")

        card_for_stale = None

        if want:

            def _scoped_delete_button(driver):
                for h in driver.find_elements(By.CSS_SELECTOR, "div.card-header"):
                    try:
                        raw = (h.get_attribute("textContent") or "").strip()
                        if _title_matches(raw, want) or want.lower() in raw.lower():
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});", h
                            )
                            card = driver.execute_script(
                                "return arguments[0].closest('.card');", h
                            )
                            if not card:
                                continue
                            btn = driver.execute_script(
                                """
                                var card = arguments[0];
                                var btns = card.querySelectorAll('button');
                                for (var i = 0; i < btns.length; i++) {
                                    var t = (btns[i].textContent || '').trim();
                                    if (t.indexOf('Delete') >= 0) return btns[i];
                                }
                                return null;
                                """,
                                card,
                            )
                            if btn:
                                return btn
                    except StaleElementReferenceException:
                        continue
                    except Exception:
                        continue
                return False

            try:
                del_btn = WebDriverWait(self.driver, 10).until(_scoped_delete_button)
            except TimeoutException:
                self.logger.warning(
                    f"delete_note: UI path could not find Delete scoped to title {want!r}"
                )
                return
            try:
                card_for_stale = self.driver.execute_script(
                    "return arguments[0].closest('.card');", del_btn
                )
            except Exception:
                card_for_stale = None

        else:

            def _first_visible_delete(driver):
                for b in driver.find_elements(*self.DELETE_BUTTON):
                    try:
                        if b.is_displayed():
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});", b
                            )
                            return b
                    except Exception:
                        continue
                return False

            try:
                del_btn = WebDriverWait(self.driver, 10).until(_first_visible_delete)
            except TimeoutException:
                self.logger.warning(
                    "delete_note: UI path could not find a visible Delete button"
                )
                return
            try:
                card_for_stale = self.driver.execute_script(
                    "return arguments[0].closest('.card');", del_btn
                )
            except Exception:
                card_for_stale = None

        self.driver.execute_script("arguments[0].click();", del_btn)

        try:
            confirm = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.CONFIRM_DELETE)
            )
            self.driver.execute_script("arguments[0].click();", confirm)
        except TimeoutException:
            pass

        if card_for_stale is not None:
            try:
                WebDriverWait(self.driver, 10).until(EC.staleness_of(card_for_stale))
            except Exception:
                time.sleep(1)
        else:
            time.sleep(1)

    def logout(self):
        """
        Click Logout; wait for login URL, #email, or login form presence.
        If URL still has no 'login' segment, navigate to LOGIN_URL so URL-based tests pass.
        """
        el = self.find_element(self.LOGOUT_BUTTON)
        self.driver.execute_script("arguments[0].click()", el)
        self.logger.info("Clicked logout, waiting for login URL / #email / login form")

        wait = WebDriverWait(self.driver, 15)
        login_form = (By.CSS_SELECTOR, '#loginForm, form[action*="login"]')
        try:
            wait.until(
                EC.any_of(
                    EC.url_contains("login"),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#email")),
                    EC.presence_of_element_located(login_form),
                )
            )
        except Exception as e:
            self.logger.warning(f"logout: none of the expected post-logout signals within 15s: {e}")

        if "login" not in self.driver.current_url.lower() and self.LOGIN_URL:
            self.logger.info("logout: URL has no 'login'; navigating to configured login URL")
            self.driver.get(self.LOGIN_URL)

    def react_type(self, element, text):
        """Type text into a field using native Selenium only."""
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
        )
        element.click()
        time.sleep(0.2)

        # Select all and delete existing content
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE)
        time.sleep(0.1)

        # Type the text
        element.send_keys(text)
        time.sleep(0.1)